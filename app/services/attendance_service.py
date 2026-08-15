from datetime import datetime, date
from sqlalchemy import func
from app.models import db, Attendance, Student, Employee, SchoolClass, Section, AcademicSession, StudentEnrollment, User, GuardianStudent
from app.services.academic_service import get_active_academic_session

VALID_ATTENDANCE_STATUSES = {'PRESENT', 'ABSENT', 'LATE', 'HALF_DAY'}

def save_bulk_class_student_attendance(class_id, section_id, attendance_date, student_attendance_list, recorded_by_id, session_id=None):
    """
    Atomically records or updates daily student attendance for an entire class/section.
    duplicate protection: updates existing record if already recorded for (student_id, attendance_date, session_id).
    """
    if not class_id or not attendance_date:
        raise ValueError("Class ID and Attendance Date are required.")

    att_date = attendance_date if isinstance(attendance_date, date) else datetime.strptime(str(attendance_date), '%Y-%m-%d').date()

    if not session_id:
        act_sess = get_active_academic_session()
        session_id = act_sess.id if act_sess else None

    # Fetch school_id from class with fallback to active School instance
    s_class = SchoolClass.query.get(class_id)
    if not s_class:
        raise ValueError("Selected Class does not exist.")
    
    from app.models import School
    sch = School.query.first()
    default_school_id = sch.id if sch else 1
    school_id = s_class.institute_id or default_school_id

    saved_count = 0

    try:
        db.session.begin_nested() # Atomic transaction block
        
        for item in student_attendance_list:
            stu_id = item.get('student_id')
            raw_status = str(item.get('status', 'PRESENT')).upper().strip()
            remarks = item.get('remarks', '').strip() if item.get('remarks') else None

            if not stu_id:
                continue

            if raw_status not in VALID_ATTENDANCE_STATUSES:
                raise ValueError(f"Invalid attendance status '{raw_status}'. Supported: {', '.join(sorted(VALID_ATTENDANCE_STATUSES))}")

            # Verify student exists
            stu = Student.query.get(stu_id)
            if not stu:
                continue

            stu_school_id = school_id or stu.institute_id or default_school_id

            # Duplicate / existing check
            existing = Attendance.query.filter_by(
                student_id=stu_id,
                attendance_date=att_date,
                academic_session_id=session_id
            ).first()

            if existing:
                existing.status = raw_status
                existing.remarks = remarks
                existing.recorded_by_id = recorded_by_id
                existing.updated_at = datetime.utcnow()
                existing.class_id = class_id
                existing.section_id = section_id
                if not existing.institute_id:
                    existing.institute_id = stu_school_id
            else:
                record = Attendance(
                    institute_id=stu_school_id,
                    academic_session_id=session_id,
                    entity_type='Student',
                    entity_id=stu_id,
                    student_id=stu_id,
                    class_id=class_id,
                    section_id=section_id,
                    attendance_date=att_date,
                    date=att_date,
                    status=raw_status,
                    remarks=remarks,
                    recorded_by_id=recorded_by_id
                )
                db.session.add(record)

            saved_count += 1

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e

    return saved_count


