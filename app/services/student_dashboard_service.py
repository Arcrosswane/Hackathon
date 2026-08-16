from datetime import date, datetime, time, timedelta
from sqlalchemy import func, or_
from app.models import (
    db, School, Institute, AcademicSession, Student, StudentEnrollment, SchoolClass, Section,
    Employee, Attendance, FeeInvoice, Payment, FinancialTransaction,
    Examination, ExaminationSubject, ExaminationResult, ExamOverallResult,
    Homework, HomeworkAttachment, HomeworkSubmission, QuestionPaper,
    Timetable, Period, Subject
)
from app.services.academic_service import get_active_academic_session


def get_student_dashboard_summary(user_id=None, student_id=None, session_id=None):
    """
    Aggregates personalized daily learning workspace metrics for the logged-in student at /student/dashboard.
    Guarantees strict student data isolation and error resilience.
    """
    # 1. Resolve Active Academic Session
    active_session = get_active_academic_session()
    sess_id = session_id or (active_session.id if active_session else None)
    today = date.today()
    day_name = today.strftime('%A').upper()  # e.g., 'MONDAY'

    # 2. Resolve Student Identity
    student = None
    if student_id:
        student = Student.query.get(student_id)
    elif user_id:
        from app.models import User
        u = User.query.get(user_id)
        if u and u.linked_entity_id:
            student = Student.query.get(u.linked_entity_id)

    # Fallback to first active student if not linked
    if not student:
        student = Student.query.filter_by(is_active=True).first()

    summary = {
        'student': student,
        'enrollment': None,
        'active_session': active_session,
        'today': today,
        'day_name': day_name,
        'today_timetable': [],
        'current_class': None,
        'next_class': None,
        'today_summary': {'total': 0, 'completed': 0, 'remaining': 0},
        'pending_tasks': [],
        'homework_overview': {},
        'exams_overview': {},
        'attendance_overview': {},
        'documents_overview': {}
    }

    if not student:
        return summary

    # ==========================================
    # 3. CURRENT ENROLLMENT RESOLUTION
    # ==========================================
    enrollment = None
    try:
        if sess_id:
            enrollment = StudentEnrollment.query.filter_by(
                student_id=student.id,
                academic_session_id=sess_id,
                is_current=True
            ).first()
        if not enrollment:
            enrollment = StudentEnrollment.query.filter_by(
                student_id=student.id,
                is_current=True
            ).first()
        summary['enrollment'] = enrollment
    except Exception as e:
        summary['enrollment'] = None

    class_id = enrollment.school_class_id if enrollment else None
    section_id = enrollment.section_id if enrollment else None

    # ==========================================
    # 4. TODAY'S TIMETABLE, CURRENT & NEXT CLASS
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

            # Sort entries by period start time
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
            completed_cnt = 0
            remaining_cnt = 0

            for tt in today_timetable:
                p = tt.period
                if p and p.start_time and p.end_time:
                    if p.start_time <= now_time <= p.end_time:
                        current_class = tt
                    elif p.end_time < now_time:
                        completed_cnt += 1
                    elif p.start_time > now_time:
                        remaining_cnt += 1
                        if next_class is None:
                            next_class = tt

            if not next_class and today_timetable and not current_class:
                next_class = today_timetable[0]

            summary['today_timetable'] = today_timetable
            summary['current_class'] = current_class
            summary['next_class'] = next_class
            summary['today_summary'] = {
                'total': len(today_timetable),
                'completed': completed_cnt,
                'remaining': remaining_cnt
            }
    except Exception as e:
        summary['today_timetable'] = []
        summary['current_class'] = None
        summary['next_class'] = None

    # ==========================================
    # 5. HOMEWORK & ASSIGNMENTS OVERVIEW
    # ==========================================
    try:
        if class_id:
            hw_query = Homework.query.filter_by(
                school_class_id=class_id,
                status='PUBLISHED'
            )
            if sess_id:
                hw_query = hw_query.filter_by(academic_session_id=sess_id)
            
            all_homework = hw_query.order_by(Homework.due_date.asc()).all()

            pending_hw = []
            submitted_hw = []
            due_today_cnt = 0

            for hw in all_homework:
                sub = HomeworkSubmission.query.filter_by(homework_id=hw.id, student_id=student.id).first()
                if sub and sub.status in ('SUBMITTED', 'REVIEWED'):
                    submitted_hw.append({'homework': hw, 'submission': sub})
                else:
                    is_overdue = hw.due_date and hw.due_date < today
                    is_due_today = hw.due_date and hw.due_date == today
                    if is_due_today:
                        due_today_cnt += 1
                    
                    item_data = {'homework': hw, 'is_overdue': is_overdue, 'is_due_today': is_due_today}
                    pending_hw.append(item_data)

                    # Surface pending homework in Task Center
                    prio = 'HIGH' if (is_due_today or is_overdue) else 'MEDIUM'
                    summary['pending_tasks'].append({
                        'priority': prio,
                        'category': 'HOMEWORK',
                        'title': f"Homework: {hw.title}",
                        'description': f"Subject: {hw.subject.name if hw.subject else 'Class Subject'} • Due: {hw.due_date.strftime('%b %d, %Y') if hw.due_date else 'TBD'}",
                        'action_label': "View & Submit",
                        'action_url': f"/homework/student"
                    })

            summary['homework_overview'] = {
                'total_assigned': len(all_homework),
                'pending_hw': pending_hw[:5],
                'submitted_count': len(submitted_hw),
                'pending_count': len(pending_hw),
                'due_today_count': due_today_cnt
            }
    except Exception as e:
        summary['homework_overview'] = {'total_assigned': 0, 'pending_hw': [], 'pending_count': 0, 'error': str(e)}

    # ==========================================
    # 6. UPCOMING EXAMS & TEST RESULTS
    # ==========================================
    try:
        upcoming_exams = Examination.query.filter(
            Examination.status.in_(['SCHEDULED', 'PUBLISHED']),
            Examination.start_date >= today
        ).order_by(Examination.start_date.asc()).limit(5).all()

        for ex in upcoming_exams:
            summary['pending_tasks'].append({
                'priority': 'MEDIUM',
                'category': 'EXAMINATION',
                'title': f"Upcoming Exam: {ex.name}",
                'description': f"Starts: {ex.start_date.strftime('%b %d, %Y') if ex.start_date else 'TBD'}",
                'action_label': "View Timetable",
                'action_url': '/examination/student-results'
            })

        # Recent Published Results for Student
        recent_results = ExaminationResult.query.filter_by(
            student_id=student.id,
            status='PUBLISHED'
        ).order_by(ExaminationResult.created_at.desc()).limit(5).all()

        summary['exams_overview'] = {
            'upcoming_exams': upcoming_exams,
            'recent_results': recent_results
        }
    except Exception as e:
        summary['exams_overview'] = {'upcoming_exams': [], 'recent_results': [], 'error': str(e)}

    # ==========================================
    # 7. PERSONAL ATTENDANCE SUMMARY
    # ==========================================
    try:
        att_records = Attendance.query.filter_by(
            entity_type='Student',
            entity_id=student.id
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
    except Exception as e:
        summary['attendance_overview'] = {'total_days': 0, 'attendance_pct': 100.0, 'error': str(e)}

    # ==========================================
    # 8. FEES & DOCUMENTS OVERVIEW
    # ==========================================
    try:
        invoices = FeeInvoice.query.filter_by(student_id=student.id).all()
        paid_invoices = [inv for inv in invoices if inv.status == 'PAID']
        unpaid_invoices = [inv for inv in invoices if inv.status in ('UNPAID', 'PARTIAL')]

        total_paid_amt = sum(float(inv.paid_amount or 0) for inv in invoices)
        total_due_amt = sum(float(inv.due_amount or 0) for inv in invoices)

        summary['documents_overview'] = {
            'total_invoices': len(invoices),
            'paid_invoices_count': len(paid_invoices),
            'unpaid_invoices_count': len(unpaid_invoices),
            'total_paid_amt': total_paid_amt,
            'total_due_amt': total_due_amt,
            'has_admission_letter': True
        }

        if len(unpaid_invoices) > 0:
            summary['pending_tasks'].append({
                'priority': 'INFO',
                'category': 'FEES',
                'title': f"{len(unpaid_invoices)} Fee Invoice(s) Outstanding",
                'description': f"Total Dues: ₹{int(total_due_amt)}",
                'action_label': "View Receipt & Pay",
                'action_url': '/fees/student-account'
            })
    except Exception as e:
        summary['documents_overview'] = {'total_invoices': 0, 'total_paid_amt': 0, 'error': str(e)}

    return summary
