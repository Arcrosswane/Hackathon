from datetime import date, datetime
from app.models import db, Student, StudentEnrollment, SchoolClass, Section, AcademicSession, Institute
from app.services.academic_service import get_active_academic_session

STUDENT_STATUSES = [
    'Active',
    'Inactive',
    'Graduated',
    'Transferred',
    'Withdrawn'
]

GUARDIAN_RELATIONS = [
    'Father',
    'Mother',
    'Guardian',
    'Other'
]

def get_all_students(active_only=False, session_id=None, class_id=None, section_id=None, search_query=None):
    """
    Query students with optional filters, search, and academic placement links.
    """
    query = Student.query

    if active_only:
        query = query.filter_by(is_active=True)

    if session_id or class_id or section_id:
        query = query.join(StudentEnrollment, (Student.id == StudentEnrollment.student_id) & (StudentEnrollment.is_current == True))
        if session_id:
            query = query.filter(StudentEnrollment.academic_session_id == session_id)
        if class_id:
            query = query.filter(StudentEnrollment.class_id == class_id)
        if section_id:
            query = query.filter(StudentEnrollment.section_id == section_id)

    if search_query:
        sq = f"%{search_query.strip()}%"
        query = query.filter(
            (Student.full_name.ilike(sq)) |
            (Student.registration_number.ilike(sq)) |
            (Student.email_address.ilike(sq)) |
            (Student.mobile_phone_number.ilike(sq)) |
            (Student.guardian_name.ilike(sq))
        )

    return query.order_by(Student.full_name.asc()).all()

def get_active_students():
    """Returns active student records."""
    return get_all_students(active_only=True)

def get_student_by_id(student_id):
    """Retrieve student by primary key ID."""
    return Student.query.get(student_id)

def get_student_by_admission_number(admission_number):
    """Retrieve student by unique admission number."""
    return Student.query.filter_by(registration_number=admission_number.strip().upper()).first()

def get_current_enrollment(student_id, session_id=None):
    """
    Returns current active enrollment record for a student.
    """
    query = StudentEnrollment.query.filter_by(student_id=student_id, is_current=True)
    if session_id:
        query = query.filter_by(academic_session_id=session_id)
    return query.first()

def get_student_enrollments(student_id):
    """Returns full academic placement history for a student ordered by created_at DESC."""
    return StudentEnrollment.query.filter_by(student_id=student_id).order_by(StudentEnrollment.created_at.desc()).all()

def create_student(admission_number, first_name, last_name=None, middle_name=None,
                   academic_session_id=None, class_id=None, section_id=None, roll_number=None,
                   admission_date=None, date_of_birth=None, gender=None,
                   email_address=None, mobile_phone_number=None,
                   home_address=None, city=None, state=None, country="India", postal_code=None,
                   guardian_name=None, guardian_relation="Father", guardian_phone=None, guardian_email=None, guardian_occupation=None,
                   profile_photo=None):
    """
    Register a new student and create initial StudentEnrollment record.
    Validates:
    - Unique admission_number
    - Class & Section existence and Section -> Class relationship
    - Roll number uniqueness within section
    """
    adm_clean = admission_number.strip().upper()
    existing = Student.query.filter_by(registration_number=adm_clean).first()
    if existing:
        raise ValueError(f"Admission Number / Registration Number '{adm_clean}' is already registered.")

    # Auto-resolve default Institute ID
    inst = Institute.query.first()
    institute_id = inst.id if inst else 1

    # Validate Class and Section placement
    target_class = None
    target_section = None
    target_session = None

    if class_id:
        target_class = SchoolClass.query.get(class_id)
        if not target_class:
            raise ValueError("Selected Class does not exist.")
        
        target_session_id = academic_session_id or target_class.academic_session_id
        target_session = AcademicSession.query.get(target_session_id)

    if section_id:
        target_section = Section.query.get(section_id)
        if not target_section:
            raise ValueError("Selected Section does not exist.")
        if target_class and target_section.class_id != target_class.id:
            raise ValueError(f"Section '{target_section.display_name}' does not belong to Class '{target_class.display_name}'.")

    # Validate Roll Number uniqueness if provided
    if roll_number and target_session and target_class and target_section:
        roll_conflict = StudentEnrollment.query.filter_by(
            academic_session_id=target_session.id,
            class_id=target_class.id,
            section_id=target_section.id,
            roll_number=roll_number,
            is_current=True
        ).first()
        if roll_conflict:
            raise ValueError(f"Roll Number {roll_number} is already assigned in {target_class.display_name} - {target_section.display_name}.")

    student = Student(
        institute_id=institute_id,
        class_id=class_id,
        registration_number=adm_clean,
        first_name=first_name.strip(),
        middle_name=middle_name.strip() if middle_name else None,
        last_name=last_name.strip() if last_name else None,
        gender=gender,
        date_of_birth=date_of_birth,
        admission_date=admission_date or date.today(),
        status="Active",
        is_active=True,
        email_address=email_address.strip() if email_address else None,
        mobile_phone_number=mobile_phone_number.strip() if mobile_phone_number else None,
        home_address=home_address.strip() if home_address else None,
        city=city.strip() if city else None,
        state=state.strip() if state else None,
        country=country.strip() if country else "India",
        postal_code=postal_code.strip() if postal_code else None,
        guardian_name=guardian_name.strip() if guardian_name else None,
        guardian_relation=guardian_relation,
        guardian_phone=guardian_phone.strip() if guardian_phone else None,
        guardian_email=guardian_email.strip() if guardian_email else None,
        guardian_occupation=guardian_occupation.strip() if guardian_occupation else None,
        profile_photo=profile_photo
    )
    student.sync_full_name()
    db.session.add(student)
    db.session.commit()

    # Create initial StudentEnrollment if placement selected
    if target_class and target_session:
        enrollment = StudentEnrollment(
            student_id=student.id,
            academic_session_id=target_session.id,
            class_id=target_class.id,
            section_id=target_section.id if target_section else None,
            roll_number=roll_number,
            enrollment_date=admission_date or date.today(),
            is_current=True,
            status="Active"
        )
        db.session.add(enrollment)
        db.session.commit()

    return student

