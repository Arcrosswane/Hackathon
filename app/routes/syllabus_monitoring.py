from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, session, flash, redirect, url_for
from app.models import db, User, SchoolClass, Subject, Employee, SyllabusTarget, AcademicSession
from app.utils.decorators import login_required
from app.services.syllabus_checker_service import (
    create_or_update_target,
    get_school_syllabus_monitoring,
    get_teacher_detail_monitoring
)

syllabus_monitoring_bp = Blueprint('syllabus_monitoring', __name__)


@syllabus_monitoring_bp.route('/syllabus-monitoring')
@login_required
def index():
    """Renders Main Admin Syllabus Monitoring Dashboard (PAGES, NOT MODALS)."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user or (current_user.user_type or '').lower() not in ('admin', 'employee'):
        flash('Permission denied. Syllabus monitoring is restricted to Administrators.', 'danger')
        return redirect(url_for('syllabus.index'))

    sch_id = current_user.school_id or 1
    month = request.args.get('month', type=int) or datetime.utcnow().month
    year = request.args.get('year', type=int) or datetime.utcnow().year
    class_id = request.args.get('class_id', type=int)
    subject_id = request.args.get('subject_id', type=int)
    status_filter = request.args.get('status', type=str)
    search_query = request.args.get('q', type=str)

    data = get_school_syllabus_monitoring(
        school_id=sch_id,
        month=month,
        year=year,
        class_id=class_id,
        subject_id=subject_id,
        status_filter=status_filter,
        search_query=search_query
    )

    all_classes = SchoolClass.query.order_by(SchoolClass.name.asc()).all()
    all_subjects = Subject.query.order_by(Subject.name.asc()).all()

    return render_template(
        'syllabus_monitoring/index.html',
        current_user=current_user,
        items=data['items'],
        summary=data['summary'],
        selected_month=month,
        selected_year=year,
        selected_class_id=class_id,
        selected_subject_id=subject_id,
        status_filter=status_filter,
        search_query=search_query,
        all_classes=all_classes,
        all_subjects=all_subjects
    )


@syllabus_monitoring_bp.route('/syllabus-monitoring/targets')
@login_required
def targets_list():
    """Renders List of Monthly Targets."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user or (current_user.user_type or '').lower() not in ('admin', 'employee'):
        flash('Permission denied.', 'danger')
        return redirect(url_for('syllabus.index'))

    sch_id = current_user.school_id or 1
    targets = SyllabusTarget.query.filter_by(school_id=sch_id).order_by(SyllabusTarget.year.desc(), SyllabusTarget.month.desc()).all()

    return render_template(
        'syllabus_monitoring/targets_list.html',
        current_user=current_user,
        targets=targets
    )


@syllabus_monitoring_bp.route('/syllabus-monitoring/targets/create', methods=['GET', 'POST'])
@login_required
def create_target_page():
    """Dedicated Page for Creating Monthly Syllabus Targets."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user or (current_user.user_type or '').lower() not in ('admin', 'employee'):
        flash('Permission denied.', 'danger')
        return redirect(url_for('syllabus_monitoring.index'))

    sch_id = current_user.school_id or 1

    if request.method == 'POST':
        month = request.form.get('month', type=int)
        year = request.form.get('year', type=int)
        class_id = request.form.get('class_id', type=int)
        subject_id = request.form.get('subject_id', type=int)
        teacher_id = request.form.get('teacher_id', type=int)
        target_topic_count = request.form.get('target_topic_count', type=int)
        tolerance_margin = request.form.get('tolerance_margin', type=int) or 1

        if not (month and year and class_id and subject_id and teacher_id and target_topic_count):
            flash('Please fill in all required fields.', 'warning')
            return redirect(url_for('syllabus_monitoring.create_target_page'))

        create_or_update_target(
            school_id=sch_id,
            month=month,
            year=year,
            class_id=class_id,
            subject_id=subject_id,
            teacher_id=teacher_id,
            target_topic_count=target_topic_count,
            tolerance_margin=tolerance_margin,
            created_by_id=current_user.id
        )

        flash('Monthly syllabus target saved successfully!', 'success')
        return redirect(url_for('syllabus_monitoring.index'))

    classes = SchoolClass.query.order_by(SchoolClass.name.asc()).all()
    subjects = Subject.query.order_by(Subject.name.asc()).all()
    teachers = Employee.query.order_by(Employee.first_name.asc()).all()

    return render_template(
        'syllabus_monitoring/create_target.html',
        current_user=current_user,
        classes=classes,
        subjects=subjects,
        teachers=teachers,
        current_month=datetime.utcnow().month,
        current_year=datetime.utcnow().year
    )


@syllabus_monitoring_bp.route('/syllabus-monitoring/targets/<int:target_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_target_page(target_id):
    """Dedicated Page for Editing an Existing Syllabus Target."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user or (current_user.user_type or '').lower() not in ('admin', 'employee'):
        flash('Permission denied.', 'danger')
        return redirect(url_for('syllabus_monitoring.index'))

    target = SyllabusTarget.query.get_or_404(target_id)
    sch_id = current_user.school_id or 1

    if request.method == 'POST':
        target.month = request.form.get('month', type=int)
        target.year = request.form.get('year', type=int)
        target.class_id = request.form.get('class_id', type=int)
        target.subject_id = request.form.get('subject_id', type=int)
        target.teacher_id = request.form.get('teacher_id', type=int)
        target.target_topic_count = request.form.get('target_topic_count', type=int)
        target.tolerance_margin = request.form.get('tolerance_margin', type=int) or 1
        target.updated_at = datetime.utcnow()

        db.session.commit()
        flash('Monthly syllabus target updated successfully!', 'success')
        return redirect(url_for('syllabus_monitoring.targets_list'))

    classes = SchoolClass.query.order_by(SchoolClass.name.asc()).all()
    subjects = Subject.query.order_by(Subject.name.asc()).all()
    teachers = Employee.query.order_by(Employee.first_name.asc()).all()

    return render_template(
        'syllabus_monitoring/edit_target.html',
        current_user=current_user,
        target=target,
        classes=classes,
        subjects=subjects,
        teachers=teachers
    )


