from flask import Blueprint, render_template, session
from app.utils.decorators import login_required, role_required
from app.services.academic_service import get_active_academic_session
from app.services.homework_service import get_all_homework, get_homework_submission_roster
from app.models import User, Employee, Timetable, Homework

teacher_bp = Blueprint('teacher', __name__, url_prefix='/teacher')

@teacher_bp.route('/dashboard')
@login_required
@role_required('teacher', 'employee')
def dashboard():
    active_session = get_active_academic_session()
    
    # Resolve current teacher ID & entity
    user_id = session.get('user_id')
    u = User.query.get(user_id) if user_id else None
    teacher_id = u.linked_entity_id if (u and u.linked_entity_id) else None
    if not teacher_id:
        first_t = Employee.query.filter_by(is_teacher=True).first()
        teacher_id = first_t.id if first_t else None

    teacher = Employee.query.get(teacher_id) if teacher_id else None

    # Resolve assigned classes & sections for teacher in active session
    assigned_classes = []
    if teacher and active_session:
        class_sec_set = set()
        
        tt_entries = Timetable.query.filter_by(
            academic_session_id=active_session.id,
            employee_id=teacher.id
        ).all()
        for tt in tt_entries:
            if tt.school_class:
                sec_str = tt.section.display_name if tt.section else "All Sections"
                class_sec_set.add((tt.school_class.display_name, sec_str))

        hw_entries = Homework.query.filter_by(
            academic_session_id=active_session.id,
            teacher_id=teacher.id
        ).all()
        for hw in hw_entries:
            if hw.school_class:
                sec_str = hw.section.display_name if hw.section else "All Sections"
                class_sec_set.add((hw.school_class.display_name, sec_str))

        assigned_classes = [f"{c} - {s}" for c, s in sorted(class_sec_set)]

    homework_list = get_all_homework(
        session_id=active_session.id if active_session else None,
        teacher_id=teacher_id
    ) if active_session else []

    recent_hw = []
    total_assigned = len(homework_list)
    pending_reviews_total = 0

    for hw in homework_list[:5]:
        roster, summary = get_homework_submission_roster(hw.id)
        pending_reviews_total += (summary['submitted_count'] - summary['reviewed_count'])
        recent_hw.append({
            'homework': hw,
            'summary': summary
        })

    return render_template(
        'teacher/dashboard.html',
        active_session=active_session,
        teacher=teacher,
        assigned_classes=assigned_classes,
        recent_hw=recent_hw,
        total_assigned=total_assigned,
        pending_reviews_total=pending_reviews_total
    )
