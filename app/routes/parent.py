from flask import Blueprint, render_template, request, jsonify, session, flash, redirect, url_for
from app.models import db, User, Guardian, StudentEnrollment
from app.utils.decorators import login_required, role_required
from app.services.parent_dashboard_service import get_parent_dashboard_summary

parent_bp = Blueprint('parent', __name__, url_prefix='/parent')

@parent_bp.route('/dashboard', methods=['GET'])
@login_required
@role_required('parent')
def dashboard():
    """Parent Child Monitoring Workspace Dashboard at /parent/dashboard."""
    user_id = session.get('user_id')
    child_id = request.args.get('child_id', type=int)

    summary = get_parent_dashboard_summary(user_id=user_id, child_id=child_id)

    if request.args.get('format') == 'json' or request.headers.get('Accept') == 'application/json':
        selected_student = summary['selected_child']
        api_summary = {
            'today': summary['today'].strftime('%Y-%m-%d'),
            'day_name': summary['day_name'],
            'guardian_name': summary['guardian'].full_name if summary['guardian'] else "Guardian Member",
            'children_count': len(summary['linked_children']),
            'selected_child_id': selected_student.id if selected_student else None,
            'selected_child_name': selected_student.full_name if selected_student else None,
            'enrolled_class': summary['selected_enrollment'].school_class.display_name if (summary['selected_enrollment'] and summary['selected_enrollment'].school_class) else None,
            'today_timetable_count': len(summary['today_timetable']),
            'alerts': summary['alerts'],
            'homework_overview': summary['homework_overview'],
            'attendance_overview': summary['attendance_overview'],
            'fees_overview': summary['fees_overview']
        }
        return jsonify(api_summary)

    return render_template('parent/dashboard.html', summary=summary)


@parent_bp.route('/account', methods=['GET', 'POST'])
@login_required
@role_required('parent')
def account():
    """Personalized Parent Profile & Account Settings at /parent/account."""
    user_id = session.get('user_id')
    u = User.query.get(user_id) if user_id else None

    guardian = None
    if u and u.linked_entity_id:
        guardian = Guardian.query.get(u.linked_entity_id)
    if not guardian:
        guardian = Guardian.query.filter_by(is_active=True).first()

    linked_children = guardian.student_links if guardian else []

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        emergency_contact = request.form.get('emergency_contact', '').strip()
        new_password = request.form.get('new_password', '').strip()

        if guardian:
            if email:
                guardian.email = email
            if phone:
                guardian.phone = phone
            if address:
                guardian.address = address
            if emergency_contact:
                guardian.emergency_contact = emergency_contact

        if u:
            if email:
                u.email = email
            if new_password:
                u.set_password(new_password)

        try:
            db.session.commit()
            flash('Your parent account profile and portal credentials have been updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating parent account settings: {str(e)}', 'danger')

        return redirect(url_for('parent.account'))

    return render_template(
        'parent/account.html',
        guardian=guardian,
        linked_children=linked_children,
        user=u
    )
