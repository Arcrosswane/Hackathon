from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.models import db, Guardian, GuardianStudent, Student, User
from app.utils.decorators import login_required, role_required
from app.services.guardian_service import (
    get_all_guardians,
    get_guardian_by_id,
    create_guardian,
    update_guardian,
    link_guardian_student,
    unlink_guardian_student,
    toggle_guardian_status,
    RELATIONSHIP_TYPES
)

guardians_bp = Blueprint('guardians', __name__, url_prefix='/admin/guardians')


@guardians_bp.route('/', methods=['GET'])
@login_required
@role_required('admin')
def index():
    search_q = request.args.get('q', '').strip()
    status_filter = request.args.get('status', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 12

    query = Guardian.query
    if search_q:
        sq = f"%{search_q}%"
        query = query.outerjoin(GuardianStudent, Guardian.id == GuardianStudent.guardian_id)\
                     .outerjoin(Student, GuardianStudent.student_id == Student.id)\
                     .filter(
                         (Guardian.full_name.ilike(sq)) |
                         (Guardian.registration_number.ilike(sq)) |
                         (Guardian.email_address.ilike(sq)) |
                         (Guardian.mobile_phone_number.ilike(sq)) |
                         (Student.full_name.ilike(sq)) |
                         (Student.registration_number.ilike(sq))
                     ).distinct()

    if status_filter == 'active':
        query = query.filter_by(is_active=True)
    elif status_filter == 'inactive':
        query = query.filter_by(is_active=False)

    pagination = query.order_by(Guardian.full_name.asc()).paginate(page=page, per_page=per_page, error_out=False)
    guardians_list = pagination.items

    return render_template(
        'guardians/index.html',
        guardians_list=guardians_list,
        pagination=pagination,
        search_q=search_q,
        status_filter=status_filter
    )


@guardians_bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def create():
    all_students = Student.query.filter_by(is_active=True).order_by(Student.full_name.asc()).all()

    if request.method == 'POST':
        registration_number = request.form.get('registration_number', '').strip()
        first_name = request.form.get('first_name', '').strip()
        middle_name = request.form.get('middle_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        
        email_address = request.form.get('email_address', '').strip()
        mobile_phone_number = request.form.get('mobile_phone_number', '').strip()
        alternate_phone = request.form.get('alternate_phone', '').strip()
        occupation = request.form.get('occupation', '').strip()

        home_address = request.form.get('home_address', '').strip()
        city = request.form.get('city', '').strip()
        state = request.form.get('state', '').strip()
        country = request.form.get('country', 'India').strip()
        postal_code = request.form.get('postal_code', '').strip()

        # Optional Student Link
        student_id = request.form.get('student_id', type=int)
        relationship = request.form.get('relationship', 'Father').strip()
        is_primary = request.form.get('is_primary') == 'on'
        is_emergency_contact = request.form.get('is_emergency_contact') == 'on'
        can_receive_notifications = request.form.get('can_receive_notifications') != 'off'

        if not registration_number or not first_name:
            flash('Guardian Code and First Name are required fields.', 'danger')
        else:
            try:
                gdn = create_guardian(
                    guardian_code=registration_number,
                    first_name=first_name,
                    last_name=last_name,
                    middle_name=middle_name,
                    email_address=email_address,
                    mobile_phone_number=mobile_phone_number,
                    alternate_phone=alternate_phone,
                    occupation=occupation,
                    home_address=home_address,
                    city=city,
                    state=state,
                    country=country,
                    postal_code=postal_code,
                    student_id=student_id,
                    relationship=relationship,
                    is_primary=is_primary,
                    is_emergency_contact=is_emergency_contact,
                    can_receive_notifications=can_receive_notifications
                )
                flash(f'Parent/Guardian "{gdn.full_name}" ({gdn.registration_number}) registered successfully!', 'success')
                return redirect(url_for('guardians.profile', guardian_id=gdn.id))
            except ValueError as ve:
                flash(str(ve), 'danger')
            except Exception as e:
                flash(f'Failed to register guardian: {str(e)}', 'danger')

    return render_template('guardians/form.html', is_edit=False, all_students=all_students, relationships=RELATIONSHIP_TYPES)


@guardians_bp.route('/<int:guardian_id>', methods=['GET'])
@login_required
@role_required('admin')
def profile(guardian_id):
    guardian = get_guardian_by_id(guardian_id)
    if not guardian:
        flash('Guardian record not found.', 'danger')
        return redirect(url_for('guardians.index'))

    # All active students to populate link modal
    all_students = Student.query.filter_by(is_active=True).order_by(Student.full_name.asc()).all()
    linked_user = User.query.filter_by(linked_entity_id=guardian.id, user_type='Guardian').first()

    return render_template(
        'guardians/profile.html',
        guardian=guardian,
        all_students=all_students,
        relationships=RELATIONSHIP_TYPES,
        linked_user=linked_user
    )


@guardians_bp.route('/<int:guardian_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit(guardian_id):
    guardian = get_guardian_by_id(guardian_id)
    if not guardian:
        flash('Guardian record not found.', 'danger')
        return redirect(url_for('guardians.index'))

    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        middle_name = request.form.get('middle_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        
        email_address = request.form.get('email_address', '').strip()
        mobile_phone_number = request.form.get('mobile_phone_number', '').strip()
        alternate_phone = request.form.get('alternate_phone', '').strip()
        occupation = request.form.get('occupation', '').strip()

        home_address = request.form.get('home_address', '').strip()
        city = request.form.get('city', '').strip()
        state = request.form.get('state', '').strip()
        country = request.form.get('country', 'India').strip()
        postal_code = request.form.get('postal_code', '').strip()

        if not first_name:
            flash('First Name is required.', 'danger')
        else:
            try:
                update_guardian(
                    guardian_id=guardian.id,
                    first_name=first_name,
                    last_name=last_name,
                    middle_name=middle_name,
                    email_address=email_address,
                    mobile_phone_number=mobile_phone_number,
                    alternate_phone=alternate_phone,
                    occupation=occupation,
                    home_address=home_address,
                    city=city,
                    state=state,
                    country=country,
                    postal_code=postal_code
                )
                flash(f'Guardian "{guardian.full_name}" profile updated successfully!', 'success')
                return redirect(url_for('guardians.profile', guardian_id=guardian.id))
            except ValueError as ve:
                flash(str(ve), 'danger')
            except Exception as e:
                flash(f'Failed to update guardian: {str(e)}', 'danger')

    return render_template('guardians/form.html', is_edit=True, guardian=guardian, relationships=RELATIONSHIP_TYPES)


@guardians_bp.route('/<int:guardian_id>/link-student', methods=['POST'])
@login_required
@role_required('admin')
def link_student(guardian_id):
    student_id = request.form.get('student_id', type=int)
    relationship = request.form.get('relationship', 'Father').strip()
    is_primary = request.form.get('is_primary') == 'on'
    is_emergency_contact = request.form.get('is_emergency_contact') == 'on'
    can_receive_notifications = request.form.get('can_receive_notifications') != 'off'

    if not student_id:
        flash('Please select a student to link.', 'warning')
    else:
        try:
            link = link_guardian_student(
                guardian_id=guardian_id,
                student_id=student_id,
                relationship=relationship,
                is_primary=is_primary,
                is_emergency_contact=is_emergency_contact,
                can_receive_notifications=can_receive_notifications
            )
            flash(f'Successfully linked child "{link.student.full_name}" as {relationship}!', 'success')
        except ValueError as ve:
            flash(str(ve), 'danger')
        except Exception as e:
            flash(f'Failed to link student: {str(e)}', 'danger')

    return redirect(url_for('guardians.profile', guardian_id=guardian_id))


@guardians_bp.route('/<int:guardian_id>/unlink-student/<int:student_id>', methods=['POST'])
@login_required
@role_required('admin')
def unlink_student(guardian_id, student_id):
    try:
        unlink_guardian_student(guardian_id, student_id)
        flash('Student relationship unlinked successfully. Both profiles remain intact.', 'info')
    except Exception as e:
        flash(str(e), 'danger')

    return redirect(url_for('guardians.profile', guardian_id=guardian_id))


@guardians_bp.route('/<int:guardian_id>/toggle-status', methods=['POST'])
@login_required
@role_required('admin')
def toggle_status(guardian_id):
    try:
        gdn = toggle_guardian_status(guardian_id)
        status_str = "activated" if gdn.is_active else "deactivated"
        flash(f'Guardian "{gdn.full_name}" has been {status_str}.', 'info')
    except Exception as e:
        flash(str(e), 'danger')
    return redirect(request.referrer or url_for('guardians.index'))
