from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
from app.utils.decorators import login_required, role_required
from app.services.academic_service import get_active_academic_session
from app.services.class_service import get_classes_for_session
from app.services.employee_service import get_all_employees
from app.models import Student, Guardian, GuardianStudent, Employee, SchoolClass, Section, Attendance
from app.services.attendance_service import (
    save_bulk_class_student_attendance, save_bulk_employee_attendance,
    get_class_daily_attendance, get_student_attendance_summary,
    get_employee_attendance_summary, get_class_attendance_matrix,
    verify_teacher_class_access, get_today_attendance_overview,
    VALID_ATTENDANCE_STATUSES
)

attendance_bp = Blueprint('attendance', __name__, url_prefix='/attendance')


def resolve_current_student_id():
    """Helper to resolve current logged in student's ID from session/user."""
    user_id = session.get('user_id')
    linked_id = session.get('linked_entity_id')
    if linked_id:
        return linked_id
    if user_id:
        from app.models import User
        u = User.query.get(user_id)
        if u and u.linked_entity_id:
            return u.linked_entity_id
        if u:
            s = Student.query.filter((Student.registration_number == u.username) | (Student.email_address == u.username)).first()
            if s:
                return s.id
    stu = Student.query.first()
    return stu.id if stu else 1


def resolve_current_guardian_id():
    """Helper to resolve current logged in parent/guardian's ID from session/user."""
    user_id = session.get('user_id')
    linked_id = session.get('linked_entity_id')
    if linked_id:
        return linked_id
    if user_id:
        from app.models import User
        u = User.query.get(user_id)
        if u and u.linked_entity_id:
            return u.linked_entity_id
        if u:
            g = Guardian.query.filter((Guardian.registration_number == u.username) | (Guardian.email_address == u.username)).first()
            if g:
                return g.id
    gdn = Guardian.query.first()
    return gdn.id if gdn else 1


def resolve_current_employee_id():
    """Helper to resolve current logged in teacher/employee's ID."""
    user_id = session.get('user_id')
    linked_id = session.get('linked_entity_id') or session.get('employee_id')
    if linked_id:
        return linked_id
    if user_id:
        from app.models import User
        u = User.query.get(user_id)
        if u and u.linked_entity_id:
            return u.linked_entity_id
        if u:
            emp = Employee.query.filter((Employee.registration_number == u.username) | (Employee.email_address == u.username)).first()
            if emp:
                return emp.id
    emp = Employee.query.first()
    return emp.id if emp else 1


# ==========================================
# 1. CLASS STUDENT ATTENDANCE (MARKING & MATRIX)
# ==========================================

@attendance_bp.route('/class', methods=['GET', 'POST'])
@login_required
def class_attendance():
    """Record / Update daily student attendance for a class & section."""
    user_role = session.get('user_role')
    if user_role not in ('Admin', 'admin', 'Teacher', 'teacher', 'Employee', 'employee'):
        flash("Unauthorized access to class attendance.", "danger")
        return abort(403)

    act_sess = get_active_academic_session()
    sess_id = act_sess.id if act_sess else None
    classes = get_classes_for_session(session_id=sess_id)

    default_date = date.today().strftime('%Y-%m-%d')
    att_date_str = request.args.get('attendance_date', default_date)
    class_id = request.args.get('class_id', type=int) or (classes[0].id if classes else None)
    section_id = request.args.get('section_id', type=int)

    # Server-side teacher authorization verification
    if user_role in ('Teacher', 'teacher', 'Employee', 'employee'):
        emp_id = resolve_current_employee_id()
        if class_id and not verify_teacher_class_access(emp_id, class_id, section_id):
            flash("Unauthorized to record attendance for this class.", "danger")
            return redirect(url_for('teacher.dashboard'))

    if request.method == 'POST':
        c_id = request.form.get('class_id', type=int)
        sec_id = request.form.get('section_id', type=int)
        d_str = request.form.get('attendance_date')
        stu_ids = request.form.getlist('student_ids', type=int)

        if not c_id or not d_str:
            flash("Class and Date are required.", "danger")
            return redirect(request.referrer or url_for('attendance.class_attendance'))

        student_attendance_list = []
        for sid in stu_ids:
            st = request.form.get(f'status_{sid}', 'PRESENT')
            rem = request.form.get(f'remarks_{sid}')
            student_attendance_list.append({
                'student_id': sid,
                'status': st,
                'remarks': rem
            })

        try:
            count = save_bulk_class_student_attendance(
                class_id=c_id,
                section_id=sec_id,
                attendance_date=d_str,
                student_attendance_list=student_attendance_list,
                recorded_by_id=session.get('user_id'),
                session_id=sess_id
            )
            flash(f"⚡ Successfully saved attendance records for {count} students on {d_str}!", "success")
            return redirect(url_for('attendance.class_attendance', class_id=c_id, section_id=sec_id or '', attendance_date=d_str))
        except ValueError as e:
            flash(str(e), "danger")

    selected_class = SchoolClass.query.get(class_id) if class_id else None
    sections = selected_class.sections if selected_class else []
    
    roster = get_class_daily_attendance(
        class_id=class_id,
        section_id=section_id,
        attendance_date=att_date_str,
        session_id=sess_id
    ) if class_id else []

    overview = get_today_attendance_overview(session_id=sess_id)

    return render_template(
        'attendance/class_attendance.html',
        classes=classes,
        sections=sections,
        selected_class_id=class_id,
        selected_section_id=section_id,
        attendance_date=att_date_str,
        roster=roster,
        overview=overview,
        valid_statuses=sorted(list(VALID_ATTENDANCE_STATUSES))
    )


