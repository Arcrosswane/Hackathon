import os
import uuid
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from werkzeug.utils import secure_filename
from app.models import db, Student, StudentEnrollment, SchoolClass, Section, AcademicSession, User, School
from app.utils.decorators import login_required, role_required
from app.services.academic_service import get_active_academic_session
from app.services.class_service import get_classes_for_session, get_sections_for_class
from app.services.subject_service import get_subjects_for_class
from app.services.student_service import (
    get_all_students,
    get_student_by_id,
    get_current_enrollment,
    get_student_enrollments,
    create_student,
    update_student,
    transfer_student,
    toggle_student_status,
    STUDENT_STATUSES,
    GUARDIAN_RELATIONS
)

students_bp = Blueprint('students', __name__, url_prefix='/admin/students')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_student_photo(file):
    if not file or file.filename == '':
        return None
    if not allowed_file(file.filename):
        raise ValueError("Invalid photo format. Only JPG, PNG, and WEBP files are allowed.")

    filename = secure_filename(file.filename)
    unique_filename = f"stu_{uuid.uuid4().hex[:10]}_{filename}"
    
    upload_dir = os.path.join(current_app.static_folder, 'uploads', 'students')
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, unique_filename)
    file.save(file_path)
    return f"uploads/students/{unique_filename}"


