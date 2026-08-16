from datetime import date, datetime, time
from sqlalchemy import func, or_
from app.models import (
    db, School, Institute, AcademicSession, Guardian, GuardianStudent, Student, StudentEnrollment,
    SchoolClass, Section, Employee, Attendance, FeeInvoice, Payment,
    Examination, ExaminationSubject, ExaminationResult, Homework, HomeworkSubmission, Timetable
)
from app.services.academic_service import get_active_academic_session


def get_parent_dashboard_summary(user_id=None, child_id=None, session_id=None):
    """
    Aggregates child monitoring & school information metrics for the authenticated parent at /parent/dashboard.
    Supports multi-child switching and guarantees strict parent-child authorization server-side.
    """
    active_session = get_active_academic_session()
    sess_id = session_id or (active_session.id if active_session else None)
    today = date.today()
    day_name = today.strftime('%A').upper()

    # 1. Resolve Guardian Identity
    guardian = None
    if user_id:
        from app.models import User
        u = User.query.get(user_id)
        if u and u.linked_entity_id:
            guardian = Guardian.query.get(u.linked_entity_id)

    if not guardian:
        guardian = Guardian.query.filter_by(is_active=True).first()

    summary = {
        'guardian': guardian,
        'linked_children': [],
        'selected_child': None,
        'selected_enrollment': None,
        'active_session': active_session,
        'today': today,
        'day_name': day_name,
        'today_timetable': [],
        'current_class': None,
        'next_class': None,
        'homework_overview': {},
        'exams_overview': {},
        'attendance_overview': {},
        'fees_overview': {},
        'alerts': []
    }

    if not guardian:
        return summary

    # ==========================================
    # 2. MULTI-CHILD RESOLUTION & AUTHORIZATION
    # ==========================================
    linked_links = GuardianStudent.query.filter_by(guardian_id=guardian.id).all()
    authorized_children = []
    for link in linked_links:
        if link.student and link.student.is_active:
            en = StudentEnrollment.query.filter_by(student_id=link.student.id, is_current=True).first()
            authorized_children.append({
                'link': link,
                'student': link.student,
                'enrollment': en,
                'relationship': link.relationship_type or 'Parent'
            })

    summary['linked_children'] = authorized_children

    if not authorized_children:
        return summary

    # Validate client-supplied child_id server-side against authorized links
    selected_child_item = None
    if child_id:
        for item in authorized_children:
            if item['student'].id == child_id:
                selected_child_item = item
                break

    if not selected_child_item:
        selected_child_item = authorized_children[0]

    selected_student = selected_child_item['student']
    selected_enrollment = selected_child_item['enrollment']
    summary['selected_child'] = selected_student
    summary['selected_enrollment'] = selected_enrollment

    class_id = selected_enrollment.school_class_id if selected_enrollment else None
    section_id = selected_enrollment.section_id if selected_enrollment else None

    # ==========================================
    # 3. SELECTED CHILD'S SCHEDULE TODAY
    # ==========================================
    try:
        if class_id:
            tt_query = Timetable.query.filter(
                Timetable.school_class_id == class_id,
                func.upper(Timetable.day_of_week) == day_name
            )
            if sess_id:
                tt_query = tt_query.filter_by(academic_session_id=sess_id)
            if section_id:
                tt_query = tt_query.filter(or_(Timetable.section_id == section_id, Timetable.section_id.is_(None)))

            today_entries = tt_query.all()
            sorted_entries = []
            for tt in today_entries:
                p = tt.period
                p_start = p.start_time if p else None
                sorted_entries.append((p_start or time.min, tt))
            
            sorted_entries.sort(key=lambda x: x[0])
            today_timetable = [tt for _, tt in sorted_entries]

            now_time = datetime.now().time()
            current_class = None
            next_class = None

            for tt in today_timetable:
                p = tt.period
                if p and p.start_time and p.end_time:
                    if p.start_time <= now_time <= p.end_time:
                        current_class = tt
                    elif p.start_time > now_time and next_class is None:
                        next_class = tt

            if not next_class and today_timetable and not current_class:
                next_class = today_timetable[0]

            summary['today_timetable'] = today_timetable
            summary['current_class'] = current_class
            summary['next_class'] = next_class
    except Exception as e:
        summary['today_timetable'] = []

    # ==========================================
    # 4. HOMEWORK & COURSEWORK STATUS
    # ==========================================
    try:
        if class_id:
            hw_query = Homework.query.filter_by(
                school_class_id=class_id,
                status='PUBLISHED'
            )
            if sess_id:
                hw_query = hw_query.filter_by(academic_session_id=sess_id)

            all_hw = hw_query.order_by(Homework.due_date.asc()).all()
            pending_hw = []
            submitted_cnt = 0

            for hw in all_hw:
                sub = HomeworkSubmission.query.filter_by(homework_id=hw.id, student_id=selected_student.id).first()
                if sub and sub.status in ('SUBMITTED', 'REVIEWED'):
                    submitted_cnt += 1
                else:
                    is_overdue = hw.due_date and hw.due_date < today
                    is_due_today = hw.due_date and hw.due_date == today
                    pending_hw.append({
                        'homework': hw,
                        'is_overdue': is_overdue,
                        'is_due_today': is_due_today
                    })

                    if is_overdue or is_due_today:
                        summary['alerts'].append({
                            'type': 'HOMEWORK',
                            'severity': 'HIGH' if is_overdue else 'MEDIUM',
                            'message': f"Homework '{hw.title}' for {selected_student.first_name} is {'overdue' if is_overdue else 'due today'}!"
                        })

            summary['homework_overview'] = {
                'total_assigned': len(all_hw),
                'pending_count': len(pending_hw),
                'submitted_count': submitted_cnt,
                'pending_items': pending_hw[:5]
            }
    except Exception as e:
        summary['homework_overview'] = {'total_assigned': 0, 'pending_count': 0, 'error': str(e)}

    # ==========================================
    # 5. PERSONAL ATTENDANCE MONITORING
    # ==========================================
    try:
        att_records = Attendance.query.filter_by(
            entity_type='Student',
            entity_id=selected_student.id
        ).all()

        total_days = len(att_records)
        present_cnt = sum(1 for a in att_records if a.status == 'PRESENT')
        absent_cnt = sum(1 for a in att_records if a.status == 'ABSENT')
        late_cnt = sum(1 for a in att_records if a.status == 'LATE')
        att_pct = round((present_cnt / total_days * 100), 1) if total_days > 0 else 100.0

        summary['attendance_overview'] = {
            'total_days': total_days,
            'present_count': present_cnt,
            'absent_count': absent_cnt,
            'late_count': late_cnt,
            'attendance_pct': att_pct
        }

        if att_pct < 75.0 and total_days > 5:
            summary['alerts'].append({
                'type': 'ATTENDANCE',
                'severity': 'HIGH',
                'message': f"{selected_student.first_name}'s session attendance is currently {att_pct}% (below 75%)."
            })
    except Exception as e:
        summary['attendance_overview'] = {'total_days': 0, 'attendance_pct': 100.0, 'error': str(e)}

    # ==========================================
    # 6. RECENT ACADEMIC RESULTS
    # ==========================================
    try:
        recent_results = ExaminationResult.query.filter_by(
            student_id=selected_student.id,
            status='PUBLISHED'
        ).order_by(ExaminationResult.created_at.desc()).limit(5).all()

        summary['exams_overview'] = {
            'recent_results': recent_results
        }
    except Exception as e:
        summary['exams_overview'] = {'recent_results': [], 'error': str(e)}

    # ==========================================
    # 7. FEES & DUES OVERVIEW
    # ==========================================
    try:
        invoices = FeeInvoice.query.filter_by(student_id=selected_student.id).all()
        paid_invoices = [inv for inv in invoices if inv.status == 'PAID']
        unpaid_invoices = [inv for inv in invoices if inv.status in ('UNPAID', 'PARTIAL')]

        total_paid = sum(float(inv.paid_amount or 0) for inv in invoices)
        total_due = sum(float(inv.due_amount or 0) for inv in invoices)

        summary['fees_overview'] = {
            'total_invoices': len(invoices),
            'paid_count': len(paid_invoices),
            'unpaid_count': len(unpaid_invoices),
            'total_paid': total_paid,
            'total_due': total_due
        }

        if len(unpaid_invoices) > 0:
            summary['alerts'].append({
                'type': 'FEES',
                'severity': 'MEDIUM',
                'message': f"{len(unpaid_invoices)} fee invoice(s) outstanding for {selected_student.first_name} (Total: ₹{int(total_due)})."
            })
    except Exception as e:
        summary['fees_overview'] = {'total_invoices': 0, 'total_due': 0, 'error': str(e)}

    return summary
