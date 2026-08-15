from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import db, Subject, SubjectClass, SchoolClass, AcademicSession
from app.utils.decorators import login_required, role_required
from app.services.academic_service import get_active_academic_session
from app.services.class_service import get_classes_for_session
from app.services.subject_service import (
    get_all_subjects,
    get_subject_by_id,
    create_subject,
    update_subject,
    get_subjects_for_class,
    get_classes_for_subject,
    assign_subject_to_class,
    remove_subject_from_class
)

subjects_bp = Blueprint('subjects', __name__, url_prefix='/admin/academics/subjects')

SUBJECT_TYPES = [
    ('core', 'Core Subject'),
    ('elective', 'Elective Subject'),
    ('optional', 'Optional Subject'),
    ('co_curricular', 'Co-Curricular')
]

@subjects_bp.route('/', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def index():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        code = request.form.get('code', '').strip()
        short_name = request.form.get('short_name', '').strip()
        subject_type = request.form.get('subject_type', 'core').strip()
        description = request.form.get('description', '').strip()

        if not name:
            flash('Subject name is required.', 'danger')
        elif len(name) > 100:
            flash('Subject name must be under 100 characters.', 'danger')
        else:
            try:
                sub = create_subject(
                    name=name,
                    code=code,
                    short_name=short_name,
                    subject_type=subject_type,
                    description=description
                )
                flash(f'Subject "{sub.name}" ({sub.code or "No Code"}) created successfully!', 'success')
                return redirect(url_for('subjects.index'))
            except ValueError as ve:
                flash(str(ve), 'danger')
            except Exception as e:
                flash(f'Failed to create subject: {str(e)}', 'danger')

    # Filtering parameters
    search_q = request.args.get('q', '').strip()
    type_filter = request.args.get('type', '').strip()
    status_filter = request.args.get('status', '').strip()

    query = Subject.query
    if search_q:
        query = query.filter(
            (Subject.name.ilike(f'%{search_q}%')) | 
            (Subject.code.ilike(f'%{search_q}%')) |
            (Subject.short_name.ilike(f'%{search_q}%'))
        )
    if type_filter:
        query = query.filter_by(subject_type=type_filter)
    if status_filter == 'active':
        query = query.filter_by(is_active=True)
    elif status_filter == 'inactive':
        query = query.filter_by(is_active=False)

    subjects_list = query.order_by(Subject.name.asc()).all()

    # Pre-fetch assigned classes count per subject
    classes_map = {}
    for sub in subjects_list:
        classes_map[sub.id] = get_classes_for_subject(sub.id, active_only=False)

    return render_template(
        'subjects/index.html',
        subjects_list=subjects_list,
        classes_map=classes_map,
        subject_types=SUBJECT_TYPES,
        search_q=search_q,
        type_filter=type_filter,
        status_filter=status_filter
    )


@subjects_bp.route('/<int:subject_id>/edit', methods=['POST'])
@login_required
@role_required('admin')
def edit_subject(subject_id):
    subject = get_subject_by_id(subject_id)
    if not subject:
        flash('Subject not found.', 'danger')
        return redirect(url_for('subjects.index'))

    name = request.form.get('name', '').strip()
    code = request.form.get('code', '').strip()
    short_name = request.form.get('short_name', '').strip()
    subject_type = request.form.get('subject_type', 'core').strip()
    description = request.form.get('description', '').strip()

    if not name:
        flash('Subject name is required.', 'danger')
        return redirect(url_for('subjects.index'))

    try:
        update_subject(
            subject_id=subject.id,
            name=name,
            code=code,
            short_name=short_name,
            subject_type=subject_type,
            description=description
        )
        flash(f'Subject "{name}" updated successfully!', 'success')
    except ValueError as ve:
        flash(str(ve), 'danger')
    except Exception as e:
        flash(f'Failed to update subject: {str(e)}', 'danger')

    return redirect(url_for('subjects.index'))


@subjects_bp.route('/<int:subject_id>/toggle-status', methods=['POST'])
@login_required
@role_required('admin')
def toggle_status(subject_id):
    subject = get_subject_by_id(subject_id)
    if not subject:
        flash('Subject not found.', 'danger')
        return redirect(url_for('subjects.index'))

    subject.is_active = not subject.is_active
    db.session.commit()
    status_str = "activated" if subject.is_active else "deactivated"
    flash(f'Subject "{subject.name}" has been {status_str}.', 'info')
    return redirect(url_for('subjects.index'))


@subjects_bp.route('/assignments', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def assignments():
    active_session = get_active_academic_session()
    sessions_list = AcademicSession.query.order_by(AcademicSession.start_date.desc()).all()

    # Selected Session ID
    selected_session_id = request.args.get('session_id', type=int)
    if not selected_session_id and active_session:
        selected_session_id = active_session.id
    elif not selected_session_id and sessions_list:
        selected_session_id = sessions_list[0].id

    # Available classes for selected session
    classes_list = get_classes_for_session(selected_session_id) if selected_session_id else []

    # Selected Class ID
    selected_class_id = request.args.get('class_id', type=int)
    if not selected_class_id and classes_list:
        selected_class_id = classes_list[0].id

    selected_class = SchoolClass.query.get(selected_class_id) if selected_class_id else None

    # Handle Mass Assignment Update POST
    if request.method == 'POST':
        target_class_id = request.form.get('class_id', type=int)
        if not target_class_id:
            flash('Target class is required for assignment.', 'danger')
            return redirect(url_for('subjects.assignments', session_id=selected_session_id))

        target_class = SchoolClass.query.get(target_class_id)
        if not target_class:
            flash('Target class does not exist.', 'danger')
            return redirect(url_for('subjects.assignments', session_id=selected_session_id))

        # Selected subject IDs from checkboxes
        selected_subject_ids = [int(sid) for sid in request.form.getlist('subject_ids')]

        # Current assignments for this class
        existing_assignments = SubjectClass.query.filter_by(class_id=target_class_id).all()
        existing_subject_ids = {a.subject_id for a in existing_assignments}

        # Add new assignments
        added_count = 0
        for sid in selected_subject_ids:
            if sid not in existing_subject_ids:
                try:
                    assign_subject_to_class(sid, target_class_id)
                    added_count += 1
                except Exception as e:
                    flash(f'Notice: {str(e)}', 'warning')

        # Remove unchecked assignments
        removed_count = 0
        for a in existing_assignments:
            if a.subject_id not in selected_subject_ids:
                remove_subject_from_class(a.subject_id, target_class_id)
                removed_count += 1

        flash(f'Subject assignments updated for {target_class.display_name}! ({added_count} added, {removed_count} removed)', 'success')
        return redirect(url_for('subjects.assignments', session_id=selected_session_id, class_id=target_class_id))

    # All available subjects
    all_subjects = get_all_subjects(active_only=False)

    # Currently assigned subject IDs for selected class
    assigned_subject_ids = set()
    if selected_class:
        assigned_subs = get_subjects_for_class(selected_class.id, active_only=False)
        assigned_subject_ids = {s.id for s in assigned_subs}

    return render_template(
        'subjects/assignments.html',
        sessions_list=sessions_list,
        selected_session_id=selected_session_id,
        classes_list=classes_list,
        selected_class_id=selected_class_id,
        selected_class=selected_class,
        all_subjects=all_subjects,
        assigned_subject_ids=assigned_subject_ids
    )


@subjects_bp.route('/<int:subject_id>/unassign-class/<int:class_id>', methods=['POST'])
@login_required
@role_required('admin')
def unassign_class(subject_id, class_id):
    success = remove_subject_from_class(subject_id, class_id)
    if success:
        flash('Subject unassigned from class successfully.', 'info')
    else:
        flash('Assignment not found.', 'danger')
    return redirect(request.referrer or url_for('subjects.index'))
