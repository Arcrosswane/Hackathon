from flask import Blueprint, render_template, request, jsonify, session, flash, redirect, url_for
from app.models import db, User, Student, StudentEnrollment
from app.utils.decorators import login_required, role_required
from app.services.student_dashboard_service import get_student_dashboard_summary

student_bp = Blueprint('student', __name__, url_prefix='/student')

@student_bp.route('/dashboard')
@login_required
@role_required('student')
def dashboard():
    """Student's Personal Learning Workspace Dashboard at /student/dashboard."""
    user_id = session.get('user_id')
    summary = get_student_dashboard_summary(user_id=user_id)

    if request.args.get('format') == 'json' or request.headers.get('Accept') == 'application/json':
        api_summary = {
            'today': summary['today'].strftime('%Y-%m-%d'),
            'day_name': summary['day_name'],
            'student_name': summary['student'].full_name if summary['student'] else "Student Member",
            'enrolled_class': summary['enrollment'].school_class.display_name if (summary['enrollment'] and summary['enrollment'].school_class) else "Grade 9",
            'enrolled_section': summary['enrollment'].section.display_name if (summary['enrollment'] and summary['enrollment'].section) else "Section A",
            'today_timetable_count': len(summary['today_timetable']),
            'current_class': summary['current_class'].subject.name if (summary['current_class'] and summary['current_class'].subject) else None,
            'next_class': summary['next_class'].subject.name if (summary['next_class'] and summary['next_class'].subject) else None,
            'pending_tasks': summary['pending_tasks'],
            'homework_overview': summary['homework_overview'],
            'attendance_overview': summary['attendance_overview'],
            'documents_overview': summary['documents_overview']
        }
        return jsonify(api_summary)

    return render_template('student/dashboard.html', summary=summary)


@student_bp.route('/dashboard/api-data')
@login_required
@role_required('student')
def dashboard_api_data():
    """JSON Summary endpoint for async student workspace refresh."""
    user_id = session.get('user_id')
    summary = get_student_dashboard_summary(user_id=user_id)
    return jsonify({
        'status': 'success',
        'pending_tasks': summary['pending_tasks'],
        'today_summary': summary['today_summary'],
        'homework': summary['homework_overview'],
        'attendance': summary['attendance_overview']
    })


@student_bp.route('/account', methods=['GET', 'POST'])
@login_required
@role_required('student')
def account():
    """Personalized Student Profile & Account Settings at /student/account."""
    user_id = session.get('user_id')
    u = User.query.get(user_id) if user_id else None
    
    student = None
    if u and u.linked_entity_id:
        student = Student.query.get(u.linked_entity_id)
    if not student:
        student = Student.query.filter_by(is_active=True).first()

    enrollment = None
    if student:
        enrollment = StudentEnrollment.query.filter_by(student_id=student.id, is_current=True).first()

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        new_password = request.form.get('new_password', '').strip()

        if student:
            if email:
                student.email = email
            if phone:
                student.phone = phone
            if address:
                student.address = address

        if u:
            if email:
                u.email = email
            if new_password:
                u.set_password(new_password)

        try:
            db.session.commit()
            flash('Your student account profile and portal credentials have been updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating student account settings: {str(e)}', 'danger')

        return redirect(url_for('student.account'))

    return render_template(
        'student/account.html',
        student=student,
        enrollment=enrollment,
        user=u
    )
