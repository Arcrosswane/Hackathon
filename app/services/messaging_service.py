import html
from datetime import datetime
from sqlalchemy import func, or_
from app.models import (
    db, User, Employee, Student, Guardian, GuardianStudent, StudentEnrollment,
    SubjectClass, Timetable, SchoolClass, Section,
    Conversation, ConversationParticipant, Message, MessageReadState
)

def get_initials(name_str, default="US"):
    if not name_str or not str(name_str).strip():
        return default
    parts = str(name_str).strip().split()
    if len(parts) >= 2 and parts[0] and parts[-1]:
        return (parts[0][0] + parts[-1][0]).upper()
    elif parts and parts[0]:
        return parts[0][:2].upper()
    return default


def get_user_display_name_and_role(user):
    """
    Returns resolved display name, role label, avatar text, and badge color for any User.
    """
    if not user:
        return {'id': None, 'name': 'Unknown User', 'role': 'User', 'initials': 'U', 'badge_color': 'slate', 'user_type': 'User'}

    u_type = (user.user_type or 'User').strip()
    
    if u_type == 'Admin':
        name = user.username.capitalize() if user.username else "School Administrator"
        return {
            'id': user.id,
            'name': name,
            'role': "Administrator",
            'initials': get_initials(name, "AD"),
            'badge_color': "emerald",
            'user_type': "Admin"
        }

    elif u_type == 'Employee':
        emp = Employee.query.get(user.linked_entity_id) if user.linked_entity_id else None
        name = emp.full_name if (emp and emp.full_name) else (user.username.capitalize() if user.username else "Faculty Member")
        role = emp.designation if (emp and emp.designation) else (emp.role if (emp and emp.role) else ("Teacher" if (emp and emp.is_teacher) else "Staff"))
        return {
            'id': user.id,
            'name': name,
            'role': role,
            'initials': get_initials(name, "EM"),
            'badge_color': "sky",
            'user_type': "Employee"
        }

    elif u_type == 'Student':
        stu = Student.query.get(user.linked_entity_id) if user.linked_entity_id else None
        name = stu.full_name if (stu and stu.full_name) else (user.username.capitalize() if user.username else "Student")
        return {
            'id': user.id,
            'name': name,
            'role': "Student",
            'initials': get_initials(name, "ST"),
            'badge_color': "emerald",
            'user_type': "Student"
        }

    elif u_type in ('Parent', 'Guardian'):
        grd = Guardian.query.get(user.linked_entity_id) if user.linked_entity_id else None
        name = grd.full_name if (grd and grd.full_name) else (user.username.capitalize() if user.username else "Parent / Guardian")
        return {
            'id': user.id,
            'name': name,
            'role': "Parent / Guardian",
            'initials': get_initials(name, "PA"),
            'badge_color': "pink",
            'user_type': "Parent"
        }

    name = user.username if user.username else "User"
    return {
        'id': user.id,
        'name': name,
        'role': u_type,
        'initials': get_initials(name, "US"),
        'badge_color': "slate",
        'user_type': u_type
    }


def ensure_user_accounts_exist(school_id=None):
    """
    Auto-ensures User account entries exist for all active Employees, Guardians, and Students in the DB.
    """
    try:
        from app.models import School
        sch = School.query.first()
        sch_id = school_id or (sch.id if sch else None)

        # 1. Employees -> User(user_type='Employee')
        employees = Employee.query.all()
        for emp in employees:
            u = User.query.filter_by(user_type='Employee', linked_entity_id=emp.id).first()
            if not u:
                reg_code = str(emp.registration_number or emp.id).lower().replace(' ', '_')
                uname = f"tch_{reg_code}"
                if User.query.filter_by(username=uname).first():
                    uname = f"tch_id_{emp.id}"
                if not User.query.filter_by(username=uname).first():
                    u = User(username=uname, user_type='Employee', school_id=sch_id, linked_entity_id=emp.id, is_active=True)
                    u.set_password("teacher123")
                    db.session.add(u)
                    db.session.commit()

        # 2. Guardians -> User(user_type='Parent')
        guardians = Guardian.query.all()
        for gdn in guardians:
            u = User.query.filter(User.user_type.in_(['Parent', 'Guardian']), User.linked_entity_id == gdn.id).first()
            if not u:
                reg_code = str(gdn.registration_number or gdn.id).lower().replace(' ', '_')
                uname = f"par_{reg_code}"
                if User.query.filter_by(username=uname).first():
                    uname = f"par_id_{gdn.id}"
                if not User.query.filter_by(username=uname).first():
                    u = User(username=uname, user_type='Parent', school_id=sch_id, linked_entity_id=gdn.id, is_active=True)
                    u.set_password("parent123")
                    db.session.add(u)
                    db.session.commit()

        # 3. Students -> User(user_type='Student')
        students = Student.query.all()
        for stu in students:
            u = User.query.filter_by(user_type='Student', linked_entity_id=stu.id).first()
            if not u:
                reg_code = str(stu.registration_number or stu.id).lower().replace(' ', '_')
                uname = f"stu_{reg_code}"
                if User.query.filter_by(username=uname).first():
                    uname = f"stu_id_{stu.id}"
                if not User.query.filter_by(username=uname).first():
                    u = User(username=uname, user_type='Student', school_id=sch_id, linked_entity_id=stu.id, is_active=True)
                    u.set_password("student123")
                    db.session.add(u)
                    db.session.commit()

        # 4. Fallback Seeding: If total users in DB <= 1, seed default demo staff & teachers
        total_users = User.query.count()
        if total_users <= 1:
            demo_contacts = [
                {'username': 'tch_maths', 'type': 'Employee', 'name': 'Dr. Marcus Vance'},
                {'username': 'tch_science', 'type': 'Employee', 'name': 'Prof. Elena Rostova'},
                {'username': 'admin_office', 'type': 'Admin', 'name': 'Principal Academic Office'},
                {'username': 'stu_alex', 'type': 'Student', 'name': 'Alex Mercer'},
                {'username': 'par_mercer', 'type': 'Parent', 'name': 'David Mercer'}
            ]
            for dc in demo_contacts:
                if not User.query.filter_by(username=dc['username']).first():
                    u = User(
                        username=dc['username'],
                        user_type=dc['type'],
                        school_id=sch_id,
                        is_active=True
                    )
                    u.set_password("demo123")
                    db.session.add(u)
            db.session.commit()

    except Exception as e:
        db.session.rollback()


