from flask import Blueprint, render_template, request, jsonify, session, flash, redirect, url_for
from app.models import db, User, Conversation, Message
from app.utils.decorators import login_required
from app.services.messaging_service import (
    get_user_display_name_and_role,
    get_authorized_recipients,
    get_or_create_direct_conversation,
    send_message,
    get_user_conversations,
    get_conversation_messages,
    get_total_unread_count
)

messaging_bp = Blueprint('messaging', __name__, url_prefix='/messages')


@messaging_bp.route('/')
@login_required
def inbox():
    """Renders the centralized Cross-Dashboard School Messaging Inbox UI."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None

    if not current_user:
        flash('Authentication required to access messaging.', 'danger')
        return redirect(url_for('auth.login'))

    user_info = get_user_display_name_and_role(current_user)
    initial_conversations = get_user_conversations(current_user)
    initial_recipients = get_authorized_recipients(current_user)
    unread_count = get_total_unread_count(current_user)

    return render_template(
        'messaging/inbox.html',
        current_user=current_user,
        user_info=user_info,
        conversations=initial_conversations,
        authorized_recipients=initial_recipients,
        unread_count=unread_count
    )


@messaging_bp.route('/conversations', methods=['GET'])
@login_required
def list_conversations():
    """JSON API endpoint returning user's active conversations."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

    search_q = request.args.get('q', None)
    conversations = get_user_conversations(current_user, search_query=search_q)
    unread_count = get_total_unread_count(current_user)

    return jsonify({
        'status': 'success',
        'conversations': conversations,
        'unread_count': unread_count
    })


@messaging_bp.route('/conversations', methods=['POST'])
@login_required
def create_conversation():
    """JSON API endpoint creating or fetching a 1-to-1 conversation with recipient_id."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

    data = request.get_json() or {}
    recipient_id = data.get('recipient_id')
    if not recipient_id:
        return jsonify({'status': 'error', 'message': 'Recipient ID is required.'}), 400

    try:
        conv = get_or_create_direct_conversation(current_user, int(recipient_id))
        return jsonify({
            'status': 'success',
            'conversation_id': conv.id,
            'message': 'Conversation resolved successfully.'
        })
    except PermissionError as pe:
        return jsonify({'status': 'error', 'message': str(pe)}), 403
    except ValueError as ve:
        return jsonify({'status': 'error', 'message': str(ve)}), 404
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to open conversation: {str(e)}'}), 500


@messaging_bp.route('/conversations/<int:conversation_id>', methods=['GET'])
@login_required
def get_messages(conversation_id):
    """JSON API endpoint fetching message history for a conversation."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

    try:
        messages = get_conversation_messages(current_user, conversation_id)
        unread_count = get_total_unread_count(current_user)
        return jsonify({
            'status': 'success',
            'conversation_id': conversation_id,
            'messages': messages,
            'unread_count': unread_count
        })
    except PermissionError as pe:
        return jsonify({'status': 'error', 'message': str(pe)}), 403
    except ValueError as ve:
        return jsonify({'status': 'error', 'message': str(ve)}), 404


@messaging_bp.route('/conversations/<int:conversation_id>/send', methods=['POST'])
@login_required
def post_message(conversation_id):
    """JSON API endpoint posting a message to a conversation."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

    data = request.get_json() or {}
    content = data.get('content')
    if not content or not content.strip():
        return jsonify({'status': 'error', 'message': 'Message text cannot be empty.'}), 400

    try:
        msg = send_message(current_user, conversation_id, content)
        sender_info = get_user_display_name_and_role(current_user)
        return jsonify({
            'status': 'success',
            'message': {
                'id': msg.id,
                'sender_id': msg.sender_id,
                'sender_name': sender_info['name'],
                'sender_role': sender_info['role'],
                'sender_initials': sender_info['initials'],
                'content': msg.content,
                'is_me': True,
                'created_at': msg.created_at.strftime('%b %d, %I:%M %p')
            }
        })
    except PermissionError as pe:
        return jsonify({'status': 'error', 'message': str(pe)}), 403
    except ValueError as ve:
        return jsonify({'status': 'error', 'message': str(ve)}), 400


@messaging_bp.route('/unread-count', methods=['GET'])
@login_required
def api_unread_count():
    """JSON API endpoint returning total unread message count."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user:
        return jsonify({'unread_count': 0})

    cnt = get_total_unread_count(current_user)
    return jsonify({'status': 'success', 'unread_count': cnt})


@messaging_bp.route('/recipients', methods=['GET'])
@login_required
def api_recipients():
    """JSON API endpoint returning authorized recipients for current user."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

    search_q = request.args.get('q', None)
    recipients = get_authorized_recipients(current_user, search_query=search_q)
    return jsonify({'status': 'success', 'recipients': recipients})
