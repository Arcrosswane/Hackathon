from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from app.models import (
    db, User, Guardian, Student, Employee, SchoolClass, Section,
    StudentEnrollment, School, Attendance, FeeInvoice, Payment, ExaminationResult,
    Homework, SchoolNotice, SchoolCircular, Notification, Conversation, Message,
    Setting, Subject, Timetable, Period
)
from app.utils.decorators import login_required, role_required
from app.services import (
    get_active_academic_session, get_admin_dashboard_summary,
    get_teacher_dashboard_summary, get_student_dashboard_summary,
    get_parent_dashboard_summary, get_user_display_name_and_role,
    get_authorized_recipients, get_or_create_direct_conversation,
    send_message as send_msg_service, get_user_conversations,
    get_conversation_messages, get_user_notifications,
    mark_notification_as_read, mark_all_notifications_as_read
)

# ---------------------------------------------------------
# BLUEPRINT DEFINITIONS
# ---------------------------------------------------------
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
teacher_bp = Blueprint('teacher', __name__, url_prefix='/teacher')
student_bp = Blueprint('student', __name__, url_prefix='/student')
parent_bp = Blueprint('parent', __name__, url_prefix='/parent')
settings_bp = Blueprint('settings', __name__, url_prefix='/settings')
classes_bp = Blueprint('classes', __name__, url_prefix='/classes')
school_bp = Blueprint('school', __name__, url_prefix='/school')
subjects_bp = Blueprint('subjects', __name__, url_prefix='/subjects')
employees_bp = Blueprint('employees', __name__, url_prefix='/employees')
students_bp = Blueprint('students', __name__, url_prefix='/students')
guardians_bp = Blueprint('guardians', __name__, url_prefix='/guardians')
timetables_bp = Blueprint('timetables', __name__, url_prefix='/timetables')
fees_bp = Blueprint('fees', __name__, url_prefix='/fees')
accounts_bp = Blueprint('accounts', __name__, url_prefix='/accounts')
payroll_bp = Blueprint('payroll', __name__, url_prefix='/payroll')
attendance_bp = Blueprint('attendance', __name__, url_prefix='/attendance')
question_bank_bp = Blueprint('question_bank', __name__, url_prefix='/question-bank')
examination_bp = Blueprint('examination', __name__, url_prefix='/examination')
reports_bp = Blueprint('reports', __name__, url_prefix='/reports')
certificates_bp = Blueprint('certificates', __name__, url_prefix='/certificates')
notices_bp = Blueprint('notices', __name__, url_prefix='/notices')
circulars_bp = Blueprint('circulars', __name__, url_prefix='/circulars')
communication_bp = Blueprint('communication', __name__, url_prefix='/communication')
syllabus_bp = Blueprint('syllabus', __name__, url_prefix='/syllabus')
syllabus_monitoring_bp = Blueprint('syllabus_monitoring', __name__, url_prefix='/syllabus-monitoring')
ai_insights_bp = Blueprint('ai_insights', __name__, url_prefix='/admin/ai-insights')
messaging_bp = Blueprint('messaging', __name__, url_prefix='/messages')
notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')
store_bp = Blueprint('store', __name__, url_prefix='/store')
homework_bp = Blueprint('homework', __name__, url_prefix='/homework')
behaviour_skills_bp = Blueprint('behaviour_skills', __name__, url_prefix='/behaviour-skills')


# ---------------------------------------------------------
# AUTHENTICATION ROUTES
# ---------------------------------------------------------
# ---------------------------------------------------------
# AUTHENTICATION ROUTES
# ---------------------------------------------------------
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        role = str(session.get('user_role', '')).lower()
        if role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif role in ('teacher', 'employee'):
            return redirect(url_for('teacher.dashboard'))
        elif role == 'student':
            return redirect(url_for('student.dashboard'))
        elif role in ('parent', 'guardian'):
            return redirect(url_for('parent.dashboard'))
        return redirect(url_for('index'))

    if request.method == 'POST':
        data = request.get_json(silent=True) or request.form
        username_or_email = data.get('username', '').strip()
        password = data.get('password', '').strip()

        if not username_or_email or not password:
            return jsonify({'status': 'error', 'message': 'Please provide both username and password.'}), 400

        user = User.query.filter_by(username=username_or_email).first()

        if user and user.is_active and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['user_role'] = user.user_type
            session['linked_entity_id'] = user.linked_entity_id

            return jsonify({
                'status': 'success',
                'message': f'Welcome back, {user.username}!',
                'user': {'id': user.id, 'username': user.username, 'role': user.user_type}
            })
        else:
            flash('Invalid username or password.', 'error')
            return redirect(url_for('auth.login'))

    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    return jsonify({'status': 'info', 'message': 'API Sign up endpoint.'})


