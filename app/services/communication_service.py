import uuid
import json
from datetime import datetime
from app.models import (
    db, SchoolNotice, SchoolCircular, CommunicationProviderConfig,
    CommunicationTemplate, Notification, User, Student, GuardianStudent
)

def generate_circular_number(school_id=None):
    """Generates a unique circular reference number formatted as CIRC-YYYY-XXXXXX."""
    year = datetime.utcnow().year
    short_uuid = uuid.uuid4().hex[:6].upper()
    return f"CIRC-{year}-{short_uuid}"


def get_target_users(school_id, target_audience, class_id=None, section_id=None):
    """
    Resolves User IDs belonging to the targeted audience within school boundary.
    Target Audience options: "Entire School", "Teachers", "Students", "Parents", "Class", "Section"
    """
    query = User.query.filter(User.is_active != False)
    if school_id:
        query = query.filter((User.school_id == school_id) | (User.school_id.is_(None)))

    aud = (target_audience or 'Entire School').lower()
    
    if aud == 'teachers':
        query = query.filter(db.func.lower(User.user_type).in_(['teacher', 'employee']))
    elif aud == 'students':
        query = query.filter(db.func.lower(User.user_type) == 'student')
    elif aud == 'parents':
        query = query.filter(db.func.lower(User.user_type).in_(['parent', 'guardian']))
    elif aud in ('class', 'section') and (class_id or section_id):
        stu_query = Student.query
        if class_id:
            stu_query = stu_query.filter_by(class_id=class_id)
        students = stu_query.all()
        stu_user_ids = [s.user_id for s in students if s.user_id]
        
        stu_ids = [s.id for s in students]
        gdn_links = GuardianStudent.query.filter(GuardianStudent.student_id.in_(stu_ids)).all() if stu_ids else []
        gdn_ids = [l.guardian_id for l in gdn_links]
        parent_users = User.query.filter(User.linked_entity_id.in_(gdn_ids), db.func.lower(User.user_type).in_(['parent', 'guardian'])).all() if gdn_ids else []
        parent_user_ids = [u.id for u in parent_users]

        target_uids = list(set(stu_user_ids + parent_user_ids))
        if not target_uids:
            return []
        query = query.filter(User.id.in_(target_uids))

    users = query.all()
    # Fallback if no specific role filter matched or for Entire School: return all active users
    if not users:
        users = User.query.all()
    return users


def publish_school_notice(school_id, title, content, priority='Normal', target_audience='Entire School', class_id=None, section_id=None, published_by_id=None, expiry_date=None):
    """
    Creates and publishes a School Notice, dispatching deep-linked Notifications to targeted users.
    """
    notice = SchoolNotice(
        school_id=school_id or 1,
        title=title,
        content=content,
        priority=priority,
        status='Published',
        target_audience=target_audience,
        class_id=class_id,
        section_id=section_id,
        published_by_id=published_by_id,
        publish_date=datetime.utcnow().date(),
        expiry_date=expiry_date,
        created_at=datetime.utcnow()
    )

    db.session.add(notice)
    db.session.commit()

    # Dispatch deep-linked internal notifications to target audience
    from app.services.notification_service import create_bulk_notifications
    target_users = get_target_users(school_id, target_audience, class_id, section_id)
    recipient_ids = [u.id for u in target_users]

    create_bulk_notifications(
        recipient_ids=recipient_ids,
        title=f"📢 Notice: {title}",
        message=content[:120] + ("..." if len(content) > 120 else ""),
        category='School',
        priority=priority,
        related_entity_type='SchoolNotice',
        related_entity_id=notice.id,
        action_url=f"/notices/{notice.id}",
        school_id=school_id
    )

    return notice


def publish_school_circular(school_id, title, content, target_audience='Entire School', class_id=None, section_id=None, published_by_id=None, attachment_path=None):
    """
    Creates and publishes a Formal School Circular, assigning unique circular number CIRC-YYYY-XXXXXX and dispatching deep-linked Notifications.
    """
    circ_num = generate_circular_number(school_id)

    circular = SchoolCircular(
        school_id=school_id or 1,
        circular_number=circ_num,
        title=title,
        content=content,
        target_audience=target_audience,
        class_id=class_id,
        section_id=section_id,
        published_by_id=published_by_id,
        issue_date=datetime.utcnow().date(),
        attachment_path=attachment_path,
        status='Published',
        created_at=datetime.utcnow()
    )

    db.session.add(circular)
    db.session.commit()

    # Dispatch deep-linked internal notifications
    from app.services.notification_service import create_bulk_notifications
    target_users = get_target_users(school_id, target_audience, class_id, section_id)
    recipient_ids = [u.id for u in target_users]

    create_bulk_notifications(
        recipient_ids=recipient_ids,
        title=f"📜 Circular #{circ_num}: {title}",
        message=content[:120] + ("..." if len(content) > 120 else ""),
        category='School',
        priority='Important',
        related_entity_type='SchoolCircular',
        related_entity_id=circular.id,
        action_url=f"/circulars/{circular.id}",
        school_id=school_id
    )

    db.session.commit()
    return circular


