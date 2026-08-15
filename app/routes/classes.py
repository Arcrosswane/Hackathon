from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import db, AcademicSession, SchoolClass, Section
from app.utils.decorators import login_required, role_required
from app.services.academic_service import get_active_academic_session
from app.services.class_service import (
    get_classes_for_session, 
    get_class_by_id, 
    create_class, 
    create_section
)

classes_bp = Blueprint('classes', __name__, url_prefix='/admin/academics/classes')

@classes_bp.route('/', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def index():
    active_sess = get_active_academic_session()
    session_id = request.args.get('session_id', type=int)

    # Default to active session if not explicitly requested
    if not session_id and active_sess:
        session_id = active_sess.id

    selected_session = AcademicSession.query.get(session_id) if session_id else active_sess
    all_sessions = AcademicSession.query.order_by(AcademicSession.start_date.desc()).all()

    # Handle Class Creation via POST
    if request.method == 'POST':
        target_session_id = request.form.get('session_id', type=int)
        name = request.form.get('name', '').strip()
        display_name = request.form.get('display_name', '').strip()
        numeric_order = request.form.get('numeric_order', 0, type=int)
        description = request.form.get('description', '').strip()

        if not target_session_id or not name:
            flash('Academic session and class name are required.', 'danger')
        else:
            try:
                new_class = create_class(
                    session_id=target_session_id,
                    name=name,
                    display_name=display_name,
                    numeric_order=numeric_order,
                    description=description
                )
                flash(f'Class "{new_class.display_name}" created successfully!', 'success')
                return redirect(url_for('classes.index', session_id=target_session_id))
            except ValueError as ve:
                flash(str(ve), 'danger')
            except Exception as e:
                flash(f'Failed to create class: {str(e)}', 'danger')

    classes_list = get_classes_for_session(selected_session.id) if selected_session else []

    return render_template(
        'classes/index.html',
        selected_session=selected_session,
        all_sessions=all_sessions,
        classes_list=classes_list
    )


@classes_bp.route('/<int:class_id>/edit', methods=['POST'])
@login_required
@role_required('admin')
def edit_class(class_id):
    target_class = get_class_by_id(class_id)
    if not target_class:
        flash('Target class not found.', 'danger')
        return redirect(url_for('classes.index'))

    name = request.form.get('name', '').strip()
    display_name = request.form.get('display_name', '').strip()
    numeric_order = request.form.get('numeric_order', type=int)
    description = request.form.get('description', '').strip()

    if not name or not display_name:
        flash('Class name and display name are required.', 'danger')
        return redirect(url_for('classes.index', session_id=target_class.academic_session_id))

    # Check unique constraint if name changed
    if name != target_class.name:
        existing = SchoolClass.query.filter_by(
            academic_session_id=target_class.academic_session_id, 
            name=name
        ).first()
        if existing:
            flash(f'Class "{name}" already exists in this academic session.', 'danger')
            return redirect(url_for('classes.index', session_id=target_class.academic_session_id))

    target_class.name = name
    target_class.display_name = display_name
    if numeric_order is not None:
        target_class.numeric_order = numeric_order
    target_class.description = description

    db.session.commit()
    flash(f'Class "{target_class.display_name}" updated successfully!', 'success')
    return redirect(url_for('classes.index', session_id=target_class.academic_session_id))


@classes_bp.route('/<int:class_id>/toggle-status', methods=['POST'])
@login_required
@role_required('admin')
def toggle_class_status(class_id):
    target_class = get_class_by_id(class_id)
    if not target_class:
        flash('Class not found.', 'danger')
        return redirect(url_for('classes.index'))

    target_class.is_active = not target_class.is_active
    db.session.commit()
    status_str = "activated" if target_class.is_active else "deactivated"
    flash(f'Class "{target_class.display_name}" has been {status_str}.', 'info')
    return redirect(url_for('classes.index', session_id=target_class.academic_session_id))


@classes_bp.route('/<int:class_id>/sections', methods=['POST'])
@login_required
@role_required('admin')
def add_section(class_id):
    target_class = get_class_by_id(class_id)
    if not target_class:
        flash('Parent class not found.', 'danger')
        return redirect(url_for('classes.index'))

    name = request.form.get('name', '').strip()
    display_name = request.form.get('display_name', '').strip()
    capacity = request.form.get('capacity', 40, type=int)

    if not name:
        flash('Section name is required.', 'danger')
    else:
        try:
            new_section = create_section(
                class_id=target_class.id,
                name=name,
                display_name=display_name,
                capacity=capacity
            )
            flash(f'Section "{new_section.display_name}" added to {target_class.display_name}!', 'success')
        except ValueError as ve:
            flash(str(ve), 'danger')
        except Exception as e:
            flash(f'Failed to add section: {str(e)}', 'danger')

    return redirect(url_for('classes.index', session_id=target_class.academic_session_id))


@classes_bp.route('/sections/<int:section_id>/edit', methods=['POST'])
@login_required
@role_required('admin')
def edit_section(section_id):
    section = Section.query.get(section_id)
    if not section:
        flash('Section not found.', 'danger')
        return redirect(url_for('classes.index'))

    display_name = request.form.get('display_name', '').strip()
    capacity = request.form.get('capacity', type=int)

    if display_name:
        section.display_name = display_name
    if capacity is not None and capacity > 0:
        section.capacity = capacity

    db.session.commit()
    flash(f'Section "{section.display_name}" updated successfully!', 'success')
    return redirect(url_for('classes.index', session_id=section.school_class.academic_session_id))


@classes_bp.route('/sections/<int:section_id>/toggle-status', methods=['POST'])
@login_required
@role_required('admin')
def toggle_section_status(section_id):
    section = Section.query.get(section_id)
    if not section:
        flash('Section not found.', 'danger')
        return redirect(url_for('classes.index'))

    section.is_active = not section.is_active
    db.session.commit()
    status_str = "activated" if section.is_active else "deactivated"
    flash(f'Section "{section.display_name}" has been {status_str}.', 'info')
    return redirect(url_for('classes.index', session_id=section.school_class.academic_session_id))


@classes_bp.route('/<int:class_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_class(class_id):
    target_class = get_class_by_id(class_id)
    if not target_class:
        flash('Class not found.', 'danger')
        return redirect(url_for('classes.index'))

    session_id = target_class.academic_session_id
    display_name = target_class.display_name

    try:
        db.session.delete(target_class)
        db.session.commit()
        flash(f'Class "{display_name}" and all associated sections deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Failed to delete class: {str(e)}', 'danger')

    return redirect(url_for('classes.index', session_id=session_id))


@classes_bp.route('/sections/<int:section_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_section(section_id):
    section = Section.query.get(section_id)
    if not section:
        flash('Section not found.', 'danger')
        return redirect(url_for('classes.index'))

    session_id = section.school_class.academic_session_id
    display_name = section.display_name

    try:
        db.session.delete(section)
        db.session.commit()
        flash(f'Section "{display_name}" deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Failed to delete section: {str(e)}', 'danger')

    return redirect(url_for('classes.index', session_id=session_id))

