from flask import Blueprint, render_template, session
from app.utils.decorators import login_required, role_required
from app.services.academic_service import get_active_academic_session
from app.services.homework_service import get_student_eligible_homework
from app.models import User, Student, StudentEnrollment

student_bp = Blueprint('student', __name__, url_prefix='/student')

@student_bp.route('/dashboard')
@login_required
@role_required('student')
def dashboard():
    active_session = get_active_academic_session()
    
    # Resolve current student ID & entity
    user_id = session.get('user_id')
    u = User.query.get(user_id) if user_id else None
    student_id = u.linked_entity_id if (u and u.linked_entity_id) else session.get('linked_entity_id')

    student = Student.query.get(student_id) if student_id else None
    enrollment = None
    if student_id and active_session:
        enrollment = StudentEnrollment.query.filter_by(
            student_id=student_id,
            academic_session_id=active_session.id,
            is_current=True
        ).first()

    homework_items = get_student_eligible_homework(
        student_id=student_id,
        session_id=active_session.id if active_session else None
    )

    pending_cnt = sum(1 for item in homework_items if item['submission_status'] in ('NOT_SUBMITTED', 'MISSING'))
    submitted_cnt = sum(1 for item in homework_items if item['submission_status'] in ('SUBMITTED', 'LATE', 'REVIEWED'))

    return render_template(
        'student/dashboard.html',
        active_session=active_session,
        student=student,
        enrollment=enrollment,
        homework_items=homework_items[:5],
        pending_cnt=pending_cnt,
        submitted_cnt=submitted_cnt
    )
