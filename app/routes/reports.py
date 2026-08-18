import csv
import io
from flask import Blueprint, render_template, request, session, flash, redirect, url_for, Response
from app.models import db, User, Student, SchoolClass, Section, Examination, Subject
from app.utils.decorators import login_required
from app.services.reports_service import (
    get_academic_report_card,
    get_class_result_summary,
    get_attendance_summary_report,
    get_fee_reports,
    get_payroll_report
)

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')


@reports_bp.route('/')
@login_required
def index():
    """Renders Central Reports Directory Hub."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user:
        return redirect(url_for('auth.login'))

    user_role = (current_user.user_type or '').lower()

    return render_template(
        'reports/index.html',
        current_user=current_user,
        user_role=user_role
    )


@reports_bp.route('/academic')
@login_required
def academic():
    """Renders Academic Reports Hub & Class Result Summaries."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user:
        return redirect(url_for('auth.login'))

    sch_id = current_user.school_id or 1
    class_id = request.args.get('class_id', type=int)
    section_id = request.args.get('section_id', type=int)
    examination_id = request.args.get('examination_id', type=int)

    classes = SchoolClass.query.all()
    examinations = Examination.query.filter_by(institute_id=sch_id).all()

    class_summary = get_class_result_summary(
        class_id=class_id,
        section_id=section_id,
        examination_id=examination_id,
        school_id=sch_id
    )

    return render_template(
        'reports/academic.html',
        current_user=current_user,
        classes=classes,
        examinations=examinations,
        class_summary=class_summary,
        selected_class_id=class_id,
        selected_examination_id=examination_id
    )


@reports_bp.route('/academic/report-card')
@login_required
def academic_report_card():
    """Renders Dedicated Printable Student Report Card Page."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user:
        return redirect(url_for('auth.login'))

    user_role = (current_user.user_type or '').lower()
    sch_id = current_user.school_id or 1

    student_id = request.args.get('student_id', type=int)
    examination_id = request.args.get('examination_id', type=int)

    # Permission check for Student / Parent
    if user_role == 'student':
        stu = Student.query.filter_by(user_id=current_user.id).first()
        student_id = stu.id if stu else student_id
    elif user_role in ('parent', 'guardian'):
        if not student_id:
            from app.models import GuardianStudent
            gdn_id = current_user.linked_entity_id
            link = GuardianStudent.query.filter_by(guardian_id=gdn_id).first() if gdn_id else None
            student_id = link.student_id if link else None

    if not student_id:
        stu = Student.query.first()
        student_id = stu.id if stu else None

    if not student_id:
        flash('No student record found to generate report card.', 'warning')
        return redirect(url_for('reports.index'))

    report_card_data = get_academic_report_card(
        student_id=student_id,
        examination_id=examination_id,
        school_id=sch_id
    )

    all_students = Student.query.all() if user_role in ('admin', 'teacher', 'employee') else []
    all_exams = Examination.query.filter_by(institute_id=sch_id).all()

    return render_template(
        'reports/report_card.html',
        current_user=current_user,
        data=report_card_data,
        all_students=all_students,
        all_exams=all_exams,
        selected_student_id=student_id,
        selected_exam_id=examination_id
    )


@reports_bp.route('/attendance')
@login_required
def attendance():
    """Renders Attendance Summary Reports Page."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user:
        return redirect(url_for('auth.login'))

    user_role = (current_user.user_type or '').lower()
    sch_id = current_user.school_id or 1
    class_id = request.args.get('class_id', type=int)
    student_id = request.args.get('student_id', type=int)

    if user_role == 'student':
        stu = Student.query.filter_by(user_id=current_user.id).first()
        student_id = stu.id if stu else student_id

    classes = SchoolClass.query.all()
    att_summary = get_attendance_summary_report(
        school_id=sch_id,
        class_id=class_id,
        student_id=student_id
    )

    return render_template(
        'reports/attendance.html',
        current_user=current_user,
        classes=classes,
        att_summary=att_summary,
        selected_class_id=class_id
    )