@students_bp.route('/', methods=['GET'])
@login_required
@role_required('admin')
def index():
    active_session = get_active_academic_session()
    sessions_list = AcademicSession.query.order_by(AcademicSession.start_date.desc()).all()

    search_q = request.args.get('q', '').strip()
    session_filter = request.args.get('session_id', type=int)
    class_filter = request.args.get('class_id', type=int)
    section_filter = request.args.get('section_id', type=int)
    status_filter = request.args.get('status', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 12

    if not session_filter and active_session:
        session_filter = active_session.id

    classes_list = get_classes_for_session(session_filter) if session_filter else []
    sections_list = get_sections_for_class(class_filter) if class_filter else []

    query = Student.query
    if search_q:
        sq = f"%{search_q}%"
        query = query.filter(
            (Student.full_name.ilike(sq)) |
            (Student.registration_number.ilike(sq)) |
            (Student.email_address.ilike(sq)) |
            (Student.mobile_phone_number.ilike(sq)) |
            (Student.guardian_name.ilike(sq))
        )
    if status_filter:
        query = query.filter_by(status=status_filter)

    if session_filter or class_filter or section_filter:
        query = query.join(StudentEnrollment, (Student.id == StudentEnrollment.student_id) & (StudentEnrollment.is_current == True))
        if session_filter:
            query = query.filter(StudentEnrollment.academic_session_id == session_filter)
        if class_filter:
            query = query.filter(StudentEnrollment.class_id == class_filter)
        if section_filter:
            query = query.filter(StudentEnrollment.section_id == section_filter)

    pagination = query.order_by(Student.full_name.asc()).paginate(page=page, per_page=per_page, error_out=False)
    students_list = pagination.items

    # Map student portal accounts for display
    student_ids = [s.id for s in students_list]
    student_users = User.query.filter(
        (User.linked_entity_id.in_(student_ids)) & (User.user_type == 'Student')
    ).all() if student_ids else []
    
    user_map = {u.linked_entity_id: u for u in student_users}

    return render_template(
        'students/index.html',
        students_list=students_list,
        user_map=user_map,
        pagination=pagination,
        sessions_list=sessions_list,
        selected_session_id=session_filter,
        classes_list=classes_list,
        selected_class_id=class_filter,
        sections_list=sections_list,
        selected_section_id=section_filter,
        statuses=STUDENT_STATUSES,
        search_q=search_q,
        status_filter=status_filter
    )


@students_bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def create():
    active_session = get_active_academic_session()
    sessions_list = AcademicSession.query.order_by(AcademicSession.start_date.desc()).all()

    if request.method == 'POST':
        session_id = request.form.get('session_id', type=int)
        class_id = request.form.get('class_id', type=int)
        section_id = request.form.get('section_id', type=int)
        registration_number = request.form.get('registration_number', '').strip()
        first_name = request.form.get('first_name', '').strip()
        middle_name = request.form.get('middle_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        gender = request.form.get('gender', '').strip()
        dob_str = request.form.get('date_of_birth', '').strip()
        adm_date_str = request.form.get('admission_date', '').strip()
        roll_number = request.form.get('roll_number', type=int)
        
        email_address = request.form.get('email_address', '').strip()
        mobile_phone_number = request.form.get('mobile_phone_number', '').strip()
        home_address = request.form.get('home_address', '').strip()
        city = request.form.get('city', '').strip()
        state = request.form.get('state', '').strip()
        country = request.form.get('country', 'India').strip()
        postal_code = request.form.get('postal_code', '').strip()

        guardian_name = request.form.get('guardian_name', '').strip()
        guardian_relation = request.form.get('guardian_relation', '').strip()
        guardian_phone = request.form.get('guardian_phone', '').strip()
        guardian_email = request.form.get('guardian_email', '').strip()
        guardian_occupation = request.form.get('guardian_occupation', '').strip()

        photo_file = request.files.get('profile_photo')

        try:
            date_of_birth = datetime.strptime(dob_str, '%Y-%m-%d').date() if dob_str else None
            admission_date = datetime.strptime(adm_date_str, '%Y-%m-%d').date() if adm_date_str else datetime.utcnow().date()
            profile_photo_path = save_student_photo(photo_file) if photo_file else None

            stu = create_student(
                session_id=session_id or (active_session.id if active_session else None),
                class_id=class_id,
                section_id=section_id if section_id else None,
                registration_number=registration_number,
                first_name=first_name,
                middle_name=middle_name,
                last_name=last_name,
                gender=gender,
                date_of_birth=date_of_birth,
                admission_date=admission_date,
                roll_number=roll_number,
                email_address=email_address,
                mobile_phone_number=mobile_phone_number,
                home_address=home_address,
                city=city,
                state=state,
                country=country,
                postal_code=postal_code,
                guardian_name=guardian_name,
                guardian_relation=guardian_relation,
                guardian_phone=guardian_phone,
                guardian_email=guardian_email,
                guardian_occupation=guardian_occupation,
                profile_photo=profile_photo_path
            )
            flash(f'Student "{stu.full_name}" ({stu.registration_number}) admitted successfully!', 'success')
            return redirect(url_for('students.profile', student_id=stu.id))
        except ValueError as ve:
            flash(str(ve), 'danger')
        except Exception as e:
            flash(f'Failed to register student: {str(e)}', 'danger')

    return render_template('students/form.html', is_edit=False, sessions_list=sessions_list, active_session=active_session, guardian_relations=GUARDIAN_RELATIONS)


@students_bp.route('/<int:student_id>', methods=['GET'])
@login_required
@role_required('admin')
def profile(student_id):
    student = get_student_by_id(student_id)
    if not student:
        flash('Student record not found.', 'danger')
        return redirect(url_for('students.index'))

    current_enrollment = get_current_enrollment(student.id)
    enrollments_history = get_student_enrollments(student.id)
    
    # Class subjects available for current placement
    class_subjects = get_subjects_for_class(current_enrollment.class_id) if current_enrollment else []

    # Linked user login account
    linked_user = User.query.filter_by(linked_entity_id=student.id, user_type='Student').first()
    if not linked_user:
        linked_user = User.query.filter_by(username=student.registration_number).first()

    return render_template(
        'students/profile.html',
        student=student,
        current_enrollment=current_enrollment,
        enrollments_history=enrollments_history,
        class_subjects=class_subjects,
        linked_user=linked_user
    )


@students_bp.route('/<int:student_id>/create-credentials', methods=['POST'])
@login_required
@role_required('admin')
def create_credentials(student_id):
    """Admin route to create or reset student portal credentials."""
    student = get_student_by_id(student_id)
    if not student:
        flash('Student record not found.', 'danger')
        return redirect(url_for('students.index'))

    username = request.form.get('username', '').strip() or f"stu_{student.registration_number.lower()}"
    password = request.form.get('password', '').strip() or "Student@123"

    user = User.query.filter_by(linked_entity_id=student.id, user_type='Student').first()
    if not user:
        user = User.query.filter_by(username=username).first()

    if user:
        user.username = username
        user.set_password(password)
        user.linked_entity_id = student.id
        user.user_type = 'Student'
        user.is_active = True
        flash(f'Portal credentials updated for {student.full_name}! Username: "{username}", Password: "{password}"', 'success')
    else:
        school = School.query.first()
        user = User(
            username=username,
            user_type='Student',
            school_id=school.id if school else None,
            linked_entity_id=student.id,
            is_active=True
        )
        user.set_password(password)
        db.session.add(user)
        flash(f'Portal account created for {student.full_name}! Username: "{username}", Password: "{password}"', 'success')

    db.session.commit()
    return redirect(request.referrer or url_for('students.profile', student_id=student.id))


@students_bp.route('/<int:student_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit(student_id):
    student = get_student_by_id(student_id)
    if not student:
        flash('Student record not found.', 'danger')
        return redirect(url_for('students.index'))

    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        middle_name = request.form.get('middle_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        gender = request.form.get('gender', '').strip()
        dob_str = request.form.get('date_of_birth', '').strip()
        adm_date_str = request.form.get('admission_date', '').strip()
        status = request.form.get('status', 'Active').strip()
        
        email_address = request.form.get('email_address', '').strip()
        mobile_phone_number = request.form.get('mobile_phone_number', '').strip()
        home_address = request.form.get('home_address', '').strip()
        city = request.form.get('city', '').strip()
        state = request.form.get('state', '').strip()
        country = request.form.get('country', 'India').strip()
        postal_code = request.form.get('postal_code', '').strip()

        guardian_name = request.form.get('guardian_name', '').strip()
        guardian_relation = request.form.get('guardian_relation', '').strip()
        guardian_phone = request.form.get('guardian_phone', '').strip()
        guardian_email = request.form.get('guardian_email', '').strip()
        guardian_occupation = request.form.get('guardian_occupation', '').strip()

        photo_file = request.files.get('profile_photo')

        try:
            date_of_birth = datetime.strptime(dob_str, '%Y-%m-%d').date() if dob_str else student.date_of_birth
            admission_date = datetime.strptime(adm_date_str, '%Y-%m-%d').date() if adm_date_str else student.admission_date
            profile_photo_path = save_student_photo(photo_file) if photo_file else student.profile_photo

            update_student(
                student_id=student.id,
                first_name=first_name,
                middle_name=middle_name,
                last_name=last_name,
                gender=gender,
                date_of_birth=date_of_birth,
                admission_date=admission_date,
                status=status,
                email_address=email_address,
                mobile_phone_number=mobile_phone_number,
                home_address=home_address,
                city=city,
                state=state,
                country=country,
                postal_code=postal_code,
                guardian_name=guardian_name,
                guardian_relation=guardian_relation,
                guardian_phone=guardian_phone,
                guardian_email=guardian_email,
                guardian_occupation=guardian_occupation,
                profile_photo=profile_photo_path
            )
            flash(f'Student "{student.full_name}" details updated successfully!', 'success')
            return redirect(url_for('students.profile', student_id=student.id))
        except ValueError as ve:
            flash(str(ve), 'danger')
        except Exception as e:
            flash(f'Failed to update student: {str(e)}', 'danger')

    active_session = get_active_academic_session()
    sessions_list = AcademicSession.query.order_by(AcademicSession.start_date.desc()).all()
    return render_template('students/form.html', is_edit=True, student=student, sessions_list=sessions_list, active_session=active_session, guardian_relations=GUARDIAN_RELATIONS, statuses=STUDENT_STATUSES)


@students_bp.route('/<int:student_id>/transfer', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def transfer(student_id):
    student = get_student_by_id(student_id)
    if not student:
        flash('Student record not found.', 'danger')
        return redirect(url_for('students.index'))

    active_session = get_active_academic_session()
    sessions_list = AcademicSession.query.order_by(AcademicSession.start_date.desc()).all()
    current_enrollment = get_current_enrollment(student.id)

    if request.method == 'POST':
        target_session_id = request.form.get('session_id', type=int)
        target_class_id = request.form.get('class_id', type=int)
        target_section_id = request.form.get('section_id', type=int)
        roll_number = request.form.get('roll_number', type=int)

        try:
            transfer_student(
                student_id=student.id,
                target_session_id=target_session_id,
                target_class_id=target_class_id,
                target_section_id=target_section_id if target_section_id else None,
                roll_number=roll_number
            )
            flash(f'Student "{student.full_name}" placed successfully!', 'success')
            return redirect(url_for('students.profile', student_id=student.id))
        except ValueError as ve:
            flash(str(ve), 'danger')
        except Exception as e:
            flash(f'Placement failed: {str(e)}', 'danger')

    classes_list = get_classes_for_session(active_session.id) if active_session else []

    return render_template(
        'students/transfer.html',
        student=student,
        current_enrollment=current_enrollment,
        sessions_list=sessions_list,
        active_session=active_session,
        classes_list=classes_list
    )


@students_bp.route('/<int:student_id>/toggle-status', methods=['POST'])
@login_required
@role_required('admin')
def toggle_status(student_id):
    try:
        stu = toggle_student_status(student_id)
        status_str = "activated" if stu.is_active else "deactivated"
        flash(f'Student "{stu.full_name}" has been {status_str}.', 'info')
    except Exception as e:
        flash(str(e), 'danger')
    return redirect(request.referrer or url_for('students.index'))


@students_bp.route('/<int:student_id>/photo', methods=['POST'])
@login_required
@role_required('admin')
def upload_photo(student_id):
    student = get_student_by_id(student_id)
    if not student:
        flash('Student record not found.', 'danger')
        return redirect(url_for('students.index'))

    photo_file = request.files.get('profile_photo')
    if photo_file and photo_file.filename:
        try:
            path = save_student_photo(photo_file)
            student.profile_photo = path
            db.session.commit()
            flash('Profile photo updated successfully!', 'success')
        except Exception as e:
            flash(str(e), 'danger')
    else:
        flash('Please select a photo file to upload.', 'warning')

    return redirect(url_for('students.profile', student_id=student.id))


@students_bp.route('/api/classes/<int:class_id>/sections', methods=['GET'])
@login_required
def api_get_sections(class_id):
    """AJAX helper returning sections for dynamic form cascading."""
    sections = get_sections_for_class(class_id, active_only=True)
    return jsonify([{'id': s.id, 'name': s.display_name} for s in sections])
