from datetime import datetime
from app.models import db, Guardian, GuardianStudent, Student, Institute

RELATIONSHIP_TYPES = [
    'Father',
    'Mother',
    'Guardian',
    'Grandfather',
    'Grandmother',
    'Uncle',
    'Aunt',
    'Other'
]

def get_all_guardians(active_only=False, search_query=None):
    """
    Query guardians with optional active filter and search across guardian name, code, email, phone, or child student name.
    """
    query = Guardian.query

    if active_only:
        query = query.filter_by(is_active=True)

    if search_query:
        sq = f"%{search_query.strip()}%"
        # Search guardian fields OR child student names via outer join
        query = query.outerjoin(GuardianStudent, Guardian.id == GuardianStudent.guardian_id)\
                     .outerjoin(Student, GuardianStudent.student_id == Student.id)\
                     .filter(
                         (Guardian.full_name.ilike(sq)) |
                         (Guardian.registration_number.ilike(sq)) |
                         (Guardian.email_address.ilike(sq)) |
                         (Guardian.mobile_phone_number.ilike(sq)) |
                         (Student.full_name.ilike(sq)) |
                         (Student.registration_number.ilike(sq))
                     ).distinct()

    return query.order_by(Guardian.full_name.asc()).all()

def get_active_guardians():
    """Returns active guardian records."""
    return get_all_guardians(active_only=True)

def get_guardian_by_id(guardian_id):
    """Retrieve guardian by primary key ID."""
    return Guardian.query.get(guardian_id)

def get_guardian_by_code(code):
    """Retrieve guardian by unique guardian code / registration number."""
    return Guardian.query.filter_by(registration_number=code.strip().upper()).first()

def create_guardian(guardian_code, first_name, last_name=None, middle_name=None,
                    email_address=None, mobile_phone_number=None, alternate_phone=None,
                    occupation=None, home_address=None, city=None, state=None, country="India", postal_code=None,
                    student_id=None, relationship="Father", is_primary=False, is_emergency_contact=False, can_receive_notifications=True):
    """
    Create a new parent/guardian record.
    Enforces uniqueness of guardian_code / registration_number.
    Optionally links an existing student if student_id is provided.
    """
    code_clean = guardian_code.strip().upper()
    existing = Guardian.query.filter_by(registration_number=code_clean).first()
    if existing:
        raise ValueError(f"Guardian Code / Registration Number '{code_clean}' is already registered.")

    # Auto-resolve default Institute ID
    inst = Institute.query.first()
    institute_id = inst.id if inst else 1

    guardian = Guardian(
        institute_id=institute_id,
        registration_number=code_clean,
        first_name=first_name.strip(),
        middle_name=middle_name.strip() if middle_name else None,
        last_name=last_name.strip() if last_name else None,
        email_address=email_address.strip() if email_address else None,
        mobile_phone_number=mobile_phone_number.strip() if mobile_phone_number else None,
        alternate_phone=alternate_phone.strip() if alternate_phone else None,
        occupation=occupation.strip() if occupation else None,
        home_address=home_address.strip() if home_address else None,
        city=city.strip() if city else None,
        state=state.strip() if state else None,
        country=country.strip() if country else "India",
        postal_code=postal_code.strip() if postal_code else None,
        is_active=True,
        status="Active"
    )
    guardian.sync_full_name()
    db.session.add(guardian)
    db.session.commit()

    if student_id:
        link_guardian_student(
            guardian_id=guardian.id,
            student_id=student_id,
            relationship=relationship,
            is_primary=is_primary,
            is_emergency_contact=is_emergency_contact,
            can_receive_notifications=can_receive_notifications
        )

    return guardian

def update_guardian(guardian_id, first_name, last_name=None, middle_name=None,
                    email_address=None, mobile_phone_number=None, alternate_phone=None,
                    occupation=None, home_address=None, city=None, state=None, country="India", postal_code=None):
    """
    Update guardian profile and contact details.
    """
    guardian = Guardian.query.get(guardian_id)
    if not guardian:
        raise ValueError("Guardian record not found.")

    guardian.first_name = first_name.strip()
    guardian.middle_name = middle_name.strip() if middle_name else None
    guardian.last_name = last_name.strip() if last_name else None
    guardian.sync_full_name()

    guardian.email_address = email_address.strip() if email_address else None
    guardian.mobile_phone_number = mobile_phone_number.strip() if mobile_phone_number else None
    guardian.alternate_phone = alternate_phone.strip() if alternate_phone else None
    guardian.occupation = occupation.strip() if occupation else None

    guardian.home_address = home_address.strip() if home_address else None
    guardian.city = city.strip() if city else None
    guardian.state = state.strip() if state else None
    guardian.country = country.strip() if country else "India"
    guardian.postal_code = postal_code.strip() if postal_code else None

    db.session.commit()
    return guardian

def link_guardian_student(guardian_id, student_id, relationship="Father", is_primary=False, is_emergency_contact=False, can_receive_notifications=True):
    """
    Connect a Guardian to a Student with relationship metadata.
    Prevents duplicate links. If is_primary=True, resets previous primary status for this student.
    """
    guardian = Guardian.query.get(guardian_id)
    if not guardian:
        raise ValueError("Guardian record not found.")

    student = Student.query.get(student_id)
    if not student:
        raise ValueError("Student record not found.")

    # Check existing link
    link = GuardianStudent.query.filter_by(guardian_id=guardian_id, student_id=student_id).first()

    if is_primary:
        # Reset other primary links for this student so only ONE primary guardian exists
        other_links = GuardianStudent.query.filter_by(student_id=student_id).all()
        for ol in other_links:
            if ol.id != (link.id if link else None):
                ol.is_primary = False

    if link:
        link.relationship = relationship
        link.is_primary = is_primary
        link.is_emergency_contact = is_emergency_contact
        link.can_receive_notifications = can_receive_notifications
    else:
        link = GuardianStudent(
            guardian_id=guardian_id,
            student_id=student_id,
            relationship=relationship,
            is_primary=is_primary,
            is_emergency_contact=is_emergency_contact,
            can_receive_notifications=can_receive_notifications
        )
        db.session.add(link)

    db.session.commit()
    return link

def unlink_guardian_student(guardian_id, student_id):
    """
    Remove the relationship link between a guardian and a student.
    Does NOT delete either person's profile record!
    """
    link = GuardianStudent.query.filter_by(guardian_id=guardian_id, student_id=student_id).first()
    if not link:
        raise ValueError("Relationship link between this guardian and student does not exist.")

    db.session.delete(link)
    db.session.commit()
    return True

def toggle_guardian_status(guardian_id):
    """Toggle guardian active/inactive status."""
    guardian = Guardian.query.get(guardian_id)
    if not guardian:
        raise ValueError("Guardian record not found.")

    guardian.is_active = not guardian.is_active
    guardian.status = "Active" if guardian.is_active else "Inactive"
    db.session.commit()
    return guardian
