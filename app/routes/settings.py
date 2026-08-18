import os
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session
from werkzeug.utils import secure_filename

from app.models import db, School, AcademicSession
from app.utils.decorators import login_required, role_required
from app.services.academic_service import get_active_academic_session, set_active_academic_session
from app.services.setting_service import get_all_settings, set_setting, get_setting

settings_bp = Blueprint('settings', __name__, url_prefix='/admin/settings')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'svg', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_or_create_school():
    school = School.query.first()
    if not school:
        school = School(
            name="StratLearn Academy",
            school_code="SL-001",
            email="contact@stratlearn.com",
            phone="+91 98765 43210",
            address="123 Education Lane",
            city="Tech City",
            state="State",
            country="India",
            postal_code="500001",
            principal_name="Dr. Academic Director"
        )
        db.session.add(school)
        db.session.commit()
    return school


@settings_bp.route('/')
@login_required
@role_required('admin')
def index():
    return redirect(url_for('settings.school_profile'))


@settings_bp.route('/school', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'teacher', 'employee', 'student', 'parent')
def school_profile():
    school = get_or_create_school()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        code = request.form.get('school_code', '').strip()

        if not name:
            flash('School name is required.', 'danger')
            return render_template('settings/school_profile.html', school=school, active_tab='school')

        school.name = name
        school.school_code = code
        school.email = request.form.get('email', '').strip()
        school.phone = request.form.get('phone', '').strip()
        school.website = request.form.get('website', '').strip()
        school.address = request.form.get('address', '').strip()
        school.city = request.form.get('city', '').strip()
        school.state = request.form.get('state', '').strip()
        school.country = request.form.get('country', '').strip()
        school.postal_code = request.form.get('postal_code', '').strip()
        school.principal_name = request.form.get('principal_name', '').strip()

        # Handle Logo File Upload
        if 'logo' in request.files:
            file = request.files['logo']
            if file and file.filename != '':
                if not allowed_file(file.filename):
                    flash('Invalid image format. Allowed: PNG, JPG, JPEG, GIF, SVG, WEBP.', 'danger')
                    return render_template('settings/school_profile.html', school=school, active_tab='school')

                # Check content size if available
                file.seek(0, os.SEEK_END)
                file_size = file.tell()
                file.seek(0)
                if file_size > MAX_FILE_SIZE:
                    flash('Logo image size must be less than 5MB.', 'danger')
                    return render_template('settings/school_profile.html', school=school, active_tab='school')

                # Save file securely
                upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'logos')
                os.makedirs(upload_dir, exist_ok=True)
                
                ext = file.filename.rsplit('.', 1)[1].lower()
                filename = f"school_logo_{int(datetime.utcnow().timestamp())}.{ext}"
                filepath = os.path.join(upload_dir, filename)
                file.save(filepath)

                # Store relative static path
                school.logo = f"uploads/logos/{filename}"

        db.session.commit()
        flash('School Profile updated successfully!', 'success')
        return redirect(url_for('settings.school_profile'))

    return render_template('settings/school_profile.html', school=school, active_tab='school')