# ---------------------------------------------------------
# ADMIN DASHBOARD ROUTES
# ---------------------------------------------------------
@admin_bp.route('/dashboard')
@login_required
@role_required('Admin', 'admin')
def dashboard():
    summary = get_admin_dashboard_summary(school_id=1, session_id=1)
    return render_template('admin/dashboard.html', summary=summary)


# ---------------------------------------------------------
# TEACHER DASHBOARD ROUTES
# ---------------------------------------------------------
@teacher_bp.route('/dashboard')
@login_required
@role_required('teacher', 'employee')
def teacher_dashboard():
    user_id = session.get('user_id')
    summary = get_teacher_dashboard_summary(teacher_id=user_id, school_id=1, session_id=1)
    return render_template('teacher/dashboard.html', summary=summary)


# ---------------------------------------------------------
# STUDENT DASHBOARD ROUTES
# ---------------------------------------------------------
@student_bp.route('/dashboard')
@login_required
@role_required('student')
def student_dashboard():
    user_id = session.get('user_id')
    summary = get_student_dashboard_summary(student_id=user_id, school_id=1, session_id=1)
    return render_template('student/dashboard.html', summary=summary)


# ---------------------------------------------------------
# PARENT DASHBOARD ROUTES
# ---------------------------------------------------------
@parent_bp.route('/dashboard')
@login_required
@role_required('parent', 'guardian')
def parent_dashboard():
    user_id = session.get('user_id')
    summary = get_parent_dashboard_summary(parent_id=user_id, school_id=1, session_id=1)
    return render_template('parent/dashboard.html', summary=summary)


# ---------------------------------------------------------
# AI INSIGHTS ROUTES
# ---------------------------------------------------------
@ai_insights_bp.route('')
@ai_insights_bp.route('/')
@login_required
@role_required('Admin', 'admin')
def ai_insights_index():
    user_id = session.get('user_id')
    u = User.query.get(user_id)
    school_id = u.school_id if (u and hasattr(u, 'school_id') and u.school_id) else 1
    
    from app.services.ai_copilot_service import generate_ai_school_insights
    insights = generate_ai_school_insights(school_id=school_id, session_id=1)
    return jsonify({'status': 'success', 'data': insights})

@ai_insights_bp.route('/ask', methods=['POST'])
@login_required
@role_required('Admin', 'admin')
def ai_insights_ask():
    data = request.get_json() or {}
    question = data.get('question', '').strip()
    
    user_id = session.get('user_id')
    u = User.query.get(user_id)
    school_id = u.school_id if (u and hasattr(u, 'school_id') and u.school_id) else 1

    from app.services.ai_copilot_service import generate_ai_school_insights
    insights = generate_ai_school_insights(school_id=school_id, session_id=1, user_question=question)
    return jsonify({'status': 'success', 'data': insights})


# ---------------------------------------------------------
# MESSAGING & NOTIFICATION ROUTES
# ---------------------------------------------------------
@messaging_bp.route('/center')
@login_required
def messaging_center():
    user_id = session.get('user_id')
    convs = get_user_conversations(user_id)
    return jsonify({'status': 'success', 'conversations': [c.id for c in convs]})

@messaging_bp.route('/api/conversations/direct', methods=['POST'])
@login_required
def create_direct_conv():
    data = request.get_json() or {}
    target_id = data.get('recipient_user_id') or data.get('user_id')
    user_id = session.get('user_id')
    if not target_id:
        return jsonify({'status': 'error', 'message': 'Target user required'}), 400
    conv = get_or_create_direct_conversation(user_id, target_id)
    return jsonify({'status': 'success', 'conversation_id': conv.id})

@notifications_bp.route('/center')
@login_required
def notification_center():
    user_id = session.get('user_id')
    notifs = get_user_notifications(user_id)
    return jsonify({'status': 'success', 'notifications': [{'id': n.id, 'title': n.title, 'message': n.message} for n in notifs]})
