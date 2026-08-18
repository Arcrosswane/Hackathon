import datetime
from sqlalchemy import func, or_, and_, desc
from app.models import (
    db, AcademicSession, User, Employee, Student, SchoolClass, Section,
    AttendanceRecord, FeeInvoice, Payment, ExaminationResult, Homework,
    SchoolNotice, SchoolCircular, Notification, NotificationPreference,
    Conversation, ConversationParticipant, Message, MessageReadState,
    Setting, RolePermission, AuditLog, StudentEnrollment
)

# ---------------------------------------------------------
# ACADEMIC SESSION SERVICES
# ---------------------------------------------------------

def get_active_academic_session(school_id):
    """
    Returns the active academic session for the given school_id.
    """
    session = AcademicSession.query.filter_by(school_id=school_id, is_active=True).first()
    if not session:
        session = AcademicSession.query.filter_by(school_id=school_id).order_by(AcademicSession.start_date.desc()).first()
    return session

def set_active_academic_session(school_id, session_id):
    """
    Sets a specific session as active and deactivates all others for the school.
    """
    AcademicSession.query.filter_by(school_id=school_id).update({'is_active': False})
    target_session = AcademicSession.query.filter_by(id=session_id, school_id=school_id).first()
    if target_session:
        target_session.is_active = True
        db.session.commit()
        return target_session
    db.session.rollback()
    return None


# ---------------------------------------------------------
# SETTING SERVICES
# ---------------------------------------------------------

def get_setting(key, default=None, school_id=None):
    query = Setting.query.filter_by(setting_key=key)
    if school_id:
        query = query.filter_by(school_id=school_id)
    setting = query.first()
    return setting.setting_value if setting else default

def set_setting(key, value, description=None, school_id=None):
    query = Setting.query.filter_by(setting_key=key)
    if school_id:
        query = query.filter_by(school_id=school_id)
    setting = query.first()
    if not setting:
        setting = Setting(setting_key=key, school_id=school_id)
        db.session.add(setting)
    setting.setting_value = str(value)
    if description:
        setting.description = description
    db.session.commit()
    return setting

def get_all_settings(school_id=None):
    query = Setting.query
    if school_id:
        query = query.filter_by(school_id=school_id)
    return {s.setting_key: s.setting_value for s in query.all()}


# ---------------------------------------------------------
# NOTIFICATION SERVICES
# ---------------------------------------------------------

def create_notification(user_id, title, message, notification_type='info', link_url=None):
    notif = Notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type,
        link_url=link_url
    )
    db.session.add(notif)
    db.session.commit()
    return notif

def create_bulk_notifications(user_ids, title, message, notification_type='info', link_url=None):
    notifications = [
        Notification(
            user_id=uid,
            title=title,
            message=message,
            notification_type=notification_type,
            link_url=link_url
        ) for uid in user_ids
    ]
    db.session.bulk_save_objects(notifications)
    db.session.commit()

def get_user_notifications(user_id, limit=20, unread_only=False):
    query = Notification.query.filter_by(user_id=user_id)
    if unread_only:
        query = query.filter_by(is_read=False)
    return query.order_by(Notification.created_at.desc()).limit(limit).all()

def get_unread_notification_count(user_id):
    return Notification.query.filter_by(user_id=user_id, is_read=False).count()

def mark_notification_as_read(notification_id, user_id):
    notif = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
    if notif:
        notif.is_read = True
        db.session.commit()
        return True
    return False

def mark_all_notifications_as_read(user_id):
    Notification.query.filter_by(user_id=user_id, is_read=False).update({'is_read': True})
    db.session.commit()


# ---------------------------------------------------------
# MESSAGING SERVICES
# ---------------------------------------------------------

