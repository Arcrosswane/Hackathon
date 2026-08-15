import os
import uuid
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename
from app.models import db, Employee, User
from app.utils.decorators import login_required, role_required
from app.services.employee_service import (
    get_all_employees,
    get_employee_by_id,
    create_employee,
    update_employee,
    toggle_employee_status,
    DEPARTMENTS,
    EMPLOYMENT_TYPES
)

employees_bp = Blueprint('employees', __name__, url_prefix='/admin/employees')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_profile_photo(file):
    if not file or file.filename == '':
        return None
    if not allowed_file(file.filename):
        raise ValueError("Invalid photo format. Only JPG, PNG, and WEBP files are allowed.")

    filename = secure_filename(file.filename)
    unique_filename = f"emp_{uuid.uuid4().hex[:10]}_{filename}"
    
    upload_dir = os.path.join(current_app.static_folder, 'uploads', 'employees')
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, unique_filename)
    file.save(file_path)
    return f"uploads/employees/{unique_filename}"


@employees_bp.route('/', methods=['GET'])
@login_required
@role_required('admin')
def index():
    search_q = request.args.get('q', '').strip()
    department_filter = request.args.get('department', '').strip()
    teacher_filter = request.args.get('teacher', '').strip()
    status_filter = request.args.get('status', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 12

    query = Employee.query
    if search_q:
        sq = f"%{search_q}%"
        query = query.filter(
            (Employee.full_name.ilike(sq)) |
            (Employee.registration_number.ilike(sq)) |
            (Employee.email_address.ilike(sq)) |
            (Employee.mobile_phone_number.ilike(sq)) |
            (Employee.designation.ilike(sq))
        )
    if department_filter:
        query = query.filter_by(department=department_filter)
    if teacher_filter == 'yes':
        query = query.filter_by(is_teacher=True)
    elif teacher_filter == 'no':
        query = query.filter_by(is_teacher=False)
    if status_filter == 'active':
        query = query.filter_by(is_active=True)
    elif status_filter == 'inactive':
        query = query.filter_by(is_active=False)

    pagination = query.order_by(Employee.full_name.asc()).paginate(page=page, per_page=per_page, error_out=False)
    employees_list = pagination.items

    return render_template(
        'employees/index.html',
        employees_list=employees_list,
        pagination=pagination,
        departments=DEPARTMENTS,
        employment_types=EMPLOYMENT_TYPES,
        search_q=search_q,
        department_filter=department_filter,
        teacher_filter=teacher_filter,
        status_filter=status_filter
    )


@employees_bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def create():
    if request.method == 'POST':
        registration_number = request.form.get('registration_number', '').strip()
        first_name = request.form.get('first_name', '').strip()
        middle_name = request.form.get('middle_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        department = request.form.get('department', 'Academic').strip()
        designation = request.form.get('designation', 'Teacher').strip()
        employment_type = request.form.get('employment_type', 'Full-time').strip()
        is_teacher = request.form.get('is_teacher') == 'on'
        
        email_address = request.form.get('email_address', '').strip()
        mobile_phone_number = request.form.get('mobile_phone_number', '').strip()
        alternate_phone = request.form.get('alternate_phone', '').strip()
        gender = request.form.get('gender', '').strip()
        
        dob_str = request.form.get('date_of_birth', '').strip()
        joining_str = request.form.get('date_of_joining', '').strip()
        
        date_of_birth = datetime.strptime(dob_str, '%Y-%m-%d').date() if dob_str else None
        date_of_joining = datetime.strptime(joining_str, '%Y-%m-%d').date() if joining_str else None

        home_address = request.form.get('home_address', '').strip()
        city = request.form.get('city', '').strip()
        state = request.form.get('state', '').strip()
        country = request.form.get('country', 'India').strip()
        postal_code = request.form.get('postal_code', '').strip()
        educational_qualification = request.form.get('educational_qualification', '').strip()

        # Handle Profile Photo Upload
        profile_photo_path = None
        photo_file = request.files.get('profile_photo')
        if photo_file and photo_file.filename:
            try:
                profile_photo_path = save_profile_photo(photo_file)
            except ValueError as ve:
                flash(str(ve), 'danger')
                return render_template('employees/form.html', is_edit=False, departments=DEPARTMENTS, employment_types=EMPLOYMENT_TYPES)

        # Server Validation
        if not registration_number or not first_name:
            flash('Employee Code and First Name are required fields.', 'danger')
        else:
            try:
                emp = create_employee(
                    registration_number=registration_number,
                    first_name=first_name,
                    last_name=last_name,
                    middle_name=middle_name,
                    department=department,
                    designation=designation,
                    employment_type=employment_type,
                    is_teacher=is_teacher,
                    email_address=email_address,
                    mobile_phone_number=mobile_phone_number,
                    gender=gender,
                    date_of_birth=date_of_birth,
                    date_of_joining=date_of_joining,
                    home_address=home_address,
                    city=city,
                    state=state,
                    country=country,
                    postal_code=postal_code,
                    profile_photo=profile_photo_path,
                    educational_qualification=educational_qualification
                )
                flash(f'Employee "{emp.full_name}" ({emp.registration_number}) registered successfully!', 'success')
                return redirect(url_for('employees.profile', employee_id=emp.id))
            except ValueError as ve:
                flash(str(ve), 'danger')
            except Exception as e:
                flash(f'Failed to register employee: {str(e)}', 'danger')

    return render_template('employees/form.html', is_edit=False, departments=DEPARTMENTS, employment_types=EMPLOYMENT_TYPES)


@employees_bp.route('/<int:employee_id>', methods=['GET'])
@login_required
@role_required('admin')
def profile(employee_id):
    employee = get_employee_by_id(employee_id)
    if not employee:
        flash('Employee not found.', 'danger')
        return redirect(url_for('employees.index'))

    # Check if a User portal login account is linked
    linked_user = User.query.filter_by(linked_entity_id=employee.id, user_type='Employee').first()

    return render_template('employees/profile.html', employee=employee, linked_user=linked_user)


@employees_bp.route('/<int:employee_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit(employee_id):
    employee = get_employee_by_id(employee_id)
    if not employee:
        flash('Employee not found.', 'danger')
        return redirect(url_for('employees.index'))

    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        middle_name = request.form.get('middle_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        department = request.form.get('department', 'Academic').strip()
        designation = request.form.get('designation', 'Teacher').strip()
        employment_type = request.form.get('employment_type', 'Full-time').strip()
        is_teacher = request.form.get('is_teacher') == 'on'

        email_address = request.form.get('email_address', '').strip()
        mobile_phone_number = request.form.get('mobile_phone_number', '').strip()
        alternate_phone = request.form.get('alternate_phone', '').strip()
        gender = request.form.get('gender', '').strip()

        dob_str = request.form.get('date_of_birth', '').strip()
        joining_str = request.form.get('date_of_joining', '').strip()

        date_of_birth = datetime.strptime(dob_str, '%Y-%m-%d').date() if dob_str else None
        date_of_joining = datetime.strptime(joining_str, '%Y-%m-%d').date() if joining_str else None

        home_address = request.form.get('home_address', '').strip()
        city = request.form.get('city', '').strip()
        state = request.form.get('state', '').strip()
        country = request.form.get('country', 'India').strip()
        postal_code = request.form.get('postal_code', '').strip()
        educational_qualification = request.form.get('educational_qualification', '').strip()

        # Handle Photo Upload
        profile_photo_path = None
        photo_file = request.files.get('profile_photo')
        if photo_file and photo_file.filename:
            try:
                profile_photo_path = save_profile_photo(photo_file)
            except ValueError as ve:
                flash(str(ve), 'danger')
                return render_template('employees/form.html', is_edit=True, employee=employee, departments=DEPARTMENTS, employment_types=EMPLOYMENT_TYPES)

        if not first_name:
            flash('First Name is required.', 'danger')
        else:
            try:
                update_employee(
                    employee_id=employee.id,
                    first_name=first_name,
                    last_name=last_name,
                    middle_name=middle_name,
                    department=department,
                    designation=designation,
                    employment_type=employment_type,
                    is_teacher=is_teacher,
                    email_address=email_address,
                    mobile_phone_number=mobile_phone_number,
                    gender=gender,
                    date_of_birth=date_of_birth,
                    date_of_joining=date_of_joining,
                    home_address=home_address,
                    city=city,
                    state=state,
                    country=country,
                    postal_code=postal_code,
                    profile_photo=profile_photo_path,
                    educational_qualification=educational_qualification
                )
                flash(f'Employee "{employee.full_name}" profile updated successfully!', 'success')
                return redirect(url_for('employees.profile', employee_id=employee.id))
            except ValueError as ve:
                flash(str(ve), 'danger')
            except Exception as e:
                flash(f'Failed to update employee: {str(e)}', 'danger')

    return render_template('employees/form.html', is_edit=True, employee=employee, departments=DEPARTMENTS, employment_types=EMPLOYMENT_TYPES)


@employees_bp.route('/<int:employee_id>/toggle-status', methods=['POST'])
@login_required
@role_required('admin')
def toggle_status(employee_id):
    try:
        emp = toggle_employee_status(employee_id)
        status_str = "activated" if emp.is_active else "deactivated"
        flash(f'Employee "{emp.full_name}" has been {status_str}.', 'info')
    except Exception as e:
        flash(str(e), 'danger')
    return redirect(request.referrer or url_for('employees.index'))


@employees_bp.route('/<int:employee_id>/photo', methods=['POST'])
@login_required
@role_required('admin')
def upload_photo(employee_id):
    employee = get_employee_by_id(employee_id)
    if not employee:
        flash('Employee not found.', 'danger')
        return redirect(url_for('employees.index'))

    photo_file = request.files.get('profile_photo')
    if photo_file and photo_file.filename:
        try:
            path = save_profile_photo(photo_file)
            employee.profile_photo = path
            db.session.commit()
            flash('Profile photo updated successfully!', 'success')
        except Exception as e:
            flash(str(e), 'danger')
    else:
        flash('Please select a photo file to upload.', 'warning')

    return redirect(url_for('employees.profile', employee_id=employee.id))