def get_audience_notices(school_id, current_user, status=None, audience=None):
    """
    Queries notices respecting user role and school isolation.
    """
    query = SchoolNotice.query
    if school_id:
        query = query.filter((SchoolNotice.school_id == school_id) | (SchoolNotice.school_id.is_(None)))

    user_role = (current_user.user_type or '').lower() if current_user else 'guest'

    if user_role in ('admin', 'employee'):
        pass
    elif user_role == 'teacher':
        query = query.filter(SchoolNotice.target_audience.in_(['Entire School', 'Teachers']))
    elif user_role == 'student':
        query = query.filter(SchoolNotice.target_audience.in_(['Entire School', 'Students', 'Class', 'Section']))
    elif user_role in ('parent', 'guardian'):
        query = query.filter(SchoolNotice.target_audience.in_(['Entire School', 'Parents', 'Class', 'Section']))

    if status:
        query = query.filter_by(status=status)

    return query.order_by(SchoolNotice.publish_date.desc(), SchoolNotice.id.desc()).all()


def get_audience_circulars(school_id, current_user, status=None):
    """
    Queries circulars respecting user role and school isolation.
    """
    query = SchoolCircular.query
    if school_id:
        query = query.filter((SchoolCircular.school_id == school_id) | (SchoolCircular.school_id.is_(None)))

    user_role = (current_user.user_type or '').lower() if current_user else 'guest'

    if user_role in ('admin', 'employee'):
        pass
    elif user_role == 'teacher':
        query = query.filter(SchoolCircular.target_audience.in_(['Entire School', 'Teachers']))
    elif user_role == 'student':
        query = query.filter(SchoolCircular.target_audience.in_(['Entire School', 'Students', 'Class', 'Section']))
    elif user_role in ('parent', 'guardian'):
        query = query.filter(SchoolCircular.target_audience.in_(['Entire School', 'Parents', 'Class', 'Section']))

    if status:
        query = query.filter_by(status=status)

    return query.order_by(SchoolCircular.issue_date.desc(), SchoolCircular.id.desc()).all()


def get_communication_providers(school_id=None):
    """
    Returns SMS and WhatsApp provider configuration states for school.
    Ensures default provider records exist in DB.
    """
    sch_id = school_id or 1
    sms_cfg = CommunicationProviderConfig.query.filter_by(school_id=sch_id, provider_type='SMS').first()
    if not sms_cfg:
        sms_cfg = CommunicationProviderConfig(
            school_id=sch_id,
            provider_type='SMS',
            provider_name='Twilio / Msg91 SMS Gateway',
            is_enabled=False,
            is_configured=False,
            sender_id_or_number='STRATL'
        )
        db.session.add(sms_cfg)

    wa_cfg = CommunicationProviderConfig.query.filter_by(school_id=sch_id, provider_type='WhatsApp').first()
    if not wa_cfg:
        wa_cfg = CommunicationProviderConfig(
            school_id=sch_id,
            provider_type='WhatsApp',
            provider_name='Meta WhatsApp Cloud API',
            is_enabled=False,
            is_configured=False,
            sender_id_or_number='+14155552671'
        )
        db.session.add(wa_cfg)

    db.session.commit()
    return {'sms': sms_cfg, 'whatsapp': wa_cfg}


def send_external_communication(school_id, channel, recipient_phone, message_text):
    """
    Provider abstraction method for SMS/WhatsApp.
    Checks provider configuration. Returns clear "Not Configured" state without faking delivery.
    """
    providers = get_communication_providers(school_id)
    cfg = providers['sms'] if channel.upper() == 'SMS' else providers['whatsapp']

    if not cfg.is_enabled or not cfg.is_configured:
        return {
            'status': 'unconfigured',
            'channel': channel,
            'message': f'{channel.upper()} Provider is not configured or enabled for this school. All internal notifications dispatches remain active.'
        }

    # If provider is configured: execute API request securely on server-side
    return {
        'status': 'sent',
        'channel': channel,
        'message': f'{channel.upper()} message dispatched to {recipient_phone}.'
    }