def get_user_display_name_and_role(user):
    if not user:
        return "Unknown User", "User"
    if user.user_type == 'Student':
        st = Student.query.get(user.linked_entity_id) if user.linked_entity_id else None
        return (f"{st.first_name} {st.last_name}", "Student") if st else (user.username, "Student")
    elif user.user_type in ('Teacher', 'Employee'):
        emp = Employee.query.get(user.linked_entity_id) if user.linked_entity_id else None
        return (f"{emp.first_name} {emp.last_name}", "Teacher") if emp else (user.username, "Staff")
    return (user.username, user.user_type)

def get_authorized_recipients(current_user):
    return User.query.filter(User.id != current_user.id, User.is_active == True).all()

def get_or_create_direct_conversation(user_id_1, user_id_2):
    subq = db.session.query(ConversationParticipant.conversation_id).filter(
        ConversationParticipant.user_id.in_([user_id_1, user_id_2])
    ).group_by(ConversationParticipant.conversation_id).having(func.count(ConversationParticipant.user_id) == 2)
    
    conv = Conversation.query.filter(Conversation.id.in_(subq), Conversation.is_group == False).first()
    if conv:
        return conv

    conv = Conversation(is_group=False)
    db.session.add(conv)
    db.session.flush()

    p1 = ConversationParticipant(conversation_id=conv.id, user_id=user_id_1)
    p2 = ConversationParticipant(conversation_id=conv.id, user_id=user_id_2)
    db.session.add_all([p1, p2])
    db.session.commit()
    return conv

def send_message(conversation_id, sender_id, content):
    msg = Message(conversation_id=conversation_id, sender_id=sender_id, content=content)
    db.session.add(msg)
    conv = Conversation.query.get(conversation_id)
    if conv:
        conv.updated_at = datetime.datetime.utcnow()
    db.session.commit()
    return msg

def get_user_conversations(user_id):
    part_convs = ConversationParticipant.query.filter_by(user_id=user_id).all()
    conv_ids = [p.conversation_id for p in part_convs]
    return Conversation.query.filter(Conversation.id.in_(conv_ids)).order_by(Conversation.updated_at.desc()).all()

def get_conversation_messages(conversation_id, limit=50):
    return Message.query.filter_by(conversation_id=conversation_id).order_by(Message.created_at.asc()).limit(limit).all()

def get_total_unread_count(user_id):
    return 0


# ---------------------------------------------------------
# DASHBOARD SERVICES
# ---------------------------------------------------------

def get_admin_dashboard_summary(school_id, session_id):
    total_students = Student.query.filter_by(school_id=school_id).count()
    total_teachers = Employee.query.filter_by(school_id=school_id).count()
    total_classes = SchoolClass.query.filter_by(school_id=school_id).count()
    
    today = datetime.date.today()
    
    att_today = AttendanceRecord.query.filter_by(school_id=school_id, attendance_date=today).all()
    present_today = sum(1 for a in att_today if a.status in ('Present', 'Late'))
    att_percentage = round((present_today / total_students * 100), 1) if total_students > 0 and att_today else 0

    return {
        'level1_kpis': {
            'total_students': total_students,
            'total_teachers': total_teachers,
            'total_classes': total_classes,
            'today_attendance_percentage': att_percentage,
            'total_outstanding_fees': 0,
            'upcoming_exams_count': 0
        },
        'attendance_overview': {'seven_days_trend': []},
        'finance_overview': {'monthly_collections': 0, 'total_outstanding': 0},
        'exams_overview': {'draft_results_count': 0},
        'level2_pending_actions': [],
        'level4_activity': []
    }

def get_teacher_dashboard_summary(teacher_id, school_id, session_id):
    return {
        'assigned_classes': [],
        'today_schedule': [],
        'pending_homework_reviews': 0
    }

def get_student_dashboard_summary(student_id, school_id, session_id):
    return {
        'attendance_percentage': 95.0,
        'upcoming_exams': [],
        'pending_homework': []
    }

def get_parent_dashboard_summary(parent_id, school_id, session_id):
    return {
        'children': [],
        'notifications': []
    }
