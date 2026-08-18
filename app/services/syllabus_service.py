from datetime import datetime
from app.models import (
    db, SyllabusChapter, SyllabusTopic, NotebookCorrection,
    SchoolClass, Subject, Student, SubjectClass, User, AcademicSession
)

def get_active_session_id():
    """Returns active academic session ID or fallback."""
    sess = AcademicSession.query.filter_by(is_active=True).first() or AcademicSession.query.order_by(AcademicSession.id.desc()).first()
    return sess.id if sess else 1


def get_teacher_assigned_classes_subjects(current_user):
    """
    Returns list of assigned (class, subject) objects for current user.
    If Admin, returns all classes and subjects.
    """
    user_role = (current_user.user_type or '').lower() if current_user else 'guest'

    if user_role in ('admin', 'employee'):
        classes = SchoolClass.query.all()
        subjects = Subject.query.all()
        assignments = []
        for c in classes:
            for s in subjects:
                assignments.append({'class': c, 'subject': s})
        return assignments

    # If teacher, match linked Employee ID or user_id in SubjectClass
    emp_id = current_user.linked_entity_id if user_role == 'teacher' else None
    sc_query = SubjectClass.query
    if emp_id:
        sc_query = sc_query.filter_by(teacher_id=emp_id)

    subject_classes = sc_query.all()
    if not subject_classes:
        # Fallback to all classes/subjects for teacher ease
        classes = SchoolClass.query.all()
        subjects = Subject.query.all()
        assignments = []
        for c in classes:
            for s in subjects:
                assignments.append({'class': c, 'subject': s})
        return assignments

    assignments = []
    for sc in subject_classes:
        cls = SchoolClass.query.get(sc.class_id)
        subj = Subject.query.get(sc.subject_id)
        if cls and subj:
            assignments.append({'class': cls, 'subject': subj})
    return assignments


def create_chapter(school_id, class_id, subject_id, chapter_name, chapter_number=1, description=None, session_id=None):
    """Creates a new syllabus chapter."""
    sch_id = school_id or 1
    sess_id = session_id or get_active_session_id()

    # Calculate next display order
    last_ch = SyllabusChapter.query.filter_by(class_id=class_id, subject_id=subject_id).order_by(SyllabusChapter.display_order.desc()).first()
    disp_order = (last_ch.display_order + 1) if last_ch else 1

    chapter = SyllabusChapter(
        school_id=sch_id,
        academic_session_id=sess_id,
        class_id=class_id,
        subject_id=subject_id,
        chapter_name=chapter_name,
        chapter_number=chapter_number or disp_order,
        description=description,
        display_order=disp_order
    )
    db.session.add(chapter)
    db.session.commit()
    return chapter


def create_topic(school_id, chapter_id, topic_name, description=None):
    """Creates a new syllabus topic inside a chapter."""
    chapter = SyllabusChapter.query.get(chapter_id)
    if not chapter:
        raise ValueError("Chapter not found.")

    sch_id = school_id or chapter.school_id or 1

    last_t = SyllabusTopic.query.filter_by(chapter_id=chapter_id).order_by(SyllabusTopic.display_order.desc()).first()
    disp_order = (last_t.display_order + 1) if last_t else 1

    topic = SyllabusTopic(
        school_id=sch_id,
        chapter_id=chapter_id,
        topic_name=topic_name,
        description=description,
        display_order=disp_order,
        teaching_status='NOT_STARTED'
    )
    db.session.add(topic)
    db.session.commit()
    return topic


def delete_topic(school_id, topic_id):
    """Safely deletes a topic and any associated notebook corrections."""
    topic = SyllabusTopic.query.get(topic_id)
    if not topic:
        return False
    
    # Delete associated notebook corrections
    NotebookCorrection.query.filter_by(topic_id=topic_id).delete()
    db.session.delete(topic)
    db.session.commit()
    return True


def quick_add_chapter_and_topic(school_id, class_id, subject_id, unit_name, topic_title):
    """Appends a new custom chapter & topic to active curriculum."""
    # Find existing chapter by unit_name or create new
    chapter = SyllabusChapter.query.filter_by(class_id=class_id, subject_id=subject_id, chapter_name=unit_name).first()
    if not chapter:
        last_ch = SyllabusChapter.query.filter_by(class_id=class_id, subject_id=subject_id).order_by(SyllabusChapter.display_order.desc()).first()
        ch_num = (last_ch.chapter_number + 1) if (last_ch and last_ch.chapter_number) else 1
        chapter = create_chapter(school_id, class_id, subject_id, chapter_name=unit_name, chapter_number=ch_num)
    
    topic = create_topic(school_id, chapter.id, topic_name=topic_title)
    return topic


def get_syllabus_chapters(school_id, class_id, subject_id, session_id=None):
    """
    Returns chapters and topics hierarchy for class & subject.
    """
    sch_id = school_id or 1
    sess_id = session_id or get_active_session_id()

    chapters = SyllabusChapter.query.filter_by(class_id=class_id, subject_id=subject_id).order_by(SyllabusChapter.display_order.asc(), SyllabusChapter.chapter_number.asc()).all()
    return chapters


