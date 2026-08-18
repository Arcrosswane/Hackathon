from flask import Blueprint, render_template, request, session, flash, redirect, url_for
from app.models import db, User, CommunicationProviderConfig, CommunicationTemplate
from app.utils.decorators import login_required
from app.services.communication_service import (
    get_communication_providers,
    send_external_communication
)

communication_bp = Blueprint('communication', __name__, url_prefix='/communication')


@communication_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Renders SMS & WhatsApp Provider Gateway Configuration Page."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user:
        return redirect(url_for('auth.login'))

    user_role = (current_user.user_type or '').lower()
    if user_role != 'admin':
        flash('Permission denied to communication channel settings.', 'danger')
        return redirect(url_for('notifications.center'))

    sch_id = current_user.school_id or 1
    providers = get_communication_providers(sch_id)

    if request.method == 'POST':
        action = request.form.get('action', '')
        
        if action == 'save_sms':
            providers['sms'].is_enabled = 'is_enabled' in request.form
            providers['sms'].sender_id_or_number = request.form.get('sender_id', 'STRATL').strip()
            api_key = request.form.get('api_key', '').strip()
            if api_key:
                providers['sms'].api_key_masked = api_key[:4] + "****" + api_key[-4:] if len(api_key) > 8 else "****"
                providers['sms'].is_configured = True
            db.session.commit()
            flash('SMS Gateway settings updated.', 'success')

        elif action == 'save_whatsapp':
            providers['whatsapp'].is_enabled = 'is_enabled' in request.form
            providers['whatsapp'].sender_id_or_number = request.form.get('sender_number', '+14155552671').strip()
            api_key = request.form.get('api_key', '').strip()
            if api_key:
                providers['whatsapp'].api_key_masked = api_key[:4] + "****" + api_key[-4:] if len(api_key) > 8 else "****"
                providers['whatsapp'].is_configured = True
            db.session.commit()
            flash('WhatsApp Gateway settings updated.', 'success')

        elif action == 'test_send':
            channel = request.form.get('channel', 'SMS')
            phone = request.form.get('phone', '+91 9876543210')
            result = send_external_communication(sch_id, channel, phone, "Test Message")
            if result['status'] == 'unconfigured':
                flash(f"⚠️ {result['message']}", 'warning')
            else:
                flash(f"✓ {result['message']}", 'success')

        return redirect(url_for('communication.settings'))

    return render_template(
        'communication/settings.html',
        current_user=current_user,
        providers=providers
    )


@communication_bp.route('/templates', methods=['GET', 'POST'])
@login_required
def templates():
    """Renders Reusable Communication Templates Page."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user:
        return redirect(url_for('auth.login'))

    sch_id = current_user.school_id or 1

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        channel = request.form.get('channel', 'SMS').strip()
        template_code = request.form.get('template_code', '').strip().upper()
        content = request.form.get('content', '').strip()

        if name and content and template_code:
            tmpl = CommunicationTemplate(
                school_id=sch_id,
                name=name,
                channel=channel,
                template_code=template_code,
                content_template=content
            )
            db.session.add(tmpl)
            db.session.commit()
            flash('Communication template saved.', 'success')
            return redirect(url_for('communication.templates'))

    template_list = CommunicationTemplate.query.filter_by(school_id=sch_id).all()

    return render_template(
        'communication/templates.html',
        current_user=current_user,
        templates=template_list
    )