@attendance_bp.route('/class/matrix')
@login_required
def class_matrix():
    """Class monthly attendance matrix grid & low attendance summary (<75%)."""
    user_role = session.get('user_role')
    if user_role not in ('Admin', 'admin', 'Teacher', 'teacher', 'Employee', 'employee'):
        flash("Unauthorized access.", "danger")
        return abort(403)

    act_sess = get_active_academic_session()
    sess_id = act_sess.id if act_sess else None
    classes = get_classes_for_session(session_id=sess_id)

    default_month = datetime.now().strftime('%Y-%m')
    month_year = request.args.get('month_year', default_month)
    class_id = request.args.get('class_id', type=int) or (classes[0].id if classes else None)
    section_id = request.args.get('section_id', type=int)

    matrix_data = get_class_attendance_matrix(
        class_id=class_id,
        section_id=section_id,
        month_year=month_year,
        session_id=sess_id
    ) if class_id else {'students': [], 'low_attendance_students': [], 'month_label': ''}

    selected_class = SchoolClass.query.get(class_id) if class_id else None
    sections = selected_class.sections if selected_class else []

    return render_template(
        'attendance/class_matrix.html',
        classes=classes,
        sections=sections,
        selected_class_id=class_id,
        selected_section_id=section_id,
        month_year=month_year,
        matrix_data=matrix_data
    )


# ==========================================
# 2. EMPLOYEE / STAFF DAILY ATTENDANCE
# ==========================================

