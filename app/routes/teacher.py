from flask import Blueprint, render_template, request, jsonify, session, flash, redirect, url_for
from app.models import db, User, Employee, Timetable, Period
from app.utils.decorators import login_required, role_required
from app.services.teacher_dashboard_service import get_teacher_dashboard_summary
from app.services.academic_service import get_active_academic_session

teacher_bp = Blueprint('teacher', __name__, url_prefix='/teacher')

@teacher_bp.route('/dashboard')
@login_required
@role_required('teacher', 'employee')
def dashboard():
    """Teacher's Daily Workspace Dashboard at /teacher/dashboard."""
    user_id = session.get('user_id')
    summary = get_teacher_dashboard_summary(user_id=user_id)

    if request.args.get('format') == 'json' or request.headers.get('Accept') == 'application/json':
        api_summary = {
            'today': summary['today'].strftime('%Y-%m-%d'),
            'day_name': summary['day_name'],
            'teacher_name': summary['teacher'].full_name if summary['teacher'] else "Faculty Member",
            'assigned_classes': [c['display'] for c in summary['assigned_classes']],
            'assigned_subjects': [s['subject_name'] for s in summary['assigned_subjects']],
            'today_timetable_count': len(summary['today_timetable']),
            'current_class': summary['current_class'].school_class.display_name if (summary['current_class'] and summary['current_class'].school_class) else None,
            'next_class': summary['next_class'].school_class.display_name if (summary['next_class'] and summary['next_class'].school_class) else None,
            'pending_actions': summary['pending_actions'],
            'homework_overview': {
                'total_assigned': summary['homework_overview'].get('total_assigned', 0),
                'pending_review_count': summary['homework_overview'].get('pending_review_count', 0)
            },
            'exams_overview': {
                'draft_papers_count': summary['exams_overview'].get('draft_papers_count', 0),
                'pending_marks_count': summary['exams_overview'].get('pending_marks_count', 0)
            },
            'payroll_overview': summary['payroll_overview']
        }
        return jsonify(api_summary)

    return render_template('teacher/dashboard.html', summary=summary)


@teacher_bp.route('/dashboard/api-data')
@login_required
@role_required('teacher', 'employee')
def dashboard_api_data():
    """JSON Summary endpoint for async teacher workspace refresh."""
    user_id = session.get('user_id')
    summary = get_teacher_dashboard_summary(user_id=user_id)
    return jsonify({
        'status': 'success',
        'pending_actions': summary['pending_actions'],
        'today_timetable_count': len(summary['today_timetable']),
        'homework': summary['homework_overview'],
        'payroll': summary['payroll_overview']
    })


@teacher_bp.route('/timetable')
@login_required
@role_required('teacher', 'employee')
def my_timetable():
    """Personal Teacher Timetable Schedule View at /teacher/timetable."""
    user_id = session.get('user_id')
    u = User.query.get(user_id) if user_id else None
    
    teacher = None
    if u and u.linked_entity_id:
        teacher = Employee.query.get(u.linked_entity_id)
    if not teacher:
        teacher = Employee.query.filter_by(is_teacher=True, is_active=True).first()

    active_session = get_active_academic_session()
    sess_id = active_session.id if active_session else None

    # Fetch ordered periods
    periods = Period.query.order_by(Period.period_order.asc()).all()
    if not periods:
        periods = Period.query.all()

    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

    # Fetch teacher timetable entries
    tt_entries = []
    if teacher and sess_id:
        from app.models import SubjectClass
        assigned_sc = SubjectClass.query.filter_by(teacher_id=teacher.id, is_active=True).all()
        assigned_subj_ids = {sc.subject_id for sc in assigned_sc if sc.subject_id}
        assigned_class_ids = {sc.class_id for sc in assigned_sc if sc.class_id}

        if assigned_subj_ids:
            tt_query = Timetable.query.filter(
                Timetable.academic_session_id == sess_id,
                Timetable.employee_id == teacher.id,
                Timetable.subject_id.in_(assigned_subj_ids)
            )
            if assigned_class_ids:
                tt_query = tt_query.filter(Timetable.school_class_id.in_(assigned_class_ids))
            tt_entries = tt_query.all()
        else:
            tt_entries = []

    # Build matrix grid[period_id][day_name] = tt_entry
    grid = {}
    for p in periods:
        grid[p.id] = {}
        for d in days:
            grid[p.id][d] = None

    for tt in tt_entries:
        if tt.period_id and tt.day_of_week:
            day_str = tt.day_of_week.capitalize()
            if tt.period_id in grid and day_str in grid[tt.period_id]:
                grid[tt.period_id][day_str] = tt

    return render_template(
        'teacher/timetable.html',
        teacher=teacher,
        active_session=active_session,
        periods=periods,
        days=days,
        grid=grid,
        tt_entries=tt_entries
    )


@teacher_bp.route('/account', methods=['GET', 'POST'])
@login_required
@role_required('teacher', 'employee')
def account():
    """Personal Teacher Account Settings & Profile at /teacher/account."""
    user_id = session.get('user_id')
    u = User.query.get(user_id) if user_id else None
    
    teacher = None
    if u and u.linked_entity_id:
        teacher = Employee.query.get(u.linked_entity_id)
    if not teacher:
        teacher = Employee.query.filter_by(is_teacher=True, is_active=True).first()

    if request.method == 'POST':
        if teacher:
            first_name = request.form.get('first_name', '').strip()
            last_name = request.form.get('last_name', '').strip()
            if first_name or last_name:
                teacher.first_name = first_name or teacher.first_name
                teacher.last_name = last_name or teacher.last_name
                teacher.full_name = f"{teacher.first_name} {teacher.last_name}".strip()

            teacher.email_address = request.form.get('email_address', '').strip() or teacher.email_address
            teacher.mobile_phone_number = request.form.get('mobile_phone_number', '').strip() or teacher.mobile_phone_number
            teacher.alternate_phone = request.form.get('alternate_phone', '').strip() or teacher.alternate_phone
            teacher.educational_qualification = request.form.get('educational_qualification', '').strip() or teacher.educational_qualification
            teacher.home_address = request.form.get('home_address', '').strip() or teacher.home_address
            teacher.city = request.form.get('city', '').strip() or teacher.city
            teacher.state = request.form.get('state', '').strip() or teacher.state
            teacher.postal_code = request.form.get('postal_code', '').strip() or teacher.postal_code

            new_pass = request.form.get('new_password', '').strip()
            if new_pass and u:
                u.set_password(new_pass)

            db.session.commit()
            flash('Your teacher account profile details have been updated successfully!', 'success')
            return redirect(url_for('teacher.account'))

    summary = get_teacher_dashboard_summary(user_id=user_id, teacher_id=teacher.id if teacher else None)
    return render_template('teacher/account.html', teacher=teacher, user=u, summary=summary)