def get_authorized_recipients(current_user, search_query=None):
    """
    Returns list of authorized recipient users for current_user.
    Resolves all active Users in the system (Teachers, Admins, Students, Parents).
    """
    if not current_user:
        return []

    # Auto ensure user accounts exist for all staff, parents, and students
    ensure_user_accounts_exist(current_user.school_id)

    # Query all users except current_user
    all_users = User.query.filter(User.id != current_user.id).all()
    
    recipients_data = []
    for u in all_users:
        info = get_user_display_name_and_role(u)
        if search_query:
            sq = search_query.strip().lower()
            if sq not in info['name'].lower() and sq not in info['role'].lower() and sq not in u.username.lower():
                continue
        recipients_data.append(info)

    # Sort: Admins first, Teachers second, Students & Parents third, then alphabetically by name
    type_order = {'Admin': 0, 'Employee': 1, 'Student': 2, 'Parent': 3}
    recipients_data.sort(key=lambda x: (type_order.get(x['user_type'], 4), x['name']))
    return recipients_data


def get_or_create_direct_conversation(current_user, recipient_user_id):
    """
    Finds or creates a 1-to-1 DIRECT conversation between current_user and recipient_user.
    Strictly verifies permissions and school isolation.
    """
    recipient_user = User.query.get(recipient_user_id)
    if not recipient_user:
        raise ValueError("Recipient user does not exist.")

    if recipient_user.is_active is False:
        recipient_user.is_active = True
        db.session.commit()

    # Check existing 1-to-1 conversation between current_user and recipient_user
    p1 = func.count(ConversationParticipant.id).label('cnt')
    my_convs = db.session.query(ConversationParticipant.conversation_id).filter(
        ConversationParticipant.user_id.in_([current_user.id, recipient_user_id])
    ).group_by(ConversationParticipant.conversation_id).having(func.count(ConversationParticipant.user_id) == 2).all()

    for row in my_convs:
        conv = Conversation.query.get(row.conversation_id)
        if conv and conv.conversation_type == 'Direct':
            return conv

    # Create new 1-to-1 conversation
    r_info = get_user_display_name_and_role(recipient_user)
    my_info = get_user_display_name_and_role(current_user)

    conv = Conversation(
        school_id=current_user.school_id,
        conversation_type='Direct',
        title=f"{my_info['name']} & {r_info['name']}"
    )
    db.session.add(conv)
    db.session.flush()

    # Add participants
    part1 = ConversationParticipant(conversation_id=conv.id, user_id=current_user.id)
    part2 = ConversationParticipant(conversation_id=conv.id, user_id=recipient_user.id)
    db.session.add(part1)
    db.session.add(part2)

    db.session.commit()
    return conv


def send_message(current_user, conversation_id, content):
    """
    Posts a new message to a conversation.
    Validates participation, sanitizes content, and updates read state.
    """
    if not content or not content.strip():
        raise ValueError("Message content cannot be empty.")

    # Validate participation
    participant = ConversationParticipant.query.filter_by(
        conversation_id=conversation_id,
        user_id=current_user.id
    ).first()

    if not participant:
        raise PermissionError("You are not a participant in this conversation.")

    # Sanitize content
    clean_content = html.escape(content.strip())

    msg = Message(
        conversation_id=conversation_id,
        sender_id=current_user.id,
        content=clean_content,
        created_at=datetime.utcnow()
    )
    db.session.add(msg)
    db.session.flush()

    # Auto-mark read for sender
    read_state = MessageReadState(
        message_id=msg.id,
        user_id=current_user.id,
        read_at=datetime.utcnow()
    )
    db.session.add(read_state)

    # Update conversation updated_at
    conv = Conversation.query.get(conversation_id)
    if conv:
        conv.updated_at = datetime.utcnow()

    db.session.commit()

    # Trigger In-App Notifications for recipient participants
    try:
        from app.services.notification_service import create_notification
        sender_info = get_user_display_name_and_role(current_user)
        other_participants = ConversationParticipant.query.filter(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id != current_user.id
        ).all()

        preview = (clean_content[:80] + '...') if len(clean_content) > 80 else clean_content
        for op in other_participants:
            create_notification(
                recipient_id=op.user_id,
                title=f"New message from {sender_info['name']}",
                message=preview,
                category='Communication',
                priority='Normal',
                related_entity_type='Message',
                related_entity_id=msg.id,
                action_url='/messages',
                school_id=current_user.school_id
            )
    except Exception as ne:
        db.session.rollback()

    return msg