def calculate_syllabus_progress(school_id, class_id, subject_id, session_id=None):
    """
    Calculates overall syllabus progress percentage strictly as (Completed / Total) * 100.
    """
    chapters = get_syllabus_chapters(school_id, class_id, subject_id, session_id)
    all_topics = []
    for ch in chapters:
        all_topics.extend(ch.topics)

    total_topics = len(all_topics)
    completed_topics = sum(1 for t in all_topics if t.teaching_status == 'COMPLETED')
    in_progress_topics = sum(1 for t in all_topics if t.teaching_status == 'IN_PROGRESS')
    not_started_topics = sum(1 for t in all_topics if t.teaching_status == 'NOT_STARTED')

    completion_pct = round((completed_topics / total_topics * 100.0), 1) if total_topics > 0 else 0.0

    return {
        'total_topics': total_topics,
        'completed_topics': completed_topics,
        'in_progress_topics': in_progress_topics,
        'not_started_topics': not_started_topics,
        'completion_percentage': completion_pct,
        'chapters_count': len(chapters)
    }


def update_topic_teaching_status(school_id, topic_id, new_status, user_id=None):
    """
    Updates teaching_status (NOT_STARTED, IN_PROGRESS, COMPLETED) for a topic.
    """
    topic = SyllabusTopic.query.get(topic_id)
    if not topic:
        raise ValueError("Topic not found.")

    valid_statuses = ['NOT_STARTED', 'IN_PROGRESS', 'COMPLETED']
    stat = (new_status or '').upper().strip()
    if stat not in valid_statuses:
        raise ValueError(f"Invalid status '{new_status}'. Must be one of {valid_statuses}")

    topic.teaching_status = stat
    topic.updated_by_id = user_id
    if stat == 'COMPLETED':
        topic.completed_at = datetime.utcnow()
        topic.completed_by_id = user_id

    db.session.commit()
    return topic


def get_notebook_matrix(school_id, class_id, subject_id, section_id=None, chapter_id=None, session_id=None):
    """
    Fetches Student x Topic matrix for notebook correction tracking.
    """
    sch_id = school_id or 1
    sess_id = session_id or get_active_session_id()

    # Query students
    stu_query = Student.query.filter_by(is_active=True)
    if sch_id:
        stu_query = stu_query.filter((Student.institute_id == sch_id) | (Student.institute_id.is_(None)))
    if class_id:
        stu_query = stu_query.filter_by(class_id=class_id)
    students = stu_query.order_by(Student.first_name.asc()).all()

    # Query topics
    if chapter_id:
        topics = SyllabusTopic.query.filter_by(chapter_id=chapter_id).order_by(SyllabusTopic.display_order.asc()).all()
    else:
        chapters = SyllabusChapter.query.filter_by(class_id=class_id, subject_id=subject_id).order_by(SyllabusChapter.display_order.asc()).all()
        topics = []
        for ch in chapters:
            topics.extend(ch.topics)

    # Query existing corrections
    topic_ids = [t.id for t in topics]
    corrections = NotebookCorrection.query.filter(
        NotebookCorrection.class_id == class_id,
        NotebookCorrection.subject_id == subject_id,
        NotebookCorrection.topic_id.in_(topic_ids)
    ).all() if topic_ids else []

    # Map corrections by (student_id, topic_id)
    corr_map = {}
    for c in corrections:
        corr_map[(c.student_id, c.topic_id)] = c.status

    # Compute notebook statistics
    total_cells = len(students) * len(topics)
    corrected_cnt = sum(1 for status in corr_map.values() if status == 'CORRECTED')
    submitted_cnt = sum(1 for status in corr_map.values() if status == 'SUBMITTED')
    pending_cnt = total_cells - (corrected_cnt + submitted_cnt)
    correction_rate = round((corrected_cnt / total_cells * 100.0), 1) if total_cells > 0 else 0.0

    return {
        'students': students,
        'topics': topics,
        'corrections_map': corr_map,
        'stats': {
            'total_cells': total_cells,
            'corrected': corrected_cnt,
            'submitted': submitted_cnt,
            'pending': pending_cnt,
            'correction_rate': correction_rate
        }
    }


def update_notebook_status(school_id, student_id, topic_id, new_status, teacher_user_id=None, session_id=None):
    """
    Updates or creates NotebookCorrection record for student-topic cell.
    """
    stat = (new_status or '').upper().strip()
    valid_statuses = ['PENDING', 'SUBMITTED', 'CORRECTED']
    if stat not in valid_statuses:
        raise ValueError(f"Invalid status '{new_status}'. Must be one of {valid_statuses}")

    topic = SyllabusTopic.query.get(topic_id)
    if not topic:
        raise ValueError("Topic not found.")

    sch_id = school_id or 1
    sess_id = session_id or get_active_session_id()

    corr = NotebookCorrection.query.filter_by(
        student_id=student_id,
        topic_id=topic_id,
        academic_session_id=sess_id
    ).first()

    if not corr:
        corr = NotebookCorrection(
            school_id=sch_id,
            academic_session_id=sess_id,
            class_id=topic.chapter.class_id,
            subject_id=topic.chapter.subject_id,
            topic_id=topic_id,
            student_id=student_id,
            teacher_id=teacher_user_id,
            status=stat
        )
        db.session.add(corr)
    else:
        corr.status = stat
        corr.teacher_id = teacher_user_id
        corr.updated_at = datetime.utcnow()

    db.session.commit()
    return corr


def get_admin_syllabus_overview(school_id, session_id=None):
    """
    Aggregates syllabus progress across all classes and subjects for Admin overview.
    """
    sch_id = school_id or 1
    classes = SchoolClass.query.all()
    subjects = Subject.query.all()

    overview = []
    for cls in classes:
        for subj in subjects:
            prog = calculate_syllabus_progress(sch_id, cls.id, subj.id, session_id)
            if prog['total_topics'] > 0:
                overview.append({
                    'class': cls,
                    'subject': subj,
                    'progress': prog
                })

    return overview
