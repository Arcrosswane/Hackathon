from flask import Blueprint, render_template, request, jsonify, session
from app.models import School, User
from app.utils.decorators import login_required, role_required
from app.services.admin_dashboard_service import get_admin_dashboard_summary

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@login_required
@role_required('Admin', 'admin')
def dashboard():
    """Central School Administration Command Center Dashboard."""
    # Server-side data isolation: derive school_id from authenticated session
    user_id = session.get('user_id')
    school_id = None
    if user_id:
        u = User.query.get(user_id)
        if u and u.school_id:
            school_id = u.school_id

    summary = get_admin_dashboard_summary(school_id=school_id)

    if request.args.get('format') == 'json' or request.headers.get('Accept') == 'application/json':
        # Return summary without unserializable SQLAlchemy objects for JSON API consumers
        api_summary = {
            'today': summary['today'].strftime('%Y-%m-%d'),
            'school_name': summary['school'].name if summary['school'] else "StratLearn Institute",
            'level1_kpis': summary['level1_kpis'],
            'level2_pending_actions': summary['level2_pending_actions'],
            'students_overview': summary['students_overview'],
            'staff_overview': summary['staff_overview'],
            'attendance_overview': summary['attendance_overview'],
            'finance_overview': summary['finance_overview'],
            'payroll_overview': summary['payroll_overview'],
            'exams_overview': {
                'upcoming_exams_count': summary['exams_overview'].get('upcoming_exams_count', 0),
                'draft_results_count': summary['exams_overview'].get('draft_results_count', 0)
            },
            'homework_overview': summary['homework_overview']
        }
        return jsonify(api_summary)

    return render_template('admin/dashboard.html', summary=summary)


@admin_bp.route('/dashboard/api-data')
@login_required
@role_required('Admin', 'admin')
def dashboard_api_data():
    """JSON Summary endpoint for async dashboard refresh."""
    user_id = session.get('user_id')
    school_id = None
    if user_id:
        u = User.query.get(user_id)
        if u and u.school_id:
            school_id = u.school_id

    summary = get_admin_dashboard_summary(school_id=school_id)
    return jsonify({
        'status': 'success',
        'kpis': summary['level1_kpis'],
        'pending_actions': summary['level2_pending_actions'],
        'attendance': summary['attendance_overview'],
        'finance': summary['finance_overview']
    })