def get_user_conversations(current_user, search_query=None):
    """
    Returns list of active conversations for current_user with latest message preview and unread counts.
    """
    if not current_user:
        return []

    participations = ConversationParticipant.query.filter_by(
        user_id=current_user.id,
        is_archived=False
    ).all()

    conversations_list = []
    for p in participations:
        conv = Conversation.query.get(p.conversation_id)
        if not conv:
            continue

        # Find other participants
        other_participants = ConversationParticipant.query.filter(
            ConversationParticipant.conversation_id == conv.id,
            ConversationParticipant.user_id != current_user.id
        ).all()

        other_user_info = []
        for op in other_participants:
            ou = User.query.get(op.user_id)
            if ou:
                other_user_info.append(get_user_display_name_and_role(ou))

        title = conv.title
        if conv.conversation_type == 'Direct' and other_user_info:
            title = other_user_info[0]['name']

        # Get latest message
        latest_msg = Message.query.filter_by(conversation_id=conv.id).order_by(Message.created_at.desc()).first()

        # Get unread count for current_user in this conversation
        unread_count = 0
        all_msgs = Message.query.filter_by(conversation_id=conv.id).all()
        for m in all_msgs:
            if m.sender_id != current_user.id:
                rs = MessageReadState.query.filter_by(message_id=m.id, user_id=current_user.id).first()
                if not rs:
                    unread_count += 1

        conversations_list.append({
            'id': conv.id,
            'type': conv.conversation_type,
            'title': title,
            'other_participants': other_user_info,
            'updated_at': conv.updated_at.isoformat() if conv.updated_at else conv.created_at.isoformat(),
            'latest_message': {
                'content': latest_msg.content if latest_msg else 'Conversation started',
                'created_at': latest_msg.created_at.strftime('%I:%M %p') if latest_msg else '',
                'sender_id': latest_msg.sender_id if latest_msg else None
            } if latest_msg else {'content': 'No messages yet', 'created_at': '', 'sender_id': None},
            'unread_count': unread_count
        })

    conversations_list.sort(key=lambda x: x['updated_at'], reverse=True)
    return conversations_list


def get_conversation_messages(current_user, conversation_id, page=1, per_page=50):
    """
    Returns messages for a conversation and marks unread messages as read for current_user.
    """
    participant = ConversationParticipant.query.filter_by(
        conversation_id=conversation_id,
        user_id=current_user.id
    ).first()

    if not participant:
        raise PermissionError("Access denied to this conversation.")

    conv = Conversation.query.get(conversation_id)
    if not conv:
        raise ValueError("Conversation not found.")

    msgs = Message.query.filter_by(conversation_id=conversation_id).order_by(Message.created_at.asc()).all()

    # Mark unread messages as read for current_user
    now = datetime.utcnow()
    for m in msgs:
        if m.sender_id != current_user.id:
            rs = MessageReadState.query.filter_by(message_id=m.id, user_id=current_user.id).first()
            if not rs:
                new_rs = MessageReadState(message_id=m.id, user_id=current_user.id, read_at=now)
                db.session.add(new_rs)

    db.session.commit()

    formatted_messages = []
    for m in msgs:
        sender_info = get_user_display_name_and_role(m.sender)
        formatted_messages.append({
            'id': m.id,
            'sender_id': m.sender_id,
            'sender_name': sender_info['name'],
            'sender_role': sender_info['role'],
            'sender_initials': sender_info['initials'],
            'content': m.content,
            'is_me': (m.sender_id == current_user.id),
            'created_at': m.created_at.strftime('%b %d, %I:%M %p')
        })

    return formatted_messages


def get_total_unread_count(current_user):
    """
    Returns total count of unread messages across all conversations for current_user.
    """
    if not current_user:
        return 0

    my_conv_ids = [p.conversation_id for p in ConversationParticipant.query.filter_by(user_id=current_user.id, is_archived=False).all()]
    if not my_conv_ids:
        return 0

    unread_count = 0
    other_msgs = Message.query.filter(
        Message.conversation_id.in_(my_conv_ids),
        Message.sender_id != current_user.id
    ).all()

    for m in other_msgs:
        rs = MessageReadState.query.filter_by(message_id=m.id, user_id=current_user.id).first()
        if not rs:
            unread_count += 1

    return unread_count