@attendance_bp.route('/employees', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def employee_attendance():
    """Admin manager for daily staff / teacher employee attendance."""
    default_date = date.today().strftime('%Y-%m-%d')
    att_date_str = request.args.get('attendance_date', default_date)
    att_date = datetime.strptime(att_date_str, '%Y-%m-%d').date()

    if request.method == 'POST':
        d_str = request.form.get('attendance_date')
        emp_ids = request.form.getlist('employee_ids', type=int)

        employee_attendance_list = []
        for eid in emp_ids:
            st = request.form.get(f'status_{eid}', 'PRESENT')
            rem = request.form.get(f'remarks_{eid}')
            employee_attendance_list.append({
                'employee_id': eid,
                'status': st,
                'remarks': rem
            })

        try:
            count = save_bulk_employee_attendance(
                attendance_date=d_str,
                employee_attendance_list=employee_attendance_list,
                recorded_by_id=session.get('user_id')
            )
            flash(f"⚡ Saved attendance for {count} employees on {d_str}!", "success")
            return redirect(url_for('attendance.employee_attendance', attendance_date=d_str))
        except ValueError as e:
            flash(str(e), "danger")

    all_employees = get_all_employees(active_only=True)
    
    # Existing attendance map for the date
    records = Attendance.query.filter_by(entity_type='Employee', attendance_date=att_date).all()
    records_map = {r.employee_id: r for r in records}

    employee_roster = []
    for emp in all_employees:
        rec = records_map.get(emp.id)
        employee_roster.append({
            'employee': emp,
            'record': rec,
            'current_status': rec.status if rec else 'PRESENT',
            'remarks': rec.remarks if rec else ''
        })

    return render_template(
        'attendance/employee_attendance.html',
        roster=employee_roster,
        attendance_date=att_date_str,
        valid_statuses=sorted(list(VALID_ATTENDANCE_STATUSES))
    )


# ==========================================
# 3. STUDENT & PARENT & EMPLOYEE SELF-SERVICE VIEWS
# ==========================================

@attendance_bp.route('/my-attendance')
@login_required
def my_attendance():
    """Student self-service portal view for own attendance ledger & statistics."""
    stu_id = resolve_current_student_id()
    act_sess = get_active_academic_session()
    sess_id = act_sess.id if act_sess else None

    month_year = request.args.get('month_year', datetime.now().strftime('%Y-%m'))
    data = get_student_attendance_summary(stu_id, session_id=sess_id, month_year=month_year)

    return render_template('attendance/student_attendance.html', data=data, month_year=month_year)


@attendance_bp.route('/child/<int:student_id>')
@login_required
def child_attendance(student_id):
    """Parent portal view for linked child's attendance with IDOR protection."""
    user_role = str(session.get('user_role', '')).lower()

    if user_role in ('parent', 'guardian'):
        gdn_id = resolve_current_guardian_id()
        link = GuardianStudent.query.filter_by(guardian_id=gdn_id, student_id=student_id).first()
        if not link:
            flash("Unauthorized access to student attendance ledger.", "danger")
            return redirect(url_for('parent.dashboard'))
    elif user_role not in ('admin'):
        flash("Unauthorized access.", "danger")
        return redirect(url_for('student.dashboard'))

    act_sess = get_active_academic_session()
    sess_id = act_sess.id if act_sess else None

    month_year = request.args.get('month_year', datetime.now().strftime('%Y-%m'))
    data = get_student_attendance_summary(student_id, session_id=sess_id, month_year=month_year)

    return render_template('attendance/child_attendance.html', data=data, month_year=month_year)


from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort, Response
from app.utils.decorators import login_required, role_required
from app.services.academic_service import get_active_academic_session
from app.services.class_service import get_classes_for_session
from app.services.employee_service import get_all_employees
from app.models import Student, Guardian, GuardianStudent, Employee, SchoolClass, Section, Attendance
from app.services.attendance_service import (
    save_bulk_class_student_attendance, save_bulk_employee_attendance,
    get_class_daily_attendance, get_student_attendance_summary,
    get_employee_attendance_summary, get_class_attendance_matrix,
    verify_teacher_class_access, get_today_attendance_overview,
    get_month_calendar_attendance, generate_attendance_csv_export,
    VALID_ATTENDANCE_STATUSES
)
import calendar
from datetime import datetime, date, timedelta


@attendance_bp.route('/calendar')
@login_required
def calendar_view():
    """Visual month grid calendar view of attendance."""
    user_role = str(session.get('user_role', '')).lower()
    entity_type = request.args.get('entity_type', 'Student')
    month_year = request.args.get('month_year', datetime.now().strftime('%Y-%m'))
    
    student_id = request.args.get('student_id', type=int)
    employee_id = request.args.get('employee_id', type=int)

    # Auto-resolve target entity if not specified
    if user_role in ('student'):
        entity_type = 'Student'
        student_id = resolve_current_student_id()
    elif user_role in ('parent', 'guardian') and not student_id:
        entity_type = 'Student'
        student_id = resolve_current_student_id()
    elif user_role in ('teacher', 'employee') and entity_type == 'Employee' and not employee_id:
        employee_id = resolve_current_employee_id()
    elif not student_id and not employee_id:
        if entity_type == 'Student':
            student_id = resolve_current_student_id()
        else:
            employee_id = resolve_current_employee_id()

    entity_id = student_id if entity_type == 'Student' else employee_id
    
    act_sess = get_active_academic_session()
    sess_id = act_sess.id if act_sess else None

    cal_data = get_month_calendar_attendance(
        entity_type=entity_type,
        entity_id=entity_id,
        month_year=month_year,
        session_id=sess_id
    )

    target_student = Student.query.get(student_id) if entity_type == 'Student' and student_id else None
    target_employee = Employee.query.get(employee_id) if entity_type == 'Employee' and employee_id else None

    return render_template(
        'attendance/calendar_view.html',
        cal_data=cal_data,
        entity_type=entity_type,
        student=target_student,
        employee=target_employee,
        selected_student_id=student_id,
        selected_employee_id=employee_id,
        month_year=month_year
    )


@attendance_bp.route('/export')
@login_required
def export_report():
    """Download attendance reports in Excel (.csv) or PDF/Print format for weekly or monthly periods."""
    scope = request.args.get('scope', 'class') # 'class', 'student', 'employee'
    period_type = request.args.get('period_type', 'monthly') # 'monthly', 'weekly'
    fmt = request.args.get('format', 'excel') # 'excel', 'pdf'
    month_year = request.args.get('month_year', datetime.now().strftime('%Y-%m'))
    week_start = request.args.get('week_start')
    class_id = request.args.get('class_id', type=int)
    section_id = request.args.get('section_id', type=int)
    student_id = request.args.get('student_id', type=int)
    employee_id = request.args.get('employee_id', type=int)

    act_sess = get_active_academic_session()
    sess_id = act_sess.id if act_sess else None

    if fmt in ('excel', 'csv'):
        csv_content, filename = generate_attendance_csv_export(
            scope=scope,
            period_type=period_type,
            month_year=month_year,
            week_start=week_start,
            class_id=class_id,
            section_id=section_id,
            student_id=student_id,
            employee_id=employee_id,
            session_id=sess_id
        )
        return Response(
            csv_content,
            mimetype="text/csv",
            headers={"Content-disposition": f"attachment; filename={filename}"}
        )
    else: # PDF / Print template
        if period_type == 'weekly':
            w_start = datetime.strptime(week_start, '%Y-%m-%d').date() if week_start else date.today()
            w_end = w_start + timedelta(days=6)
            period_label = f"Week of {w_start.strftime('%b %d, %Y')} to {w_end.strftime('%b %d, %Y')}"
            start_date, end_date = w_start, w_end
        else:
            dt_obj = datetime.strptime(month_year, '%Y-%m')
            period_label = dt_obj.strftime('%B %Y')
            start_date = date(dt_obj.year, dt_obj.month, 1)
            last_day = calendar.monthrange(dt_obj.year, dt_obj.month)[1]
            end_date = date(dt_obj.year, dt_obj.month, last_day)

        target_class = SchoolClass.query.get(class_id) if class_id else None
        target_student = Student.query.get(student_id) if student_id else None
        target_employee = Employee.query.get(employee_id) if employee_id else None

        query = Attendance.query.filter(Attendance.attendance_date >= start_date)\
                             .filter(Attendance.attendance_date <= end_date)

        if scope == 'class' and class_id:
            query = query.filter_by(class_id=class_id)
            if section_id:
                query = query.filter_by(section_id=section_id)
        elif scope == 'employee':
            query = query.filter_by(entity_type='Employee')
            if employee_id:
                query = query.filter_by(employee_id=employee_id)
        elif scope == 'student' and student_id:
            query = query.filter_by(student_id=student_id)

        records = query.order_by(Attendance.attendance_date.desc()).all()

        total = len(records)
        present = sum(1 for r in records if r.status == 'PRESENT')
        absent = sum(1 for r in records if r.status == 'ABSENT')
        late = sum(1 for r in records if r.status == 'LATE')
        half_day = sum(1 for r in records if r.status == 'HALF_DAY')
        rate = round(((present + late + 0.5 * half_day) / total * 100.0), 1) if total > 0 else 100.0

        return render_template(
            'attendance/attendance_report_pdf.html',
            records=records,
            scope=scope,
            period_type=period_type,
            period_label=period_label,
            target_class=target_class,
            target_student=target_student,
            target_employee=target_employee,
            summary={
                'total': total,
                'present': present,
                'absent': absent,
                'late': late,
                'half_day': half_day,
                'rate': rate
            }
        )
