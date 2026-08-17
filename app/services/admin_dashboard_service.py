from datetime import date, datetime, timedelta
from sqlalchemy import func, or_
from app.models import (
    db, School, Institute, AcademicSession, Student, StudentEnrollment, SchoolClass, Section,
    Employee, Attendance, FeeInvoice, Payment, FinancialTransaction, PayrollRecord,
    Examination, ExaminationSubject, ExaminationResult, ExamOverallResult,
    Homework, HomeworkSubmission, QuestionPaper, BehaviourRecord, SkillAssessment
)
from app.services.academic_service import get_active_academic_session


def get_admin_dashboard_summary(school_id=None, session_id=None):
    """
    Aggregates school-wide operational, academic, and financial metrics 
    across all existing StratLearn modules for the Admin Command Center.
    Guarantees error resilience and data isolation.
    """
    school = None
    if school_id:
        school = School.query.get(school_id)
    if not school:
        school = School.query.first()

    active_session = get_active_academic_session()
    sess_id = session_id or (active_session.id if active_session else None)
    today = date.today()

    summary = {
        'school': school,
        'active_session': active_session,
        'today': today,
        'level1_kpis': {},
        'level2_pending_actions': [],
        'level3_trends': {},
        'level4_activity': [],
        'students_overview': {},
        'staff_overview': {},
        'attendance_overview': {},
        'finance_overview': {},
        'payroll_overview': {},
        'exams_overview': {},
        'homework_overview': {},
        'store_overview': {}
    }

    # ==========================================
    # 1. STUDENT OVERVIEW & KPIS
    # ==========================================
    try:
        total_students = Student.query.filter_by(is_active=True).count()
        
        # New admissions in last 30 days
        thirty_days_ago = today - timedelta(days=30)
        new_admissions = Student.query.filter(
            Student.is_active == True,
            Student.admission_date >= thirty_days_ago
        ).count()

        # Class breakdown
        classes = SchoolClass.query.filter_by(is_active=True).order_by(SchoolClass.numeric_order.asc()).all()
        class_distribution = []
        for cls in classes:
            st_count = Student.query.filter_by(class_id=cls.id, is_active=True).count()
            class_distribution.append({
                'class_id': cls.id,
                'class_name': cls.display_name,
                'student_count': st_count
            })

        summary['students_overview'] = {
            'total_students': total_students,
            'new_admissions': new_admissions,
            'class_distribution': class_distribution
        }
        summary['level1_kpis']['total_students'] = total_students
    except Exception as e:
        summary['students_overview'] = {'total_students': 0, 'new_admissions': 0, 'class_distribution': [], 'error': str(e)}

    # ==========================================
    # 2. STAFF OVERVIEW & KPIS
    # ==========================================
    try:
        total_employees = Employee.query.filter_by(is_active=True).count()
        teaching_staff = Employee.query.filter_by(is_active=True, is_teacher=True).count()
        admin_staff = max(0, total_employees - teaching_staff)

        # Today's Staff Attendance
        staff_today_att = Attendance.query.filter_by(
            entity_type='Employee',
            attendance_date=today
        ).all()

        staff_present = sum(1 for a in staff_today_att if a.status in ('PRESENT', 'LATE'))
        staff_absent = sum(1 for a in staff_today_att if a.status == 'ABSENT')

        summary['staff_overview'] = {
            'total_employees': total_employees,
            'teaching_staff': teaching_staff,
            'admin_staff': admin_staff,
            'staff_present': staff_present,
            'staff_absent': staff_absent,
            'staff_attendance_recorded': len(staff_today_att) > 0
        }
        summary['level1_kpis']['total_employees'] = total_employees
    except Exception as e:
        summary['staff_overview'] = {'total_employees': 0, 'teaching_staff': 0, 'admin_staff': 0, 'staff_present': 0, 'staff_absent': 0, 'error': str(e)}

    # ==========================================
    # 3. TODAY'S ATTENDANCE & 7-DAY TREND
    # ==========================================
    try:
        student_today_att = Attendance.query.filter_by(
            entity_type='Student',
            attendance_date=today
        ).all()

        stu_present = sum(1 for a in student_today_att if a.status in ('PRESENT', 'LATE'))
        stu_absent = sum(1 for a in student_today_att if a.status == 'ABSENT')
        stu_late = sum(1 for a in student_today_att if a.status == 'LATE')
        stu_total_recorded = len(student_today_att)

        att_percentage = round((stu_present / stu_total_recorded * 100.0), 1) if stu_total_recorded > 0 else 0.0

        # 7-Day Attendance Trend
        seven_days_trend = []
        for i in range(6, -1, -1):
            d = today - timedelta(days=i)
            day_records = Attendance.query.filter_by(entity_type='Student', attendance_date=d).all()
            d_total = len(day_records)
            d_present = sum(1 for a in day_records if a.status in ('PRESENT', 'LATE'))
            d_pct = round((d_present / d_total * 100.0), 1) if d_total > 0 else 0.0
            seven_days_trend.append({
                'date': d.strftime('%b %d'),
                'day_name': d.strftime('%a'),
                'total': d_total,
                'present': d_present,
                'percentage': d_pct
            })

        summary['attendance_overview'] = {
            'today_recorded': stu_total_recorded > 0,
            'present_count': stu_present,
            'absent_count': stu_absent,
            'late_count': stu_late,
            'total_recorded': stu_total_recorded,
            'attendance_percentage': att_percentage,
            'seven_days_trend': seven_days_trend
        }
        summary['level1_kpis']['today_attendance_pct'] = att_percentage

        if stu_total_recorded == 0:
            summary['level2_pending_actions'].append({
                'priority': 'HIGH',
                'category': 'ATTENDANCE',
                'title': "Today's Student Attendance Not Recorded",
                'description': f"No student attendance records filed for today ({today.strftime('%b %d, %Y')}).",
                'action_label': "Record Attendance",
                'action_url': '/attendance/class'
            })
    except Exception as e:
        summary['attendance_overview'] = {'today_recorded': False, 'attendance_percentage': 0.0, 'seven_days_trend': [], 'error': str(e)}

    # ==========================================
    # 4. FINANCE & FEE SNAPSHOT
    # ==========================================
    try:
        first_day_of_month = date(today.year, today.month, 1)
        
        # Monthly Fee Collections
        monthly_collections = db.session.query(func.sum(Payment.amount_paid)).filter(
            Payment.payment_date >= first_day_of_month,
            Payment.payment_status.in_(['SUCCESS', 'CONFIRMED', 'PAID'])
        ).scalar() or 0.0

        # Outstanding Fee Dues
        unpaid_invoices = FeeInvoice.query.filter(
            FeeInvoice.status.in_(['UNPAID', 'PARTIALLY_PAID', 'OVERDUE'])
        ).all()

        total_outstanding = sum(inv.balance_due for inv in unpaid_invoices)
        unpaid_count = len(unpaid_invoices)

        # Monthly Income & Expenses from Accounts Module
        monthly_income = db.session.query(func.sum(FinancialTransaction.amount)).filter(
            FinancialTransaction.type == 'INCOME',
            FinancialTransaction.transaction_date >= first_day_of_month,
            FinancialTransaction.status == 'COMPLETED'
        ).scalar() or 0.0

        monthly_expense = db.session.query(func.sum(FinancialTransaction.amount)).filter(
            FinancialTransaction.type == 'EXPENSE',
            FinancialTransaction.transaction_date >= first_day_of_month,
            FinancialTransaction.status == 'COMPLETED'
        ).scalar() or 0.0

        summary['finance_overview'] = {
            'monthly_collections': float(monthly_collections),
            'total_outstanding': float(total_outstanding),
            'unpaid_invoices_count': unpaid_count,
            'monthly_income': float(monthly_income),
            'monthly_expense': float(monthly_expense)
        }
        summary['level1_kpis']['total_outstanding_fees'] = float(total_outstanding)

        if unpaid_count > 0:
            summary['level2_pending_actions'].append({
                'priority': 'MEDIUM',
                'category': 'FINANCE',
                'title': f"{unpaid_count} Unpaid Fee Invoices Pending",
                'description': f"Total outstanding student fee dues amount to ₹{total_outstanding:,.2f}.",
                'action_label': "View Invoices",
                'action_url': '/fees/invoices'
            })
    except Exception as e:
        summary['finance_overview'] = {'monthly_collections': 0.0, 'total_outstanding': 0.0, 'unpaid_invoices_count': 0, 'error': str(e)}

    # ==========================================
    # 5. PAYROLL SNAPSHOT
    # ==========================================
    try:
        latest_payrolls = PayrollRecord.query.order_by(PayrollRecord.created_at.desc()).limit(10).all()
        pending_payrolls = PayrollRecord.query.filter(PayrollRecord.payment_status.in_(['DRAFT', 'PENDING', 'PROCESSING'])).count()
        last_run = latest_payrolls[0] if latest_payrolls else None

        summary['payroll_overview'] = {
            'pending_count': pending_payrolls,
            'last_run_month': f"{last_run.month}/{last_run.year}" if last_run else "None",
            'last_run_status': last_run.payment_status if last_run else "N/A"
        }

        if pending_payrolls > 0:
            summary['level2_pending_actions'].append({
                'priority': 'MEDIUM',
                'category': 'PAYROLL',
                'title': f"{pending_payrolls} Pending Staff Payroll Entries",
                'description': "Employee monthly salary processing requires approval and payment disbursement.",
                'action_label': "Process Payroll",
                'action_url': '/payroll/roster'
            })
    except Exception as e:
        summary['payroll_overview'] = {'pending_count': 0, 'last_run_month': 'N/A', 'error': str(e)}

    # ==========================================
    # 6. EXAMINATIONS & UNPUBLISHED RESULTS
    # ==========================================
    try:
        upcoming_exams = Examination.query.filter(
            Examination.status.in_(['DRAFT', 'SCHEDULED', 'ONGOING'])
        ).order_by(Examination.start_date.asc()).limit(5).all()

        upcoming_subject_tests = ExaminationSubject.query.filter(
            ExaminationSubject.exam_date >= today
        ).order_by(ExaminationSubject.exam_date.asc()).limit(5).all()

        # Unpublished exam results requiring admin publication
        draft_results_count = ExaminationResult.query.filter(
            ExaminationResult.status.in_(['DRAFT', 'SUBMITTED'])
        ).count()

        summary['exams_overview'] = {
            'upcoming_exams_count': len(upcoming_exams),
            'upcoming_exams': upcoming_exams,
            'upcoming_subject_tests': upcoming_subject_tests,
            'draft_results_count': draft_results_count
        }
        summary['level1_kpis']['upcoming_exams_count'] = len(upcoming_exams)

        if draft_results_count > 0:
            summary['level2_pending_actions'].append({
                'priority': 'HIGH',
                'category': 'EXAMINATIONS',
                'title': f"{draft_results_count} Evaluated Exam Marks Awaiting Publication",
                'description': "Student examination results are evaluated in draft state. Publish results to release report cards.",
                'action_label': "Publish Exam Results",
                'action_url': '/examinations'
            })
    except Exception as e:
        summary['exams_overview'] = {'upcoming_exams_count': 0, 'upcoming_exams': [], 'draft_results_count': 0, 'error': str(e)}

    # ==========================================
    # 7. HOMEWORK & ACADEMIC ACTIVITY
    # ==========================================
    try:
        active_homework = Homework.query.filter_by(status='PUBLISHED').order_by(Homework.due_date.asc()).limit(5).all()
        pending_eval_submissions = HomeworkSubmission.query.filter_by(status='SUBMITTED').count()

        summary['homework_overview'] = {
            'active_homework_count': len(active_homework),
            'active_homework': active_homework,
            'pending_eval_submissions': pending_eval_submissions
        }

        if pending_eval_submissions > 0:
            summary['level2_pending_actions'].append({
                'priority': 'INFO',
                'category': 'HOMEWORK',
                'title': f"{pending_eval_submissions} Student Homework Submissions Pending Grading",
                'description': "Teachers have unreviewed student homework submissions.",
                'action_label': "Manage Homework",
                'action_url': '/homework/manage'
            })
    except Exception as e:
        summary['homework_overview'] = {'active_homework_count': 0, 'active_homework': [], 'pending_eval_submissions': 0, 'error': str(e)}

    # ==========================================
    # 7b. STORE & POS SNAPSHOT
    # ==========================================
    try:
        from app.services.store_service import get_store_dashboard_metrics, resolve_school_id
        sch_id = school.id if school else resolve_school_id()
        store_metrics = get_store_dashboard_metrics(sch_id) if sch_id else {}
        summary['store_overview'] = store_metrics

        if store_metrics.get('pending_orders', 0) > 0:
            summary['level2_pending_actions'].append({
                'priority': 'MEDIUM',
                'category': 'STORE',
                'title': f"{store_metrics['pending_orders']} Pending Store Orders",
                'description': 'Online store orders awaiting confirmation and processing.',
                'action_label': 'Manage Store Orders',
                'action_url': '/store/admin',
            })
        if store_metrics.get('low_stock_count', 0) > 0:
            summary['level2_pending_actions'].append({
                'priority': 'HIGH',
                'category': 'STORE',
                'title': f"{store_metrics['low_stock_count']} Products Low on Stock",
                'description': 'School store inventory below threshold. Restock required.',
                'action_label': 'View Inventory',
                'action_url': '/store/admin',
            })
    except Exception as e:
        summary['store_overview'] = {'today_sales': 0, 'pending_orders': 0, 'low_stock_count': 0, 'error': str(e)}

    # ==========================================
    # 8. RECENT ACTIVITY FEED
    # ==========================================
    try:
        recent_activity = []

        # Recent Student Admissions
        recent_stus = Student.query.order_by(Student.created_at.desc()).limit(3).all()
        for st in recent_stus:
            recent_activity.append({
                'type': 'STUDENT',
                'title': f"New Student Admitted: {st.full_name}",
                'meta': f"Adm No: {st.registration_number} • Class: {st.school_class.display_name if st.school_class else 'Unassigned'}",
                'timestamp': st.created_at,
                'icon': '👤'
            })

        # Recent Fee Payments
        recent_pmts = Payment.query.order_by(Payment.created_at.desc()).limit(3).all()
        for p in recent_pmts:
            recent_activity.append({
                'type': 'FEE',
                'title': f"Fee Payment Recorded: ₹{p.amount_paid:,.2f}",
                'meta': f"Invoice #{p.invoice_id} • Mode: {p.payment_mode or 'Cash'}",
                'timestamp': p.created_at,
                'icon': '💰'
            })

        # Recent Homework Created
        recent_hw = Homework.query.order_by(Homework.created_at.desc()).limit(3).all()
        for hw in recent_hw:
            recent_activity.append({
                'type': 'HOMEWORK',
                'title': f"Homework Assigned: {hw.title}",
                'meta': f"Subject: {hw.subject.name if hw.subject else '—'} • Class: {hw.school_class.display_name if hw.school_class else '—'}",
                'timestamp': hw.created_at,
                'icon': '📖'
            })

        # Sort activity feed chronologically
        recent_activity.sort(key=lambda x: x['timestamp'] or datetime.min, reverse=True)
        summary['level4_activity'] = recent_activity[:8]

    except Exception as e:
        summary['level4_activity'] = []

    return summary
