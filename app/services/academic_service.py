from app.models import db, AcademicSession

def get_active_academic_session():
    """
    Returns the current active AcademicSession instance, or None if no session is active.
    Future modules can call this helper to scope queries to the active session.
    """
    return AcademicSession.query.filter_by(is_active=True).first()

def set_active_academic_session(session_id):
    """
    Safely activates session_id and deactivates all other academic sessions in a single database transaction.
    """
    session_to_activate = AcademicSession.query.get(session_id)
    if not session_to_activate:
        raise ValueError(f"AcademicSession with ID {session_id} does not exist.")

    # Transactionally deactivate all sessions
    AcademicSession.query.update({AcademicSession.is_active: False})
    
    # Activate target session
    session_to_activate.is_active = True
    db.session.commit()
    return session_to_activate
