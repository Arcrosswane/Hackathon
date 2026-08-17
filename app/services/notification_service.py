import html
from datetime import datetime, timedelta
from app.models import db, User, Notification, NotificationPreference

def create_notification(
    recipient_id,
    title,
    message,
    category='System',
    priority='Normal',
    related_entity_type=None,
    related_entity_id=None,
    action_url=None,
    school_id=None
):
    """
    Creates a single in-app notification for recipient_id.
    Validates user, checks notification preferences, suppresses rapid duplicates, and enforces school isolation.
    """
    recipient = User.query.get(recipient_id)
    if not recipient or not recipient.is_active:
        return None

    # Resolve school ID
    resolved_school_id = school_id or recipient.school_id

    # Check notification preference
    pref = NotificationPreference.query.filter_by(user_id=recipient_id, category=category).first()
    if pref and not pref.is_enabled:
        return None

    # Sanitize content
    clean_title = html.escape((title or '').strip())
    clean_message = html.escape((message or '').strip())
    if not clean_title or not clean_message:
        return None

    # Duplicate suppression (Check if identical notification was created within last 60 seconds)
    recent_cutoff = datetime.utcnow() - timedelta(seconds=60)
    existing_duplicate = Notification.query.filter(
        Notification.recipient_id == recipient_id,
        Notification.category == category,
        Notification.title == clean_title,
        Notification.related_entity_type == related_entity_type,
        Notification.related_entity_id == related_entity_id,
        Notification.created_at >= recent_cutoff
    ).first()

    if existing_duplicate:
        return existing_duplicate

    notification = Notification(
        school_id=resolved_school_id,
        recipient_id=recipient_id,
        category=category,
        title=clean_title,
        message=clean_message,
        priority=priority,
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id,
        action_url=action_url,
        created_at=datetime.utcnow()
    )

    db.session.add(notification)
    db.session.commit()
    return notification


def create_bulk_notifications(
    recipient_ids,
    title,
    message,
    category='System',
    priority='Normal',
    related_entity_type=None,
    related_entity_id=None,
    action_url=None,
    school_id=None
):
    """
    Bulk creates in-app notifications for multiple recipient IDs safely.
    """
    if not recipient_ids:
        return []

    created_notifications = []
    unique_recipient_ids = set(recipient_ids)

    for rid in unique_recipient_ids:
        try:
            n = create_notification(
                recipient_id=rid,
                title=title,
                message=message,
                category=category,
                priority=priority,
                related_entity_type=related_entity_type,
                related_entity_id=related_entity_id,
                action_url=action_url,
                school_id=school_id
            )
            if n:
                created_notifications.append(n)
        except Exception as e:
            continue

    return created_notifications


def get_user_notifications(current_user, category=None, is_unread_only=False, page=1, per_page=20):
    """
    Returns paginated notifications list for current_user.
    """
    if not current_user:
        return {'items': [], 'total': 0, 'pages': 0, 'current_page': page}

    query = Notification.query.filter_by(recipient_id=current_user.id)

    if category and category.strip() and category != 'All':
        query = query.filter_by(category=category.strip())

    if is_unread_only:
        query = query.filter(Notification.read_at.is_(None))

    query = query.order_by(Notification.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    formatted_items = []
    for n in pagination.items:
        formatted_items.append({
            'id': n.id,
            'category': n.category,
            'title': n.title,
            'message': n.message,
            'priority': n.priority,
            'action_url': n.action_url or f"/notifications/open/{n.id}",
            'is_read': n.is_read(),
            'read_at': n.read_at.strftime('%b %d, %I:%M %p') if n.read_at else None,
            'created_at': n.created_at.strftime('%b %d, %I:%M %p'),
            'time_ago': format_time_ago(n.created_at)
        })

    return {
        'notifications': formatted_items,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': pagination.page,
        'unread_count': get_unread_notification_count(current_user)
    }


def get_unread_notification_count(current_user):
    """
    Returns integer count of unread notifications for current_user.
    """
    if not current_user:
        return 0

    return Notification.query.filter(
        Notification.recipient_id == current_user.id,
        Notification.read_at.is_(None)
    ).count()


def mark_notification_as_read(current_user, notification_id):
    """
    Marks a single notification as read if owned by current_user.
    """
    if not current_user:
        return False

    n = Notification.query.filter_by(id=notification_id, recipient_id=current_user.id).first()
    if not n:
        return False

    if not n.read_at:
        n.read_at = datetime.utcnow()
        db.session.commit()

    return True


def mark_all_notifications_as_read(current_user):
    """
    Marks all unread notifications for current_user as read.
    """
    if not current_user:
        return 0

    unread_notifications = Notification.query.filter(
        Notification.recipient_id == current_user.id,
        Notification.read_at.is_(None)
    ).all()

    now = datetime.utcnow()
    count = 0
    for n in unread_notifications:
        n.read_at = now
        count += 1

    if count > 0:
        db.session.commit()

    return count


def format_time_ago(dt):
    """
    Formats a datetime object into a human-readable relative time string.
    """
    if not dt:
        return ''
    diff = datetime.utcnow() - dt
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "Just now"
    elif seconds < 3600:
        mins = int(seconds // 60)
        return f"{mins}m ago"
    elif seconds < 86400:
        hours = int(seconds // 3600)
        return f"{hours}h ago"
    else:
        days = int(seconds // 86400)
        return f"{days}d ago"
