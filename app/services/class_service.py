from app.models import db, SchoolClass, Section

def get_classes_for_session(session_id=None, active_only=False):
    """
    Returns an ordered list of classes for a specific academic session.
    If session_id is None, defaults to the active academic session.
    Sorted by numeric_order ASC, then name ASC.
    """
    if not session_id:
        from app.services.academic_service import get_active_academic_session
        act_sess = get_active_academic_session()
        session_id = act_sess.id if act_sess else None

    query = SchoolClass.query
    if session_id:
        query = query.filter_by(academic_session_id=session_id)
    if active_only:
        query = query.filter_by(is_active=True)
    return query.order_by(SchoolClass.numeric_order.asc(), SchoolClass.name.asc()).all()

def get_active_classes_for_session(session_id):
    """Helper for future modules to read active classes."""
    return get_classes_for_session(session_id, active_only=True)

def get_all_classes(active_only=False):
    """Returns all school classes ordered by numeric_order and name."""
    query = SchoolClass.query
    if active_only:
        query = query.filter_by(is_active=True)
    return query.order_by(SchoolClass.numeric_order.asc(), SchoolClass.name.asc()).all()

def get_class_by_id(class_id):
    """Retrieve a class record by primary key."""
    return SchoolClass.query.get(class_id)

def get_sections_for_class(class_id, active_only=False):
    """Returns sections belonging to a specific class."""
    query = Section.query.filter_by(class_id=class_id)
    if active_only:
        query = query.filter_by(is_active=True)
    return query.order_by(Section.name.asc()).all()

def create_class(session_id, name, display_name=None, numeric_order=0, description=None):
    """
    Create a new class within an academic session.
    Enforces uniqueness of class name within the session.
    """
    existing = SchoolClass.query.filter_by(academic_session_id=session_id, name=name).first()
    if existing:
        raise ValueError(f"Class '{name}' already exists in this academic session.")

    if not display_name:
        display_name = f"Class {name}" if name.isdigit() else name

    new_class = SchoolClass(
        academic_session_id=session_id,
        name=name,
        display_name=display_name,
        numeric_order=int(numeric_order),
        description=description
    )
    db.session.add(new_class)
    db.session.commit()
    return new_class

def create_section(class_id, name, display_name=None, capacity=40):
    """
    Create a new section within a class.
    Enforces uniqueness of section name within the parent class.
    """
    existing = Section.query.filter_by(class_id=class_id, name=name).first()
    if existing:
        raise ValueError(f"Section '{name}' already exists in this class.")

    if not display_name:
        display_name = f"Section {name}"

    new_section = Section(
        class_id=class_id,
        name=name,
        display_name=display_name,
        capacity=capacity
    )
    db.session.add(new_section)
    db.session.commit()
    return new_section
