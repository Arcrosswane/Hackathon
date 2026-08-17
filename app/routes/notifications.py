from flask import Blueprint, render_template, request, jsonify, session, flash, redirect, url_for
from app.models import db, User, Notification
from app.utils.decorators import login_required
from app.services.notification_service import (
    get_user_notifications,
    get_unread_notification_count,
    mark_notification_as_read,
    mark_all_notifications_as_read
)

notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')


@notifications_bp.route('/')
@login_required
def center():
    """Renders the Centralized School Notification Center workspace."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None

    if not current_user:
        flash('Authentication required to access Notification Center.', 'danger')
        return redirect(url_for('auth.login'))

    category = request.args.get('category', 'All').strip()
    page = request.args.get('page', 1, type=int)

    notifications_data = get_user_notifications(
        current_user=current_user,
        category=category,
        page=page,
        per_page=20
    )

    categories = ['All', 'Academic', 'Attendance', 'Homework', 'Exams', 'Fees', 'Communication', 'School', 'Behaviour', 'System']

    return render_template(
        'notifications/center.html',
        current_user=current_user,
        notifications_data=notifications_data,
        active_category=category,
        categories=categories,
        unread_count=notifications_data['unread_count']
    )


@notifications_bp.route('/api/list', methods=['GET'])
@login_required
def api_list_notifications():
    """JSON API endpoint returning paginated notifications for current user."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

    category = request.args.get('category', 'All').strip()
    is_unread_only = request.args.get('unread_only', 'false').lower() == 'true'
    page = request.args.get('page', 1, type=int)

    data = get_user_notifications(
        current_user=current_user,
        category=category,
        is_unread_only=is_unread_only,
        page=page,
        per_page=20
    )
    data['status'] = 'success'
    return jsonify(data)


@notifications_bp.route('/api/unread-count', methods=['GET'])
@login_required
def api_unread_count():
    """JSON API endpoint returning total unread notifications count for current user."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user:
        return jsonify({'unread_count': 0})

    cnt = get_unread_notification_count(current_user)
    return jsonify({'status': 'success', 'unread_count': cnt})


@notifications_bp.route('/api/<int:notification_id>/read', methods=['POST'])
@login_required
def api_mark_read(notification_id):
    """JSON API endpoint marking a single notification as read."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

    success = mark_notification_as_read(current_user, notification_id)
    if not success:
        return jsonify({'status': 'error', 'message': 'Notification not found or access denied.'}), 404

    return jsonify({
        'status': 'success',
        'message': 'Notification marked as read.',
        'unread_count': get_unread_notification_count(current_user)
    })


@notifications_bp.route('/api/read-all', methods=['POST'])
@login_required
def api_mark_all_read():
    """JSON API endpoint marking all unread notifications for current user as read."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

    count = mark_all_notifications_as_read(current_user)
    return jsonify({
        'status': 'success',
        'marked_count': count,
        'unread_count': 0,
        'message': f'{count} notifications marked as read.'
    })


@notifications_bp.route('/open/<int:notification_id>')
@login_required
def open_deep_link(notification_id):
    """
    Secure deep link handler.
    Verifies notification ownership, marks it read, and safely redirects to target action URL.
    """
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user:
        flash('Authentication required.', 'danger')
        return redirect(url_for('auth.login'))

    notification = Notification.query.filter_by(id=notification_id, recipient_id=current_user.id).first()
    if not notification:
        flash('Notification not found or access denied.', 'danger')
        return redirect(url_for('notifications.center'))

    # Mark as read
    mark_notification_as_read(current_user, notification_id)

    # Safe target redirect
    target_url = notification.action_url
    if target_url and target_url.startswith('/'):
        return redirect(target_url)

    # Fallback to category defaults
    cat = (notification.category or '').lower()
    if cat == 'communication':
        return redirect(url_for('notifications.center'))
    elif cat == 'homework':
        role = str(session.get('user_role', '')).lower()
        if role == 'student':
            return redirect(url_for('homework.student_index'))
        elif role in ('parent', 'guardian'):
            return redirect(url_for('homework.parent_index'))
        return redirect(url_for('homework.manage'))
    elif cat == 'exams':
        role = str(session.get('user_role', '')).lower()
        if role == 'student':
            return redirect(url_for('examination.student_results'))
        elif role in ('parent', 'guardian'):
            return redirect(url_for('examination.parent_results'))
        return redirect(url_for('examination.exams_list'))
    elif cat == 'fees':
        return redirect(url_for('fees.student_fee_account'))

    return redirect(url_for('notifications.center'))