@settings_bp.route('/sessions', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def academic_sessions():
    if request.method == 'POST':
        session_name = request.form.get('name', '').strip()
        start_date_str = request.form.get('start_date', '').strip()
        end_date_str = request.form.get('end_date', '').strip()
        is_active_flag = request.form.get('is_active') == 'on'

        if not session_name or not start_date_str or not end_date_str:
            flash('Session name, start date, and end date are required.', 'danger')
        else:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

                if start_date >= end_date:
                    flash('Start date must be strictly before end date.', 'danger')
                else:
                    new_session = AcademicSession(
                        name=session_name,
                        start_date=start_date,
                        end_date=end_date,
                        is_active=False
                    )
                    db.session.add(new_session)
                    db.session.commit()

                    if is_active_flag or AcademicSession.query.count() == 1:
                        set_active_academic_session(new_session.id)
                    
                    flash(f'Academic Session "{session_name}" created successfully!', 'success')
                    return redirect(url_for('settings.academic_sessions'))
            except ValueError:
                flash('Invalid date format provided.', 'danger')

    sessions = AcademicSession.query.order_by(AcademicSession.start_date.desc()).all()
    active_session = get_active_academic_session()
    return render_template('settings/academic_sessions.html', sessions=sessions, active_session=active_session, active_tab='sessions')


@settings_bp.route('/sessions/<int:session_id>/activate', methods=['POST'])
@login_required
@role_required('admin')
def activate_session(session_id):
    try:
        session_obj = set_active_academic_session(session_id)
        flash(f'Academic Session "{session_obj.name}" is now active!', 'success')
    except Exception as e:
        flash(f'Failed to activate session: {str(e)}', 'danger')
    return redirect(url_for('settings.academic_sessions'))


@settings_bp.route('/general', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def general_settings():
    if request.method == 'POST':
        set_setting('timezone', request.form.get('timezone', 'Asia/Kolkata').strip())
        set_setting('country', request.form.get('country', 'India').strip())
        set_setting('currency', request.form.get('currency', 'INR (₹)').strip())
        set_setting('date_format', request.form.get('date_format', 'YYYY-MM-DD').strip())
        set_setting('time_format', request.form.get('time_format', '12-hour').strip())

        flash('General settings updated successfully!', 'success')
        return redirect(url_for('settings.general_settings'))

    current_settings = get_all_settings()
    return render_template('settings/general_settings.html', settings=current_settings, active_tab='general')


@settings_bp.route('/academic', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def academic_settings():
    if request.method == 'POST':
        passing_pct_str = request.form.get('passing_percentage', '33').strip()
        grading_system = request.form.get('grading_system', 'Percentage').strip()

        try:
            passing_pct = float(passing_pct_str)
            if passing_pct < 0 or passing_pct > 100:
                flash('Passing percentage must be between 0 and 100.', 'danger')
            else:
                set_setting('passing_percentage', str(passing_pct))
                set_setting('grading_system', grading_system)
                
                from app.services.setting_service import log_audit_event
                user_id = session.get('user_id')
                log_audit_event(school_id=1, user_id=user_id, action="Updated Academic Settings", module="SETTINGS", details=f"Passing: {passing_pct}%, Grading: {grading_system}")
                
                flash('Academic settings updated successfully!', 'success')
                return redirect(url_for('settings.academic_settings'))
        except ValueError:
            flash('Passing percentage must be a valid number.', 'danger')

    current_settings = get_all_settings()
    return render_template('settings/academic_settings.html', settings=current_settings, active_tab='academic')


@settings_bp.route('/roles')
@login_required
@role_required('admin')
def roles():
    """Renders Core Roles List & User Access Overview Page."""
    from app.models import User
    role_counts = {
        'ADMIN': User.query.filter((User.user_type == 'admin') | (User.user_type == 'ADMIN')).count(),
        'TEACHER': User.query.filter((User.user_type == 'teacher') | (User.user_type == 'TEACHER') | (User.user_type == 'employee')).count(),
        'STUDENT': User.query.filter((User.user_type == 'student') | (User.user_type == 'STUDENT')).count(),
        'PARENT': User.query.filter((User.user_type == 'parent') | (User.user_type == 'PARENT')).count()
    }
    return render_template('settings/roles.html', role_counts=role_counts, active_tab='roles')


@settings_bp.route('/permissions', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def permissions_matrix():
    """Renders Granular Role-Permission Matrix Page."""
    from app.services.setting_service import get_role_permissions_matrix, update_role_permission, ALL_PERMISSIONS, log_audit_event
    user_id = session.get('user_id')

    if request.method == 'POST':
        form_data = request.form
        for role in ['ADMIN', 'TEACHER', 'STUDENT', 'PARENT']:
            for p_key in ALL_PERMISSIONS:
                form_field = f"perm_{role}_{p_key}"
                is_granted = form_field in form_data
                update_role_permission(role, p_key, is_granted)

        log_audit_event(school_id=1, user_id=user_id, action="Updated Granular Role Permissions Matrix", module="PERMISSIONS")
        flash('Role permissions matrix updated successfully!', 'success')
        return redirect(url_for('settings.permissions_matrix'))

    matrix = get_role_permissions_matrix()
    return render_template('settings/permissions.html', matrix=matrix, all_permissions=ALL_PERMISSIONS, active_tab='permissions')


@settings_bp.route('/communication', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def communication_settings():
    """Renders Communication & SMS/WhatsApp Provider Credentials Configuration."""
    from app.services.setting_service import log_audit_event
    user_id = session.get('user_id')

    if request.method == 'POST':
        set_setting('sms_provider', request.form.get('sms_provider', 'Disabled').strip())
        set_setting('sms_api_key', request.form.get('sms_api_key', '').strip())
        set_setting('sms_sender_id', request.form.get('sms_sender_id', '').strip())

        set_setting('whatsapp_provider', request.form.get('whatsapp_provider', 'Disabled').strip())
        set_setting('whatsapp_api_token', request.form.get('whatsapp_api_token', '').strip())
        set_setting('whatsapp_phone_number_id', request.form.get('whatsapp_phone_number_id', '').strip())

        log_audit_event(school_id=1, user_id=user_id, action="Updated Communication Provider Settings", module="COMMUNICATION")
        flash('Communication Provider configuration updated successfully!', 'success')
        return redirect(url_for('settings.communication_settings'))

    current_settings = get_all_settings()
    sms_configured = bool(current_settings.get('sms_provider') not in ('Disabled', '') and current_settings.get('sms_api_key'))
    wa_configured = bool(current_settings.get('whatsapp_provider') not in ('Disabled', '') and current_settings.get('whatsapp_api_token'))

    return render_template('settings/communication.html', settings=current_settings, sms_configured=sms_configured, wa_configured=wa_configured, active_tab='communication')


@settings_bp.route('/attendance', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def attendance_settings():
    """Renders Attendance Rules & Working Days Settings Page."""
    from app.services.setting_service import log_audit_event
    user_id = session.get('user_id')

    if request.method == 'POST':
        set_setting('attendance_late_threshold', request.form.get('late_threshold', '15').strip())
        set_setting('working_days_per_month', request.form.get('working_days', '24').strip())
        set_setting('auto_absent_notification', request.form.get('auto_absent_notification', 'enabled').strip())

        log_audit_event(school_id=1, user_id=user_id, action="Updated Attendance Rules & Thresholds", module="ATTENDANCE")
        flash('Attendance settings updated successfully!', 'success')
        return redirect(url_for('settings.attendance_settings'))

    current_settings = get_all_settings()
    return render_template('settings/attendance_settings.html', settings=current_settings, active_tab='attendance')


@settings_bp.route('/finance', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def finance_settings():
    """Renders Fee & Payroll Finance Preferences Page."""
    from app.services.setting_service import log_audit_event
    user_id = session.get('user_id')

    if request.method == 'POST':
        set_setting('currency', request.form.get('currency', 'INR (₹)').strip())
        set_setting('fee_invoice_prefix', request.form.get('fee_invoice_prefix', 'INV-').strip())
        set_setting('fee_due_days', request.form.get('fee_due_days', '10').strip())
        set_setting('payroll_cycle', request.form.get('payroll_cycle', 'Monthly').strip())

        log_audit_event(school_id=1, user_id=user_id, action="Updated Finance & Payroll Preferences", module="FINANCE")
        flash('Finance settings updated successfully!', 'success')
        return redirect(url_for('settings.finance_settings'))

    current_settings = get_all_settings()
    return render_template('settings/finance_settings.html', settings=current_settings, active_tab='finance')


@settings_bp.route('/system', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def system_settings():
    """Renders System Preferences & Administrative Audit Logs Page."""
    from app.services.setting_service import log_audit_event, get_audit_logs
    user_id = session.get('user_id')

    if request.method == 'POST':
        set_setting('timezone', request.form.get('timezone', 'Asia/Kolkata').strip())
        set_setting('date_format', request.form.get('date_format', 'YYYY-MM-DD').strip())
        set_setting('time_format', request.form.get('time_format', '12-hour').strip())
        set_setting('pagination_size', request.form.get('pagination_size', '25').strip())

        log_audit_event(school_id=1, user_id=user_id, action="Updated System Preferences", module="SYSTEM")
        flash('System preferences updated successfully!', 'success')
        return redirect(url_for('settings.system_settings'))

    current_settings = get_all_settings()
    audit_logs = get_audit_logs(school_id=1, limit=50)

    return render_template('settings/system.html', settings=current_settings, audit_logs=audit_logs, active_tab='system')