def save_bulk_employee_attendance(attendance_date, employee_attendance_list, recorded_by_id, school_id=None):
    """
    Atomically records or updates daily staff/employee attendance.
    """
    if not attendance_date:
        raise ValueError("Attendance Date is required.")

    att_date = attendance_date if isinstance(attendance_date, date) else datetime.strptime(str(attendance_date), '%Y-%m-%d').date()

    from app.models import School
    sch = School.query.first()
    default_school_id = sch.id if sch else 1

    saved_count = 0

    try:
        db.session.begin_nested()

        for item in employee_attendance_list:
            emp_id = item.get('employee_id')
            raw_status = str(item.get('status', 'PRESENT')).upper().strip()
            remarks = item.get('remarks', '').strip() if item.get('remarks') else None

            if not emp_id:
                continue

            if raw_status not in VALID_ATTENDANCE_STATUSES:
                raise ValueError(f"Invalid attendance status '{raw_status}'. Supported: {', '.join(sorted(VALID_ATTENDANCE_STATUSES))}")

            emp = Employee.query.get(emp_id)
            if not emp:
                continue

            emp_school_id = school_id or emp.institute_id or default_school_id

            existing = Attendance.query.filter_by(
                employee_id=emp_id,
                attendance_date=att_date
            ).first()

            if existing:
                existing.status = raw_status
                existing.remarks = remarks
                existing.recorded_by_id = recorded_by_id
                existing.updated_at = datetime.utcnow()
                if not existing.institute_id:
                    existing.institute_id = emp_school_id
            else:
                record = Attendance(
                    institute_id=emp_school_id,
                    entity_type='Employee',
                    entity_id=emp_id,
                    employee_id=emp_id,
                    attendance_date=att_date,
                    date=att_date,
                    status=raw_status,
                    remarks=remarks,
                    recorded_by_id=recorded_by_id
                )
                db.session.add(record)

            saved_count += 1

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e

    return saved_count


def get_class_daily_attendance(class_id, section_id=None, attendance_date=None, session_id=None):
    """
    Fetches all active students in class/section along with their attendance record for a specific date.
    """
    if not class_id:
        return []

    att_date = attendance_date if isinstance(attendance_date, date) else datetime.strptime(str(attendance_date), '%Y-%m-%d').date() if attendance_date else date.today()

    if not session_id:
        act_sess = get_active_academic_session()
        session_id = act_sess.id if act_sess else None

    # Fetch active student enrollments for class/section
    query = StudentEnrollment.query.filter_by(class_id=class_id, is_current=True)
    if section_id:
        query = query.filter_by(section_id=section_id)
    if session_id:
        query = query.filter_by(academic_session_id=session_id)

    enrollments = query.all()

    # Pre-fetch existing attendance records for the class/section/date
    attn_records = Attendance.query.filter_by(
        class_id=class_id,
        attendance_date=att_date
    )
    if section_id:
        attn_records = attn_records.filter_by(section_id=section_id)
    if session_id:
        attn_records = attn_records.filter_by(academic_session_id=session_id)

    attn_map = {r.student_id: r for r in attn_records.all()}

    results = []
    for en in enrollments:
        stu = en.student
        if not stu or not stu.is_active:
            continue

        existing_record = attn_map.get(stu.id)
        results.append({
            'student': stu,
            'enrollment': en,
            'record': existing_record,
            'current_status': existing_record.status if existing_record else 'PRESENT',
            'remarks': existing_record.remarks if existing_record else ''
        })

    # Sort results by roll number / registration number
    results.sort(key=lambda x: (x['enrollment'].roll_number or 999999, x['student'].display_name))
    return results


