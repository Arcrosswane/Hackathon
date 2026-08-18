from datetime import datetime
from sqlalchemy import func
from app.models import (
    db, SyllabusTarget, SyllabusChapter, SyllabusTopic,
    SchoolClass, Section, Subject, Employee, User, AcademicSession
)
from app.services.notification_service import create_notification


def get_active_session_id():
    active_sess = AcademicSession.query.filter_by(is_active=True).first()
    if not active_sess:
        active_sess = AcademicSession.query.order_by(AcademicSession.id.desc()).first()
    return active_sess.id if active_sess else 1


def calculate_status(target_count, actual_count, tolerance=1):
    """
    Calculates status classification (BEHIND, ON_TRACK, AHEAD) based on tolerance.
    """
    diff = actual_count - target_count
    if diff < -tolerance:
        status = 'BEHIND'
    elif -tolerance <= diff <= tolerance:
        status = 'ON_TRACK'
    else:
        status = 'AHEAD'
    return status, diff


def create_or_update_target(school_id, month, year, class_id, subject_id, teacher_id, target_topic_count, tolerance_margin=1, section_id=None, created_by_id=None, session_id=None):
    """
    Creates or updates a monthly syllabus target.
    """
    sch_id = school_id or 1
    sess_id = session_id or get_active_session_id()

    month_names = ["", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    m_name = f"{month_names[int(month)]} {year}" if (1 <= int(month) <= 12) else f"Month {month} {year}"

    target = SyllabusTarget.query.filter_by(
        school_id=sch_id,
        academic_session_id=sess_id,
        month=month,
        year=year,
        class_id=class_id,
        subject_id=subject_id,
        teacher_id=teacher_id
    ).first()

    if target:
        target.target_topic_count = int(target_topic_count)
        target.tolerance_margin = int(tolerance_margin)
        target.section_id = section_id
        target.updated_at = datetime.utcnow()
    else:
        target = SyllabusTarget(
            school_id=sch_id,
            academic_session_id=sess_id,
            month=month,
            year=year,
            month_name=m_name,
            class_id=class_id,
            section_id=section_id,
            subject_id=subject_id,
            teacher_id=teacher_id,
            target_topic_count=int(target_topic_count),
            tolerance_margin=int(tolerance_margin),
            created_by_id=created_by_id
        )
        db.session.add(target)

    db.session.commit()

    # Check notification trigger if status becomes BEHIND
    actual_count = get_actual_completed_topics(sch_id, class_id, subject_id)
    status, _ = calculate_status(target.target_topic_count, actual_count, target.tolerance_margin)
    if status == 'BEHIND':
        send_behind_notification(sch_id, target, actual_count)

    return target


def get_actual_completed_topics(school_id, class_id, subject_id):
    """
    ONE SOURCE OF TRUTH: Calculates actual completed topics count from SyllabusTopic records.
    """
    return db.session.query(func.count(SyllabusTopic.id))\
        .join(SyllabusChapter, SyllabusTopic.chapter_id == SyllabusChapter.id)\
        .filter(
            SyllabusChapter.class_id == class_id,
            SyllabusChapter.subject_id == subject_id,
            SyllabusTopic.teaching_status == 'COMPLETED'
        ).scalar() or 0


def get_total_topics_count(school_id, class_id, subject_id):
    """
    Calculates total syllabus topics for a class and subject.
    """
    return db.session.query(func.count(SyllabusTopic.id))\
        .join(SyllabusChapter, SyllabusTopic.chapter_id == SyllabusChapter.id)\
        .filter(
            SyllabusChapter.class_id == class_id,
            SyllabusChapter.subject_id == subject_id
        ).scalar() or 0


def get_school_syllabus_monitoring(school_id, month=None, year=None, class_id=None, subject_id=None, teacher_id=None, status_filter=None, search_query=None, session_id=None):
    """
    Calculates real-time Expected vs Actual syllabus progress for school monitoring dashboard.
    """
    sch_id = school_id or 1
    sess_id = session_id or get_active_session_id()

    query = SyllabusTarget.query.filter_by(school_id=sch_id, academic_session_id=sess_id)

    if month:
        query = query.filter_by(month=month)
    if year:
        query = query.filter_by(year=year)
    if class_id:
        query = query.filter_by(class_id=class_id)
    if subject_id:
        query = query.filter_by(subject_id=subject_id)
    if teacher_id:
        query = query.filter_by(teacher_id=teacher_id)

    targets = query.all()

    monitored_items = []
    behind_cnt = 0
    on_track_cnt = 0
    ahead_cnt = 0
    total_target_topics = 0
    total_actual_topics = 0

    for t in targets:
        actual_cnt = get_actual_completed_topics(sch_id, t.class_id, t.subject_id)
        tot_topics = get_total_topics_count(sch_id, t.class_id, t.subject_id)
        status, diff = calculate_status(t.target_topic_count, actual_cnt, t.tolerance_margin)

        comp_pct = round((actual_cnt / tot_topics * 100.0), 1) if tot_topics > 0 else (
            round((actual_cnt / t.target_topic_count * 100.0), 1) if t.target_topic_count > 0 else 0.0
        )

        teacher_obj = t.teacher
        teacher_name = f"{teacher_obj.first_name} {teacher_obj.last_name}" if teacher_obj else "Unknown Teacher"

        item = {
            'target': t,
            'teacher': teacher_obj,
            'teacher_name': teacher_name,
            'school_class': t.school_class,
            'section': t.section,
            'subject': t.subject,
            'month_name': t.month_name,
            'target_count': t.target_topic_count,
            'actual_count': actual_cnt,
            'total_topics': tot_topics,
            'difference': diff,
            'status': status,
            'completion_pct': comp_pct
        }

        # Filter check
        if status_filter and status_filter.upper() != status:
            continue
        if search_query:
            sq = search_query.lower()
            if (sq not in teacher_name.lower() and
                sq not in (t.subject.name or '').lower() and
                sq not in (t.school_class.name or '').lower()):
                continue

        monitored_items.append(item)

        if status == 'BEHIND':
            behind_cnt += 1
        elif status == 'ON_TRACK':
            on_track_cnt += 1
        elif status == 'AHEAD':
            ahead_cnt += 1

        total_target_topics += t.target_topic_count
        total_actual_topics += actual_cnt

    total_monitored = len(monitored_items)
    overall_progress_pct = round((total_actual_topics / total_target_topics * 100.0), 1) if total_target_topics > 0 else 0.0

    return {
        'items': monitored_items,
        'summary': {
            'total_monitored': total_monitored,
            'behind': behind_cnt,
            'on_track': on_track_cnt,
            'ahead': ahead_cnt,
            'overall_progress_pct': overall_progress_pct,
            'total_target_topics': total_target_topics,
            'total_actual_topics': total_actual_topics
        }
    }


def get_teacher_detail_monitoring(school_id, teacher_id, month=None, year=None, session_id=None):
    """
    Returns detailed teacher monitoring analysis including full chapter/topic syllabus breakdown tree.
    """
    sch_id = school_id or 1
    sess_id = session_id or get_active_session_id()

    teacher = Employee.query.get_or_404(teacher_id)
    query = SyllabusTarget.query.filter_by(school_id=sch_id, academic_session_id=sess_id, teacher_id=teacher_id)

    if month:
        query = query.filter_by(month=month)
    if year:
        query = query.filter_by(year=year)

    targets = query.all()
    teacher_targets_detail = []

    for t in targets:
        actual_cnt = get_actual_completed_topics(sch_id, t.class_id, t.subject_id)
        tot_topics = get_total_topics_count(sch_id, t.class_id, t.subject_id)
        status, diff = calculate_status(t.target_topic_count, actual_cnt, t.tolerance_margin)
        comp_pct = round((actual_cnt / tot_topics * 100.0), 1) if tot_topics > 0 else 0.0

        # Fetch syllabus chapters and topics breakdown
        chapters = SyllabusChapter.query.filter_by(class_id=t.class_id, subject_id=t.subject_id).order_by(SyllabusChapter.chapter_number.asc()).all()

        teacher_targets_detail.append({
            'target': t,
            'school_class': t.school_class,
            'subject': t.subject,
            'target_count': t.target_topic_count,
            'actual_count': actual_cnt,
            'total_topics': tot_topics,
            'difference': diff,
            'status': status,
            'completion_pct': comp_pct,
            'chapters': chapters
        })

    return {
        'teacher': teacher,
        'targets_detail': teacher_targets_detail
    }


def send_behind_notification(school_id, target, actual_count):
    """
    Deduplicated notification to school admins when a teacher falls behind schedule.
    """
    admin_users = User.query.filter_by(user_type='admin').all()
    teacher_name = f"{target.teacher.first_name} {target.teacher.last_name}" if target.teacher else "Teacher"
    subj_name = target.subject.name if target.subject else "Subject"
    class_name = target.school_class.name if target.school_class else "Class"

    for admin in admin_users:
        msg = f"{teacher_name} is behind the {target.month_name} {subj_name} syllabus target for Class {class_name} (Target: {target.target_topic_count}, Actual: {actual_count})."
        create_notification(
            user_id=admin.id,
            title="⚠️ Teacher Behind Syllabus Target",
            message=msg,
            notification_type="SYSTEM",
            link_url=f"/syllabus-monitoring/teacher/{target.teacher_id}"
        )