@reports_bp.route('/fees')
@login_required
def fees():
    """Renders Fee Collection & Dues Reports Page (Restricted from Students)."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user:
        return redirect(url_for('auth.login'))

    user_role = (current_user.user_type or '').lower()
    if user_role in ('teacher', 'employee'):
        flash('Permission denied to financial fee reports.', 'danger')
        return redirect(url_for('reports.index'))

    sch_id = current_user.school_id or 1
    class_id = request.args.get('class_id', type=int)
    classes = SchoolClass.query.all()

    fee_summary = get_fee_reports(school_id=sch_id, class_id=class_id)

    return render_template(
        'reports/fees.html',
        current_user=current_user,
        classes=classes,
        fee_summary=fee_summary,
        selected_class_id=class_id
    )


@reports_bp.route('/payroll')
@login_required
def payroll():
    """Renders Payroll & Salary Summary Page (Restricted to Admin)."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user:
        return redirect(url_for('auth.login'))

    user_role = (current_user.user_type or '').lower()
    if user_role != 'admin':
        flash('Permission denied to payroll reports.', 'danger')
        return redirect(url_for('reports.index'))

    sch_id = current_user.school_id or 1
    payroll_summary = get_payroll_report(school_id=sch_id)

    return render_template(
        'reports/payroll.html',
        current_user=current_user,
        payroll_summary=payroll_summary
    )


@reports_bp.route('/students')
@login_required
def students():
    """Renders Student Master Profiles Summary Page."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user:
        return redirect(url_for('auth.login'))

    sch_id = current_user.school_id or 1
    class_id = request.args.get('class_id', type=int)

    classes = SchoolClass.query.all()
    query = Student.query
    if sch_id:
        query = query.filter((Student.institute_id == sch_id) | (Student.institute_id.is_(None)))
    if class_id:
        query = query.filter_by(class_id=class_id)

    student_list = query.all()

    return render_template(
        'reports/students.html',
        current_user=current_user,
        classes=classes,
        students=student_list,
        selected_class_id=class_id
    )


@reports_bp.route('/performance')
@login_required
def performance():
    """Renders Academic Performance Analytics Page."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user:
        return redirect(url_for('auth.login'))

    sch_id = current_user.school_id or 1
    class_id = request.args.get('class_id', type=int)

    classes = SchoolClass.query.all()
    class_summary = get_class_result_summary(class_id=class_id, school_id=sch_id)

    return render_template(
        'reports/performance.html',
        current_user=current_user,
        classes=classes,
        class_summary=class_summary,
        selected_class_id=class_id
    )


@reports_bp.route('/export/csv')
@login_required
def export_csv():
    """Export tabular report data in CSV format."""
    report_type = request.args.get('type', 'attendance')
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    sch_id = current_user.school_id or 1 if current_user else 1

    output = io.StringIO()
    writer = csv.writer(output)

    if report_type == 'attendance':
        writer.writerow(['Admission No', 'Student Name', 'Class', 'Total Working Days', 'Present Days', 'Absent Days', 'Attendance Pct'])
        summary = get_attendance_summary_report(school_id=sch_id)
        for s in summary['students']:
            writer.writerow([s['admission_number'], s['name'], s['class_name'], s['total_working_days'], s['present_days'], s['absent_days'], f"{s['percentage']}%"])
    elif report_type == 'fees':
        writer.writerow(['Invoice No', 'Student Name', 'Total Amount', 'Paid Amount', 'Balance Due', 'Status'])
        summary = get_fee_reports(school_id=sch_id)
        for i in summary['invoices']:
            writer.writerow([i['invoice_number'], i['student_name'], i['total_amount'], i['paid_amount'], i['balance'], i['status']])
    else:
        writer.writerow(['ID', 'Name', 'Details'])

    response = Response(output.getvalue(), mimetype='text/csv')
    response.headers['Content-Disposition'] = f'attachment; filename=stratlearn_{report_type}_report.csv'
    return response