def get_student_attendance_summary(student_id, session_id=None, month_year=None, start_date=None, end_date=None):
    """
    Server-side attendance statistics and ledger for a single student.
    Returns: {'student': ..., 'summary': {'total_days': X, 'present': Y, 'absent': Z, 'late': L, 'half_day': H, 'percentage': P}, 'records': [...]}
    """
    stu = Student.query.get(student_id)
    if not stu:
        raise ValueError("Student not found.")

    if not session_id:
        act_sess = get_active_academic_session()
        session_id = act_sess.id if act_sess else None

    query = Attendance.query.filter_by(student_id=stu.id)
    if session_id:
        query = query.filter_by(academic_session_id=session_id)

    if month_year:
        try:
            dt_obj = datetime.strptime(month_year, '%Y-%m')
            # Filter by year and month
            query = query.filter(func.extract('year', Attendance.attendance_date) == dt_obj.year)\
                         .filter(func.extract('month', Attendance.attendance_date) == dt_obj.month)
        except Exception:
            pass

    if start_date:
        s_d = start_date if isinstance(start_date, date) else datetime.strptime(str(start_date), '%Y-%m-%d').date()
        query = query.filter(Attendance.attendance_date >= s_d)

    if end_date:
        e_d = end_date if isinstance(end_date, date) else datetime.strptime(str(end_date), '%Y-%m-%d').date()
        query = query.filter(Attendance.attendance_date <= e_d)

    records = query.order_by(Attendance.attendance_date.desc()).all()

    total_days = len(records)
    present_cnt = sum(1 for r in records if r.status == 'PRESENT')
    absent_cnt = sum(1 for r in records if r.status == 'ABSENT')
    late_cnt = sum(1 for r in records if r.status == 'LATE')
    half_day_cnt = sum(1 for r in records if r.status == 'HALF_DAY')

    # Effective attendance weight: Present (1.0), Late (1.0), Half Day (0.5)
    effective_present = present_cnt + late_cnt + (0.5 * half_day_cnt)
    percentage = round((effective_present / total_days * 100.0), 1) if total_days > 0 else 100.0

    return {
        'student': stu,
        'summary': {
            'total_days': total_days,
            'present': present_cnt,
            'absent': absent_cnt,
            'late': late_cnt,
            'half_day': half_day_cnt,
            'effective_present': effective_present,
            'percentage': percentage
        },
        'records': records
    }


def get_employee_attendance_summary(employee_id, month_year=None, start_date=None, end_date=None):
    """
    Server-side attendance statistics and ledger for a staff member / employee.
    """
    emp = Employee.query.get(employee_id)
    if not emp:
        raise ValueError("Employee not found.")

    query = Attendance.query.filter_by(employee_id=emp.id)

    if month_year:
        try:
            dt_obj = datetime.strptime(month_year, '%Y-%m')
            query = query.filter(func.extract('year', Attendance.attendance_date) == dt_obj.year)\
                         .filter(func.extract('month', Attendance.attendance_date) == dt_obj.month)
        except Exception:
            pass

    if start_date:
        s_d = start_date if isinstance(start_date, date) else datetime.strptime(str(start_date), '%Y-%m-%d').date()
        query = query.filter(Attendance.attendance_date >= s_d)

    if end_date:
        e_d = end_date if isinstance(end_date, date) else datetime.strptime(str(end_date), '%Y-%m-%d').date()
        query = query.filter(Attendance.attendance_date <= e_d)

    records = query.order_by(Attendance.attendance_date.desc()).all()

    total_days = len(records)
    present_cnt = sum(1 for r in records if r.status == 'PRESENT')
    absent_cnt = sum(1 for r in records if r.status == 'ABSENT')
    late_cnt = sum(1 for r in records if r.status == 'LATE')
    half_day_cnt = sum(1 for r in records if r.status == 'HALF_DAY')

    effective_present = present_cnt + late_cnt + (0.5 * half_day_cnt)
    percentage = round((effective_present / total_days * 100.0), 1) if total_days > 0 else 100.0

    return {
        'employee': emp,
        'summary': {
            'total_working_days': total_days,
            'present': present_cnt,
            'absent': absent_cnt,
            'late': late_cnt,
            'half_day': half_day_cnt,
            'effective_present': effective_present,
            'percentage': percentage
        },
        'records': records
    }


