from datetime import datetime
from app.models import db, Employee

DEPARTMENTS = [
    'Academic',
    'Administration',
    'Accounts',
    'Library',
    'IT',
    'Transport',
    'Support',
    'Other'
]

EMPLOYMENT_TYPES = [
    'Full-time',
    'Part-time',
    'Contract',
    'Temporary',
    'Other'
]

def get_all_employees(active_only=False, department=None, designation=None, is_teacher=None, search_query=None):
    """
    Query employees with optional filters, search, and ordering.
    """
    query = Employee.query

    if active_only:
        query = query.filter_by(is_active=True)

    if department:
        query = query.filter_by(department=department)

    if designation:
        query = query.filter_by(designation=designation)

    if is_teacher is not None:
        query = query.filter_by(is_teacher=is_teacher)

    if search_query:
        sq = f"%{search_query.strip()}%"
        query = query.filter(
            (Employee.full_name.ilike(sq)) |
            (Employee.registration_number.ilike(sq)) |
            (Employee.email_address.ilike(sq)) |
            (Employee.mobile_phone_number.ilike(sq)) |
            (Employee.designation.ilike(sq))
        )

    return query.order_by(Employee.full_name.asc()).all()

def get_active_employees():
    """Returns active employee records."""
    return get_all_employees(active_only=True)

def get_teachers():
    """
    Returns employees who are identified as teachers.
    Future teacher modules (Timetable, Homework, Exams, Class Tests) consume this helper.
    """
    return get_all_employees(is_teacher=True)

def get_active_teachers():
    """Returns active teaching staff."""
    return get_all_employees(active_only=True, is_teacher=True)

def get_employee_by_id(employee_id):
    """Retrieve employee by primary key ID."""
    return Employee.query.get(employee_id)

def get_employee_by_code(code):
    """Retrieve employee by unique employee code / registration number."""
    return Employee.query.filter_by(registration_number=code.strip()).first()

def generate_next_employee_code():
    year = datetime.now().year
    count = Employee.query.count() + 1
    code = f"EMP-{year}-{count:04d}"
    while Employee.query.filter_by(registration_number=code).first():
        count += 1
        code = f"EMP-{year}-{count:04d}"
    return code

def create_employee(registration_number=None, first_name=None, last_name=None, middle_name=None,
                    department="Academic", designation="Teacher", employment_type="Full-time",
                    is_teacher=True, email_address=None, mobile_phone_number=None,
                    gender=None, date_of_birth=None, date_of_joining=None,
                    home_address=None, city=None, state=None, country="India", postal_code=None,
                    profile_photo=None, educational_qualification=None):
    """
    Create a new employee record.
    Auto-generates unique registration_number / employee_code if missing.
    """
    if not registration_number or not str(registration_number).strip():
        code_clean = generate_next_employee_code()
    else:
        code_clean = registration_number.strip().upper()
        existing = Employee.query.filter_by(registration_number=code_clean).first()
        if existing:
            raise ValueError(f"Employee Code / Registration Number '{code_clean}' is already registered.")

    # Determine is_teacher automatically if department is Academic or designation contains Teacher
    if department == "Academic" or "teacher" in designation.lower():
        is_teacher = True

    # Auto-resolve default Institute ID
    from app.models import Institute
    inst = Institute.query.first()
    institute_id = inst.id if inst else 1

    employee = Employee(
        institute_id=institute_id,
        registration_number=code_clean,
        first_name=first_name.strip(),
        middle_name=middle_name.strip() if middle_name else None,
        last_name=last_name.strip() if last_name else None,
        role=designation,
        department=department,
        designation=designation,
        employment_type=employment_type,
        is_teacher=is_teacher,
        is_active=True,
        email_address=email_address.strip() if email_address else None,
        mobile_phone_number=mobile_phone_number.strip() if mobile_phone_number else None,
        gender=gender,
        date_of_birth=date_of_birth,
        date_of_joining=date_of_joining,
        home_address=home_address.strip() if home_address else None,
        city=city.strip() if city else None,
        state=state.strip() if state else None,
        country=country.strip() if country else "India",
        postal_code=postal_code.strip() if postal_code else None,
        profile_photo=profile_photo,
        educational_qualification=educational_qualification
    )
    employee.sync_full_name()

    db.session.add(employee)
    db.session.commit()
    return employee

def update_employee(employee_id, first_name, last_name=None, middle_name=None,
                    department="Academic", designation="Teacher", employment_type="Full-time",
                    is_teacher=True, email_address=None, mobile_phone_number=None,
                    gender=None, date_of_birth=None, date_of_joining=None,
                    home_address=None, city=None, state=None, country="India", postal_code=None,
                    profile_photo=None, educational_qualification=None):
    """
    Update an existing employee record.
    """
    employee = Employee.query.get(employee_id)
    if not employee:
        raise ValueError("Employee record not found.")

    if department == "Academic" or "teacher" in designation.lower():
        is_teacher = True

    employee.first_name = first_name.strip()
    employee.middle_name = middle_name.strip() if middle_name else None
    employee.last_name = last_name.strip() if last_name else None
    employee.sync_full_name()

    employee.role = designation
    employee.department = department
    employee.designation = designation
    employee.employment_type = employment_type
    employee.is_teacher = is_teacher

    employee.email_address = email_address.strip() if email_address else None
    employee.mobile_phone_number = mobile_phone_number.strip() if mobile_phone_number else None
    employee.gender = gender
    employee.date_of_birth = date_of_birth
    employee.date_of_joining = date_of_joining
    employee.home_address = home_address.strip() if home_address else None
    employee.city = city.strip() if city else None
    employee.state = state.strip() if state else None
    employee.country = country.strip() if country else "India"
    employee.postal_code = postal_code.strip() if postal_code else None
    employee.educational_qualification = educational_qualification

    if profile_photo:
        employee.profile_photo = profile_photo

    db.session.commit()
    return employee

def toggle_employee_status(employee_id):
    """Toggle employee active/inactive status."""
    employee = Employee.query.get(employee_id)
    if not employee:
        raise ValueError("Employee record not found.")

    employee.is_active = not employee.is_active
    db.session.commit()
    return employee
