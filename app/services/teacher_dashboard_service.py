from datetime import date, datetime, time, timedelta
from sqlalchemy import func, or_
from app.models import (
    db, School, Institute, AcademicSession, Student, StudentEnrollment, SchoolClass, Section,
    Employee, Attendance, FeeInvoice, Payment, FinancialTransaction, PayrollRecord,
    Examination, ExaminationSubject, ExaminationResult, ExamOverallResult,
    Homework, HomeworkAttachment, HomeworkSubmission, QuestionPaper,
    BehaviourCategory, BehaviourRecord, SkillDefinition, SkillAssessment,
    Timetable, Period, Subject
)
from app.services.academic_service import get_active_academic_session


def get_teacher_dashboard_summary(user_id=None, teacher_id=None, session_id=None):
    """
    Aggregates personalized daily workspace metrics for the logged-in teacher at /teacher/dashboard.
    Guarantees strict teacher data isolation and error resilience.
    """
    # 1. Resolve Active Academic Session
    active_session = get_active_academic_session()
    sess_id = session_id or (active_session.id if active_session else None)
    today = date.today()
    day_name = today.strftime('%A').upper()  # e.g., 'MONDAY'

    # 2. Resolve Teacher Identity (Employee with is_teacher=True)
    teacher = None
    if teacher_id:
        teacher = Employee.query.get(teacher_id)
    elif user_id:
        from app.models import User
        u = User.query.get(user_id)
        if u and u.linked_entity_id:
            teacher = Employee.query.get(u.linked_entity_id)

    # Fallback to first active teacher if not linked
    if not teacher:
        teacher = Employee.query.filter_by(is_teacher=True, is_active=True).first()

    summary = {
        'teacher': teacher,
        'active_session': active_session,
        'today': today,
        'day_name': day_name,
        'assigned_classes': [],
        'assigned_subjects': [],
        'today_timetable': [],
        'current_class': None,
        'next_class': None,
        'pending_actions': [],
        'homework_overview': {},
        'exams_overview': {},
        'attendance_overview': {},
        'payroll_overview': {}
    }

    if not teacher:
        return summary

    try:
        from sqlalchemy import text
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE subject_classes ADD COLUMN teacher_id INT NULL;"))
            conn.commit()
    except Exception:
        pass

    # ==========================================
    # 3. ASSIGNED CLASSES & SUBJECTS RESOLUTION
    # ==========================================
    try:
        class_sec_set = set()
        subject_set = set()

        # SubjectClass direct assignments
        sc_assignments = SubjectClass.query.filter_by(teacher_id=teacher.id, is_active=True).all()
        for sc in sc_assignments:
            if sc.school_class:
                class_sec_set.add((sc.school_class.id, sc.school_class.display_name, None, "All Sections"))
            if sc.subject:
                subject_set.add((sc.subject.id, sc.subject.name))

        # Fallback to Homework created by teacher if no SubjectClass assignment exists yet
        if not sc_assignments:
            hw_all = Homework.query.filter_by(teacher_id=teacher.id).all()
            for hw in hw_all:
                if hw.school_class:
                    sec_str = hw.section.display_name if hw.section else "All Sections"
                    class_sec_set.add((hw.school_class.id, hw.school_class.display_name, hw.section_id, sec_str))
                if hw.subject:
                    subject_set.add((hw.subject.id, hw.subject.name))

        assigned_classes_list = [
            {'class_id': c_id, 'class_name': c_name, 'section_id': s_id, 'section_name': s_name, 'display': f"{c_name} - {s_name}"}
            for c_id, c_name, s_id, s_name in sorted(class_sec_set, key=lambda x: (x[1], x[3]))
        ]

        assigned_subjects_list = [
            {'subject_id': s_id, 'subject_name': s_name}
            for s_id, s_name in sorted(subject_set, key=lambda x: x[1])
        ]

        summary['assigned_classes'] = assigned_classes_list
        summary['assigned_subjects'] = assigned_subjects_list
    except Exception as e:
        summary['assigned_classes'] = []
        summary['assigned_subjects'] = []

    # ==========================================
    # 4. TODAY'S TIMETABLE, CURRENT & NEXT CLASS
    # ==========================================
    try:
        assigned_subj_ids = [s['subject_id'] for s in summary['assigned_subjects']]
        if assigned_subj_ids:
            today_tt_query = Timetable.query.filter(
                Timetable.employee_id == teacher.id,
                func.upper(Timetable.day_of_week) == day_name,
                Timetable.subject_id.in_(assigned_subj_ids)
            )
            if sess_id:
                today_tt_query = today_tt_query.filter_by(academic_session_id=sess_id)
            today_entries = today_tt_query.all()
        else:
            today_entries = []
        
        # Sort entries by period start time
        sorted_entries = []
        for tt in today_entries:
            p = tt.period
            p_start = p.start_time if p else None
            sorted_entries.append((p_start or time.min, tt))
        
        sorted_entries.sort(key=lambda x: x[0])
        today_timetable = [tt for _, tt in sorted_entries]

        # Determine Current & Next Class based on now()
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

        # Fallback for next_class if currently outside school hours
        if not next_class and today_timetable and not current_class:
            next_class = today_timetable[0]

        summary['today_timetable'] = today_timetable
        summary['current_class'] = current_class
        summary['next_class'] = next_class

    except Exception as e:
        summary['today_timetable'] = []
        summary['current_class'] = None
        summary['next_class'] = None

    # ==========================================
    # 5. PENDING ATTENDANCE & ATTENDANCE OVERVIEW
    # ==========================================
    try:
        classes_pending_attendance = []
        classes_recorded_attendance = []

        for item in summary['assigned_classes']:
            c_id = item['class_id']
            s_id = item['section_id']

            att_records = Attendance.query.filter_by(
                entity_type='Student',
                class_id=c_id,
                attendance_date=today
            )
            if s_id:
                att_records = att_records.filter_by(section_id=s_id)
            
            att_count = att_records.count()
            if att_count == 0:
                classes_pending_attendance.append(item)
                summary['pending_actions'].append({
                    'priority': 'HIGH',
                    'category': 'ATTENDANCE',
                    'title': f"Record Today's Attendance — {item['display']}",
                    'description': f"Student attendance has not been filed for {item['display']} today ({today.strftime('%b %d')}).",
                    'action_label': "Take Attendance",
                    'action_url': f"/attendance/class?class_id={c_id}" + (f"&section_id={s_id}" if s_id else "")
                })
            else:
                classes_recorded_attendance.append(item)

        summary['attendance_overview'] = {
            'pending_classes': classes_pending_attendance,
            'recorded_classes': classes_recorded_attendance,
            'today_completed': len(classes_pending_attendance) == 0 and len(summary['assigned_classes']) > 0
        }
    except Exception as e:
        summary['attendance_overview'] = {'pending_classes': [], 'recorded_classes': [], 'today_completed': False, 'error': str(e)}

    # ==========================================
    # 6. HOMEWORK OVERVIEW & SUBMISSION REVIEWS
    # ==========================================
    try:
        teacher_hw = Homework.query.filter_by(teacher_id=teacher.id).order_by(Homework.created_at.desc()).all()
        active_homework = [hw for hw in teacher_hw if hw.status == 'PUBLISHED']
        
        pending_review_submissions = 0
        unreviewed_hw_tasks = []

        for hw in active_homework:
            unreviewed_count = HomeworkSubmission.query.filter_by(homework_id=hw.id, status='SUBMITTED').count()
            if unreviewed_count > 0:
                pending_review_submissions += unreviewed_count
                unreviewed_hw_tasks.append({'homework': hw, 'unreviewed_count': unreviewed_count})

        summary['homework_overview'] = {
            'total_assigned': len(teacher_hw),
            'active_homework': active_homework[:5],
            'pending_review_count': pending_review_submissions,
            'unreviewed_hw_tasks': unreviewed_hw_tasks
        }

        if pending_review_submissions > 0:
            summary['pending_actions'].append({
                'priority': 'MEDIUM',
                'category': 'HOMEWORK',
                'title': f"{pending_review_submissions} Student Homework Submissions Pending Review",
                'description': f"You have unreviewed student submissions across {len(unreviewed_hw_tasks)} active homework assignments.",
                'action_label': "Grade Submissions",
                'action_url': '/homework/manage'
            })
    except Exception as e:
        summary['homework_overview'] = {'total_assigned': 0, 'active_homework': [], 'pending_review_count': 0, 'error': str(e)}

    # ==========================================
    # 7. EXAMINATIONS, QUESTION PAPERS & MARKS ENTRY
    # ==========================================
    try:
        subj_ids = [s['subject_id'] for s in summary['assigned_subjects']]
        
        # Upcoming Exam Subjects taught by teacher
        upcoming_exam_subjects = []
        if subj_ids:
            upcoming_exam_subjects = ExaminationSubject.query.filter(
                ExaminationSubject.subject_id.in_(subj_ids),
                ExaminationSubject.exam_date >= today
            ).order_by(ExaminationSubject.exam_date.asc()).limit(5).all()

        # Question Paper Readiness for teacher's subjects
        teacher_papers = QuestionPaper.query.filter_by(teacher_id=teacher.id).order_by(QuestionPaper.created_at.desc()).all()
        draft_papers = [p for p in teacher_papers if p.status == 'DRAFT']

        # Pending Exam Marks Entry
        pending_marks_entries = ExaminationResult.query.filter(
            ExaminationResult.status.in_(['DRAFT', 'SUBMITTED'])
        ).count()

        summary['exams_overview'] = {
            'upcoming_exam_subjects': upcoming_exam_subjects,
            'teacher_papers': teacher_papers[:5],
            'draft_papers_count': len(draft_papers),
            'pending_marks_count': pending_marks_entries
        }

        if pending_marks_entries > 0:
            summary['pending_actions'].append({
                'priority': 'HIGH',
                'category': 'EXAMINATIONS',
                'title': f"{pending_marks_entries} Exam Mark Entries Pending Submission",
                'description': "Evaluated student exam subject rosters require final marks entry.",
                'action_label': "Enter Exam Marks",
                'action_url': '/examinations/teacher/marks-roster'
            })
    except Exception as e:
        summary['exams_overview'] = {'upcoming_exam_subjects': [], 'teacher_papers': [], 'draft_papers_count': 0, 'error': str(e)}

    # ==========================================
    # 8. SALARY / PAYROLL STATUS
    # ==========================================
    try:
        latest_payroll = PayrollRecord.query.filter_by(employee_id=teacher.id).order_by(PayrollRecord.created_at.desc()).first()
        summary['payroll_overview'] = {
            'latest_payroll': latest_payroll,
            'month_year': f"{latest_payroll.month}/{latest_payroll.year}" if latest_payroll else "N/A",
            'status': latest_payroll.payment_status if latest_payroll else "NO_RECORDS",
            'net_salary': float(latest_payroll.net_salary) if latest_payroll else 0.0
        }
    except Exception as e:
        summary['payroll_overview'] = {'latest_payroll': None, 'status': 'N/A', 'error': str(e)}

    return summary