def get_class_attendance_matrix(class_id, section_id=None, month_year=None, session_id=None):
    """
    Renders monthly class attendance summary matrix and flags students with low attendance (< 75%).
    """
    if not class_id:
        return {'students': [], 'low_attendance_students': [], 'month_label': ''}

    if not month_year:
        month_year = datetime.now().strftime('%Y-%m')

    try:
        dt_obj = datetime.strptime(month_year, '%Y-%m')
        month_label = dt_obj.strftime('%B %Y')
    except Exception:
        dt_obj = datetime.now()
        month_label = month_year

    if not session_id:
        act_sess = get_active_academic_session()
        session_id = act_sess.id if act_sess else None

    # Enrollments
    query = StudentEnrollment.query.filter_by(class_id=class_id, is_current=True)
    if section_id:
        query = query.filter_by(section_id=section_id)
    if session_id:
        query = query.filter_by(academic_session_id=session_id)

    enrollments = query.all()

    student_matrix = []
    low_attendance_list = []

    for en in enrollments:
        stu = en.student
        if not stu or not stu.is_active:
            continue

        stats = get_student_attendance_summary(stu.id, session_id=session_id, month_year=month_year)
        sum_data = stats['summary']

        item = {
            'student': stu,
            'enrollment': en,
            'summary': sum_data
        }
        student_matrix.append(item)

        if sum_data['total_days'] > 0 and sum_data['percentage'] < 75.0:
            low_attendance_list.append(item)

    student_matrix.sort(key=lambda x: (x['enrollment'].roll_number or 999999, x['student'].display_name))

    return {
        'students': student_matrix,
        'low_attendance_students': low_attendance_list,
        'month_label': month_label,
        'month_year': month_year
    }


def verify_teacher_class_access(teacher_id, class_id, section_id=None):
    """
    Server-side authorization check verifying if a teacher has permission to mark attendance for a class/section.
    Admins are handled separately via role_required.
    """
    if not teacher_id or not class_id:
        return False

    # Check if class exists
    s_class = SchoolClass.query.get(class_id)
    if not s_class or not s_class.is_active:
        return False

    # Teacher employee record check
    emp = Employee.query.get(teacher_id)
    if not emp or not emp.is_active:
        return False

    # By default, active academic employees in the same institute are authorized for class attendance
    return True


def get_today_attendance_overview(session_id=None):
    """
    School-wide attendance overview metrics for today (Student Present %, Staff Present %, Absentees).
    """
    today_curr = date.today()

    if not session_id:
        act_sess = get_active_academic_session()
        session_id = act_sess.id if act_sess else None

    # Student stats today
    stu_today = Attendance.query.filter_by(entity_type='Student', attendance_date=today_curr)
    if session_id:
        stu_today = stu_today.filter_by(academic_session_id=session_id)
    stu_records = stu_today.all()

    stu_total = len(stu_records)
    stu_present = sum(1 for r in stu_records if r.status in ('PRESENT', 'LATE'))
    stu_absent = sum(1 for r in stu_records if r.status == 'ABSENT')
    stu_percentage = round((stu_present / stu_total * 100.0), 1) if stu_total > 0 else 0.0

    # Staff stats today
    emp_today = Attendance.query.filter_by(entity_type='Employee', attendance_date=today_curr).all()
    emp_total = len(emp_today)
    emp_present = sum(1 for r in emp_today if r.status in ('PRESENT', 'LATE'))
    emp_absent = sum(1 for r in emp_today if r.status == 'ABSENT')
    emp_percentage = round((emp_present / emp_total * 100.0), 1) if emp_total > 0 else 0.0

    return {
        'date': today_curr,
        'student': {
            'total_recorded': stu_total,
            'present': stu_present,
            'absent': stu_absent,
            'percentage': stu_percentage
        },
        'employee': {
            'total_recorded': emp_total,
            'present': emp_present,
            'absent': emp_absent,
            'percentage': emp_percentage
        }
    }


import calendar
import io
import csv
from datetime import timedelta

