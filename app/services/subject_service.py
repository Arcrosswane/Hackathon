from app.models import db, Subject, SubjectClass, SchoolClass

def get_all_subjects(active_only=False):
    """Returns list of subjects ordered by name."""
    query = Subject.query
    if active_only:
        query = query.filter_by(is_active=True)
    return query.order_by(Subject.name.asc()).all()

def get_active_subjects():
    """Returns active subjects for selection menus."""
    return get_all_subjects(active_only=True)

def get_subject_by_id(subject_id):
    """Retrieve subject record by primary key."""
    return Subject.query.get(subject_id)

def create_subject(name, code=None, short_name=None, subject_type="core", description=None):
    """
    Create a new subject in the catalog.
    Enforces uniqueness of subject name.
    """
    existing = Subject.query.filter_by(name=name).first()
    if existing:
        raise ValueError(f"Subject with name '{name}' already exists.")

    if not code or not str(code).strip():
        clean_n = "".join(e for e in name.upper() if e.isalnum())[:4] or "SUB"
        code = f"SUB-{clean_n}"
        count = 1
        while Subject.query.filter_by(code=code).first():
            code = f"SUB-{clean_n}{count}"
            count += 1
    else:
        code = code.strip().upper()

    if not short_name:
        short_name = name[:10]

    subject = Subject(
        code=code,
        name=name,
        short_name=short_name,
        subject_type=subject_type or "core",
        description=description,
        is_active=True
    )
    db.session.add(subject)
    db.session.commit()
    return subject

def update_subject(subject_id, name, code=None, short_name=None, subject_type="core", description=None):
    """Update subject metadata."""
    subject = Subject.query.get(subject_id)
    if not subject:
        raise ValueError("Subject not found.")

    if name != subject.name:
        existing = Subject.query.filter_by(name=name).first()
        if existing:
            raise ValueError(f"Subject name '{name}' already taken.")

    subject.name = name
    subject.code = code.upper() if code else None
    subject.short_name = short_name or name[:10]
    subject.subject_type = subject_type or "core"
    subject.description = description

    db.session.commit()
    return subject

def get_subjects_for_class(class_id, active_only=True):
    """
    Returns list of Subject instances assigned to a specific class.
    Future modules (Timetable, Homework, Exams, Marks) consume this function.
    """
    query = db.session.query(Subject).join(SubjectClass, Subject.id == SubjectClass.subject_id)\
                      .filter(SubjectClass.class_id == class_id)
    if active_only:
        query = query.filter(Subject.is_active == True, SubjectClass.is_active == True)
    return query.order_by(Subject.name.asc()).all()

def get_classes_for_subject(subject_id, active_only=True):
    """Returns list of SchoolClass instances using a particular subject."""
    query = db.session.query(SchoolClass).join(SubjectClass, SchoolClass.id == SubjectClass.class_id)\
                         .filter(SubjectClass.subject_id == subject_id)
    if active_only:
        query = query.filter(SchoolClass.is_active == True, SubjectClass.is_active == True)
    return query.order_by(SchoolClass.numeric_order.asc(), SchoolClass.name.asc()).all()

def assign_subject_to_class(subject_id, class_id):
    """
    Assign a subject to a class.
    Enforces uniqueness so duplicate assignment is prevented.
    """
    subject = Subject.query.get(subject_id)
    school_class = SchoolClass.query.get(class_id)

    if not subject:
        raise ValueError("Subject does not exist.")
    if not school_class:
        raise ValueError("Class does not exist.")
    if not subject.is_active:
        raise ValueError(f"Cannot assign inactive subject '{subject.name}'.")

    existing = SubjectClass.query.filter_by(subject_id=subject_id, class_id=class_id).first()
    if existing:
        if not existing.is_active:
            existing.is_active = True
            db.session.commit()
            return existing
        raise ValueError(f"Subject '{subject.name}' is already assigned to {school_class.display_name}.")

    assignment = SubjectClass(subject_id=subject_id, class_id=class_id, is_active=True)
    db.session.add(assignment)
    db.session.commit()
    return assignment

def remove_subject_from_class(subject_id, class_id):
    """Remove subject-class assignment."""
    assignment = SubjectClass.query.filter_by(subject_id=subject_id, class_id=class_id).first()
    if assignment:
        db.session.delete(assignment)
        db.session.commit()
        return True
    return False