@syllabus_monitoring_bp.route('/syllabus-monitoring/targets/<int:target_id>/delete', methods=['POST'])
@login_required
def delete_target_submit(target_id):
    """Deletes a monthly target."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user or (current_user.user_type or '').lower() not in ('admin', 'employee'):
        flash('Permission denied.', 'danger')
        return redirect(url_for('syllabus_monitoring.index'))

    target = SyllabusTarget.query.get_or_404(target_id)
    db.session.delete(target)
    db.session.commit()
    flash('Monthly target deleted successfully.', 'info')
    return redirect(url_for('syllabus_monitoring.targets_list'))


@syllabus_monitoring_bp.route('/syllabus-monitoring/teacher/<int:teacher_id>')
@login_required
def teacher_detail(teacher_id):
    """Dedicated Teacher Detail Page displaying syllabus target vs actual comparison and full chapter/topic tree."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user:
        return redirect(url_for('auth.login'))

    user_role = (current_user.user_type or '').lower()
    sch_id = current_user.school_id or 1

    # Teacher Privacy Check: Teachers can ONLY view their own detail page
    if user_role == 'teacher' and current_user.employee_id != teacher_id:
        flash('Teacher privacy restriction: You can only view your own syllabus progress.', 'danger')
        return redirect(url_for('teacher.dashboard'))

    month = request.args.get('month', type=int) or datetime.utcnow().month
    year = request.args.get('year', type=int) or datetime.utcnow().year

    detail_data = get_teacher_detail_monitoring(sch_id, teacher_id, month=month, year=year)

    return render_template(
        'syllabus_monitoring/teacher_detail.html',
        current_user=current_user,
        teacher=detail_data['teacher'],
        targets_detail=detail_data['targets_detail'],
        selected_month=month,
        selected_year=year,
        user_role=user_role
    )


@syllabus_monitoring_bp.route('/syllabus-monitoring/behind')
@login_required
def behind_teachers():
    """Dedicated Filtered View: Teachers Behind Schedule."""
    return redirect(url_for('syllabus_monitoring.index', status='BEHIND'))


@syllabus_monitoring_bp.route('/syllabus-monitoring/on-track')
@login_required
def on_track_teachers():
    """Dedicated Filtered View: Teachers On Track."""
    return redirect(url_for('syllabus_monitoring.index', status='ON_TRACK'))


@syllabus_monitoring_bp.route('/syllabus-monitoring/ahead')
@login_required
def ahead_teachers():
    """Dedicated Filtered View: Teachers Ahead of Schedule."""
    return redirect(url_for('syllabus_monitoring.index', status='AHEAD'))


@syllabus_monitoring_bp.route('/syllabus-monitoring/reports')
@login_required
def monitoring_reports():
    """Renders Multi-Format Monitoring Reports & Export Page."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user or (current_user.user_type or '').lower() not in ('admin', 'employee'):
        flash('Permission denied.', 'danger')
        return redirect(url_for('syllabus.index'))

    sch_id = current_user.school_id or 1
    data = get_school_syllabus_monitoring(school_id=sch_id)

    return render_template(
        'syllabus_monitoring/reports.html',
        current_user=current_user,
        items=data['items'],
        summary=data['summary']
    )