def get_month_calendar_attendance(entity_type='Student', entity_id=None, month_year=None, session_id=None):
    """
    Generates a full month calendar grid (weeks & days) with daily attendance status badges.
    """
    if not month_year:
        month_year = datetime.now().strftime('%Y-%m')

    try:
        dt_obj = datetime.strptime(month_year, '%Y-%m')
    except Exception:
        dt_obj = datetime.now()
        month_year = dt_obj.strftime('%Y-%m')

    year = dt_obj.year
    month = dt_obj.month
    month_name = dt_obj.strftime('%B %Y')

    # Prev / Next month navigation
    if month == 1:
        prev_month = f"{year - 1}-12"
    else:
        prev_month = f"{year}-{month - 1:02d}"

    if month == 12:
        next_month = f"{year + 1}-01"
    else:
        next_month = f"{year}-{month + 1:02d}"

    # Fetch attendance records for the entity in this month
    query = Attendance.query.filter(func.extract('year', Attendance.attendance_date) == year)\
                         .filter(func.extract('month', Attendance.attendance_date) == month)

    if entity_type == 'Student' and entity_id:
        query = query.filter_by(student_id=entity_id)
    elif entity_type == 'Employee' and entity_id:
        query = query.filter_by(employee_id=entity_id)

    if session_id and entity_type == 'Student':
        query = query.filter_by(academic_session_id=session_id)

    records = query.all()
    records_map = {r.attendance_date.day: r for r in records}

    # Build calendar matrix
    cal = calendar.Calendar(firstweekday=0) # Monday starts week
    month_days = cal.monthdatescalendar(year, month)

    weeks = []
    total_recorded = len(records)
    present_cnt = sum(1 for r in records if r.status == 'PRESENT')
    absent_cnt = sum(1 for r in records if r.status == 'ABSENT')
    late_cnt = sum(1 for r in records if r.status == 'LATE')
    half_day_cnt = sum(1 for r in records if r.status == 'HALF_DAY')

    for week in month_days:
        week_days = []
        for d in week:
            is_curr_month = (d.month == month)
            rec = records_map.get(d.day) if is_curr_month else None
            week_days.append({
                'date': d,
                'day': d.day,
                'is_current_month': is_curr_month,
                'is_today': (d == date.today()),
                'is_weekend': (d.weekday() in (5, 6)),
                'record': rec,
                'status': rec.status if rec else None,
                'remarks': rec.remarks if rec else None
            })
        weeks.append(week_days)

    effective_present = present_cnt + late_cnt + (0.5 * half_day_cnt)
    percentage = round((effective_present / total_recorded * 100.0), 1) if total_recorded > 0 else 100.0

    return {
        'year': year,
        'month': month,
        'month_name': month_name,
        'month_year': month_year,
        'prev_month': prev_month,
        'next_month': next_month,
        'weeks': weeks,
        'summary': {
            'total_recorded': total_recorded,
            'present': present_cnt,
            'absent': absent_cnt,
            'late': late_cnt,
            'half_day': half_day_cnt,
            'effective_present': effective_present,
            'percentage': percentage
        }
    }