def update_student(student_id, first_name, last_name=None, middle_name=None,
                   date_of_birth=None, gender=None, email_address=None, mobile_phone_number=None,
                   home_address=None, city=None, state=None, country="India", postal_code=None,
                   guardian_name=None, guardian_relation="Father", guardian_phone=None, guardian_email=None, guardian_occupation=None,
                   profile_photo=None):
    """
    Update student profile and guardian information.
    """
    student = Student.query.get(student_id)
    if not student:
        raise ValueError("Student record not found.")

    student.first_name = first_name.strip()
    student.middle_name = middle_name.strip() if middle_name else None
    student.last_name = last_name.strip() if last_name else None
    student.sync_full_name()

    student.gender = gender
    student.date_of_birth = date_of_birth
    student.email_address = email_address.strip() if email_address else None
    student.mobile_phone_number = mobile_phone_number.strip() if mobile_phone_number else None

    student.home_address = home_address.strip() if home_address else None
    student.city = city.strip() if city else None
    student.state = state.strip() if state else None
    student.country = country.strip() if country else "India"
    student.postal_code = postal_code.strip() if postal_code else None

    student.guardian_name = guardian_name.strip() if guardian_name else None
    student.guardian_relation = guardian_relation
    student.guardian_phone = guardian_phone.strip() if guardian_phone else None
    student.guardian_email = guardian_email.strip() if guardian_email else None
    student.guardian_occupation = guardian_occupation.strip() if guardian_occupation else None

    if profile_photo:
        student.profile_photo = profile_photo

    db.session.commit()
    return student

def transfer_student(student_id, new_class_id, new_section_id=None, new_session_id=None, roll_number=None):
    """
    Transfer or re-assign a student's academic placement.
    Archives previous active enrollment (is_current=False, status='Transferred') and creates new active placement.
    Preserves complete historical record for reports & certificates!
    """
    student = Student.query.get(student_id)
    if not student:
        raise ValueError("Student record not found.")

    target_class = SchoolClass.query.get(new_class_id)
    if not target_class:
        raise ValueError("Selected target Class does not exist.")

    session_id = new_session_id or target_class.academic_session_id
    target_session = AcademicSession.query.get(session_id)

    target_section = None
    if new_section_id:
        target_section = Section.query.get(new_section_id)
        if not target_section:
            raise ValueError("Selected target Section does not exist.")
        if target_section.class_id != target_class.id:
            raise ValueError(f"Section '{target_section.display_name}' does not belong to Class '{target_class.display_name}'.")

    # Validate roll number uniqueness
    if roll_number and target_session and target_class and target_section:
        roll_conflict = StudentEnrollment.query.filter_by(
            academic_session_id=target_session.id,
            class_id=target_class.id,
            section_id=target_section.id,
            roll_number=roll_number,
            is_current=True
        ).filter(StudentEnrollment.student_id != student_id).first()
        if roll_conflict:
            raise ValueError(f"Roll Number {roll_number} is already assigned in {target_class.display_name} - {target_section.display_name}.")

    # Deactivate current enrollment records for this student
    current_enrollments = StudentEnrollment.query.filter_by(student_id=student.id, is_current=True).all()
    for en in current_enrollments:
        en.is_current = False
        en.status = "Transferred"

    # Create new active enrollment
    new_enrollment = StudentEnrollment(
        student_id=student.id,
        academic_session_id=target_session.id,
        class_id=target_class.id,
        section_id=target_section.id if target_section else None,
        roll_number=roll_number,
        enrollment_date=date.today(),
        is_current=True,
        status="Active"
    )
    db.session.add(new_enrollment)

    # Sync direct class_id reference on student
    student.class_id = target_class.id

    db.session.commit()
    return new_enrollment

def toggle_student_status(student_id):
    """Toggle student active/inactive status."""
    student = Student.query.get(student_id)
    if not student:
        raise ValueError("Student record not found.")

    student.is_active = not student.is_active
    student.status = "Active" if student.is_active else "Inactive"
    db.session.commit()
    return student