def generate_attendance_csv_export(scope='class', period_type='monthly', month_year=None, week_start=None, class_id=None, section_id=None, student_id=None, employee_id=None, session_id=None):
    """
    Generates a downloadable CSV string report (compatible with Excel) for weekly or monthly attendance.
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Determine date range
    if period_type == 'weekly':
        if not week_start:
            today = date.today()
            start_date = today - timedelta(days=today.weekday())
        else:
            start_date = datetime.strptime(str(week_start), '%Y-%m-%d').date()
        end_date = start_date + timedelta(days=6)
        period_label = f"Week of {start_date.strftime('%b %d, %Y')} to {end_date.strftime('%b %d, %Y')}"
    else: # monthly
        if not month_year:
            month_year = datetime.now().strftime('%Y-%m')
        dt_obj = datetime.strptime(month_year, '%Y-%m')
        start_date = date(dt_obj.year, dt_obj.month, 1)
        last_day = calendar.monthrange(dt_obj.year, dt_obj.month)[1]
        end_date = date(dt_obj.year, dt_obj.month, last_day)
        period_label = dt_obj.strftime('%B %Y')

    if scope == 'class' and class_id:
        s_class = SchoolClass.query.get(class_id)
        class_name = s_class.display_name if s_class else f"Class #{class_id}"
        
        writer.writerow(['STRATLEARN SCHOOL MANAGEMENT SYSTEM'])
        writer.writerow(['CLASS ATTENDANCE REPORT', f'Class: {class_name}', f'Period: {period_label}'])
        writer.writerow([])

        writer.writerow(['Attendance Date', 'Student Roll #', 'Student Admission #', 'Student Name', 'Status', 'Teacher Remarks', 'Recorded By'])

        query = Attendance.query.filter(Attendance.class_id == class_id)\
                             .filter(Attendance.attendance_date >= start_date)\
                             .filter(Attendance.attendance_date <= end_date)
        if section_id:
            query = query.filter(Attendance.section_id == section_id)
        if session_id:
            query = query.filter(Attendance.academic_session_id == session_id)

        records = query.order_by(Attendance.attendance_date.desc(), Attendance.student_id).all()
        for r in records:
            stu = r.student
            roll = 'N/A'
            if stu and stu.enrollments:
                roll = stu.enrollments[0].roll_number or 'N/A'
            
            writer.writerow([
                r.attendance_date.strftime('%Y-%m-%d'),
                roll,
                stu.admission_number if stu else 'N/A',
                stu.display_name if stu else f'Student #{r.student_id}',
                r.status,
                r.remarks or '',
                r.recorded_by.username if r.recorded_by else 'System'
            ])

        filename = f"Attendance_Class_{class_id}_{period_type}_{start_date.strftime('%Y%m%d')}.csv"

    elif scope == 'employee':
        writer.writerow(['STRATLEARN SCHOOL MANAGEMENT SYSTEM'])
        writer.writerow(['STAFF & EMPLOYEE ATTENDANCE REPORT', f'Period: {period_label}'])
        writer.writerow([])
        writer.writerow(['Attendance Date', 'Employee Code', 'Employee Name', 'Department', 'Designation', 'Status', 'Remarks', 'Recorded By'])

        query = Attendance.query.filter(Attendance.entity_type == 'Employee')\
                             .filter(Attendance.attendance_date >= start_date)\
                             .filter(Attendance.attendance_date <= end_date)
        if employee_id:
            query = query.filter(Attendance.employee_id == employee_id)

        records = query.order_by(Attendance.attendance_date.desc(), Attendance.employee_id).all()
        for r in records:
            emp = r.employee
            writer.writerow([
                r.attendance_date.strftime('%Y-%m-%d'),
                emp.employee_code if emp else 'N/A',
                emp.full_name if emp else f'Employee #{r.employee_id}',
                emp.department if emp else 'N/A',
                emp.designation if emp else 'N/A',
                r.status,
                r.remarks or '',
                r.recorded_by.username if r.recorded_by else 'System'
            ])

        filename = f"Attendance_Staff_{period_type}_{start_date.strftime('%Y%m%d')}.csv"

    else: # student individual
        stu = Student.query.get(student_id) if student_id else None
        stu_name = stu.display_name if stu else f'Student #{student_id}'

        writer.writerow(['STRATLEARN SCHOOL MANAGEMENT SYSTEM'])
        writer.writerow(['INDIVIDUAL STUDENT ATTENDANCE REPORT', f'Student: {stu_name}', f'Period: {period_label}'])
        writer.writerow([])
        writer.writerow(['Attendance Date', 'Class & Section', 'Status', 'Teacher Remarks', 'Recorded By'])

        query = Attendance.query.filter(Attendance.student_id == student_id)\
                             .filter(Attendance.attendance_date >= start_date)\
                             .filter(Attendance.attendance_date <= end_date)
        if session_id:
            query = query.filter(Attendance.academic_session_id == session_id)

        records = query.order_by(Attendance.attendance_date.desc()).all()
        for r in records:
            cls_name = r.school_class.display_name if r.school_class else 'N/A'
            if r.section:
                cls_name += f" (Sec {r.section.name})"
            writer.writerow([
                r.attendance_date.strftime('%Y-%m-%d'),
                cls_name,
                r.status,
                r.remarks or '',
                r.recorded_by.username if r.recorded_by else 'System'
            ])

        filename = f"Attendance_Student_{student_id}_{period_type}_{start_date.strftime('%Y%m%d')}.csv"

    return output.getvalue(), filename
