from flask import Blueprint, render_template, request, jsonify, session, flash, redirect, url_for
from app.models import db, User, SchoolClass, Subject, SyllabusChapter, SyllabusTopic
from app.utils.decorators import login_required
from app.services.syllabus_service import (
    get_teacher_assigned_classes_subjects,
    get_syllabus_chapters,
    calculate_syllabus_progress,
    update_topic_teaching_status,
    create_chapter,
    create_topic,
    delete_topic,
    quick_add_chapter_and_topic,
    get_notebook_matrix,
    update_notebook_status,
    get_admin_syllabus_overview
)
from app.utils.cbse_syllabus_seed import seed_cbse_curriculum_data

syllabus_bp = Blueprint('syllabus', __name__)


@syllabus_bp.route('/syllabus/')
@login_required
def index():
    """Renders Syllabus & Notebook Tracker Directory Workspace."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user:
        return redirect(url_for('auth.login'))

    user_role = (current_user.user_type or '').lower()
    sch_id = current_user.school_id or 1

    # Auto seed CBSE curriculum if chapters DB is empty
    if SyllabusChapter.query.count() == 0:
        seed_cbse_curriculum_data(sch_id)

    assignments = get_teacher_assigned_classes_subjects(current_user)

    # Compute progress summary for assigned pairs
    for item in assignments:
        item['progress'] = calculate_syllabus_progress(sch_id, item['class'].id, item['subject'].id)

    return render_template(
        'syllabus/index.html',
        current_user=current_user,
        assignments=assignments,
        user_role=user_role
    )


@syllabus_bp.route('/syllabus/manage', methods=['GET', 'POST'])
@login_required
def manage():
    """Renders Admin Chapter & Topic Creator/Manager Page."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user:
        return redirect(url_for('auth.login'))

    user_role = (current_user.user_type or '').lower()
    if user_role not in ('admin', 'employee'):
        flash('Permission denied to syllabus management.', 'danger')
        return redirect(url_for('syllabus.index'))

    sch_id = current_user.school_id or 1

    if request.method == 'POST':
        action = request.form.get('action', '')
        
        if action == 'create_chapter':
            class_id = request.form.get('class_id', type=int)
            subject_id = request.form.get('subject_id', type=int)
            chapter_name = request.form.get('chapter_name', '').strip()
            chapter_num = request.form.get('chapter_number', type=int)
            desc = request.form.get('description', '').strip()

            if class_id and subject_id and chapter_name:
                ch = create_chapter(sch_id, class_id, subject_id, chapter_name, chapter_num, desc)
                flash(f"Chapter '{ch.chapter_name}' created successfully!", 'success')
                return redirect(url_for('syllabus.manage', class_id=class_id, subject_id=subject_id))

        elif action == 'create_topic':
            chapter_id = request.form.get('chapter_id', type=int)
            topic_name = request.form.get('topic_name', '').strip()
            desc = request.form.get('description', '').strip()

            if chapter_id and topic_name:
                t = create_topic(sch_id, chapter_id, topic_name, desc)
                flash(f"Topic '{t.topic_name}' added to Chapter!", 'success')
                ch = SyllabusChapter.query.get(chapter_id)
                return redirect(url_for('syllabus.manage', class_id=ch.class_id, subject_id=ch.subject_id))

    class_id = request.args.get('class_id', type=int)
    subject_id = request.args.get('subject_id', type=int)

    classes = SchoolClass.query.all()
    subjects = Subject.query.all()

    if not class_id and classes:
        class_id = classes[0].id
    if not subject_id and subjects:
        subject_id = subjects[0].id

    chapters = get_syllabus_chapters(sch_id, class_id, subject_id) if (class_id and subject_id) else []

    return render_template(
        'syllabus/manage.html',
        current_user=current_user,
        classes=classes,
        subjects=subjects,
        selected_class_id=class_id,
        selected_subject_id=subject_id,
        chapters=chapters
    )


@syllabus_bp.route('/syllabus/<int:class_id>/<int:subject_id>')
@login_required
def tracker(class_id, subject_id):
    """Renders Dedicated Interactive Syllabus Tracker Page."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user:
        return redirect(url_for('auth.login'))

    sch_id = current_user.school_id or 1
    cls = SchoolClass.query.get_or_404(class_id)
    subj = Subject.query.get_or_404(subject_id)

    chapters = get_syllabus_chapters(sch_id, class_id, subject_id)
    progress = calculate_syllabus_progress(sch_id, class_id, subject_id)

    return render_template(
        'syllabus/tracker.html',
        current_user=current_user,
        school_class=cls,
        subject=subj,
        chapters=chapters,
        progress=progress
    )


@syllabus_bp.route('/syllabus/topic/<int:topic_id>/status', methods=['POST'])
@login_required
def update_topic_status(topic_id):
    """API endpoint for updating topic teaching status (Teacher only)."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

    user_role = (current_user.user_type or '').lower()
    if user_role not in ('teacher', 'employee'):
        return jsonify({'status': 'error', 'message': 'Permission denied. Syllabus teaching status can only be updated by assigned teachers.'}), 403

    sch_id = current_user.school_id or 1
    data = request.get_json() or {}
    new_status = data.get('status', 'NOT_STARTED')

    try:
        topic = update_topic_teaching_status(sch_id, topic_id, new_status, current_user.id)
        prog = calculate_syllabus_progress(sch_id, topic.chapter.class_id, topic.chapter.subject_id)
        return jsonify({
            'status': 'success',
            'topic_id': topic.id,
            'teaching_status': topic.teaching_status,
            'progress': prog
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400


@syllabus_bp.route('/notebook-tracker')
@login_required
def notebook_index():
    """Renders Notebook Correction Directory Selection Page."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user:
        return redirect(url_for('auth.login'))

    user_role = (current_user.user_type or '').lower()
    sch_id = current_user.school_id or 1

    assignments = get_teacher_assigned_classes_subjects(current_user)

    return render_template(
        'syllabus/notebook_index.html',
        current_user=current_user,
        assignments=assignments,
        user_role=user_role
    )


@syllabus_bp.route('/notebook-tracker/<int:class_id>/<int:subject_id>')
@login_required
def notebook_matrix(class_id, subject_id):
    """Renders Student x Topic Notebook Correction Grid Matrix Page."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user:
        return redirect(url_for('auth.login'))

    sch_id = current_user.school_id or 1
    cls = SchoolClass.query.get_or_404(class_id)
    subj = Subject.query.get_or_404(subject_id)

    # Auto seed CBSE data if needed
    if SyllabusChapter.query.count() == 0:
        seed_cbse_curriculum_data(sch_id)

    chapter_id = request.args.get('chapter_id', type=int)

    matrix_data = get_notebook_matrix(sch_id, class_id, subject_id, chapter_id=chapter_id)
    chapters = get_syllabus_chapters(sch_id, class_id, subject_id)

    all_classes = SchoolClass.query.order_by(SchoolClass.id.asc()).all()
    all_subjects = Subject.query.order_by(Subject.name.asc()).all()

    return render_template(
        'syllabus/notebook_matrix.html',
        current_user=current_user,
        school_class=cls,
        subject=subj,
        all_classes=all_classes,
        all_subjects=all_subjects,
        students=matrix_data['students'],
        topics=matrix_data['topics'],
        corrections_map=matrix_data['corrections_map'],
        stats=matrix_data['stats'],
        chapters=chapters,
        selected_chapter_id=chapter_id
    )


@syllabus_bp.route('/syllabus/chapter/quick-add', methods=['POST'])
@login_required
def quick_add_topic():
    """Quick-adds a new custom chapter & topic directly into matrix."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user:
        return redirect(url_for('auth.login'))

    user_role = (current_user.user_type or '').lower()
    if user_role not in ('admin', 'teacher', 'employee'):
        flash('Permission denied to add curriculum topics.', 'danger')
        return redirect(url_for('syllabus.notebook_index'))

    sch_id = current_user.school_id or 1
    class_id = request.form.get('class_id', type=int)
    subject_id = request.form.get('subject_id', type=int)
    unit_name = request.form.get('unit_name', '').strip() or 'Custom Unit'
    topic_title = request.form.get('topic_title', '').strip()

    if class_id and subject_id and topic_title:
        quick_add_chapter_and_topic(sch_id, class_id, subject_id, unit_name, topic_title)
        flash(f"Topic '{topic_title}' added to curriculum successfully!", 'success')
        return redirect(url_for('syllabus.notebook_matrix', class_id=class_id, subject_id=subject_id))

    flash('Please fill in all required fields.', 'warning')
    return redirect(url_for('syllabus.notebook_index'))


@syllabus_bp.route('/syllabus/topic/<int:topic_id>/delete', methods=['POST'])
@login_required
def delete_topic_route(topic_id):
    """Deletes a topic from the curriculum."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user:
        return redirect(url_for('auth.login'))

    user_role = (current_user.user_type or '').lower()
    if user_role not in ('admin', 'teacher', 'employee'):
        flash('Permission denied to delete topics.', 'danger')
        return redirect(url_for('syllabus.notebook_index'))

    sch_id = current_user.school_id or 1
    topic = SyllabusTopic.query.get_or_404(topic_id)
    class_id = topic.chapter.class_id
    subject_id = topic.chapter.subject_id

    delete_topic(sch_id, topic_id)
    flash("Topic deleted successfully.", 'info')
    return redirect(url_for('syllabus.notebook_matrix', class_id=class_id, subject_id=subject_id))


@syllabus_bp.route('/notebook-tracker/update', methods=['POST'])
@login_required
def update_notebook_cell():
    """API endpoint for updating student notebook cell status (Teacher only)."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

    user_role = (current_user.user_type or '').lower()
    if user_role not in ('teacher', 'employee'):
        return jsonify({'status': 'error', 'message': 'Permission denied. Notebook status can only be updated by assigned teachers.'}), 403

    sch_id = current_user.school_id or 1
    data = request.get_json() or {}

    student_id = data.get('student_id', type=int)
    topic_id = data.get('topic_id', type=int)
    new_status = data.get('status', 'PENDING')

    if not student_id or not topic_id:
        return jsonify({'status': 'error', 'message': 'Missing student_id or topic_id'}), 400

    try:
        corr = update_notebook_status(sch_id, student_id, topic_id, new_status, current_user.id)
        return jsonify({
            'status': 'success',
            'student_id': student_id,
            'topic_id': topic_id,
            'cell_status': corr.status
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400


@syllabus_bp.route('/syllabus/admin-overview')
@login_required
def admin_overview():
    """Renders Admin Overall Syllabus Completion Overview Page with Graphs and Reports."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user or (current_user.user_type or '').lower() not in ('admin', 'employee'):
        flash('Permission denied. Admin overview is available for administrators.', 'danger')
        return redirect(url_for('syllabus.index'))

    sch_id = current_user.school_id or 1
    overview = get_admin_syllabus_overview(sch_id)

    # Compute graph aggregations
    total_classes = len(set([item['class'].id for item in overview])) if overview else 0
    total_topics_all = sum(item['progress']['total_topics'] for item in overview)
    total_completed_all = sum(item['progress']['completed_topics'] for item in overview)
    overall_completion_pct = round((total_completed_all / total_topics_all * 100.0), 1) if total_topics_all > 0 else 0.0

    return render_template(
        'syllabus/admin_overview.html',
        current_user=current_user,
        overview=overview,
        total_classes=total_classes,
        total_topics_all=total_topics_all,
        total_completed_all=total_completed_all,
        overall_completion_pct=overall_completion_pct
    )


@syllabus_bp.route('/syllabus/export/csv')
@login_required
def export_csv():
    """Exports syllabus & notebook completion statistics report as a CSV file for Excel/Admin reporting."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user or (current_user.user_type or '').lower() not in ('admin', 'employee'):
        flash('Permission denied to export reports.', 'danger')
        return redirect(url_for('syllabus.index'))

    import csv
    import io
    from flask import Response

    sch_id = current_user.school_id or 1
    overview = get_admin_syllabus_overview(sch_id)

    output = io.StringIO()
    writer = csv.writer(output)

    # Write CSV Header
    writer.writerow(['Class', 'Subject', 'Total Topics', 'Completed Topics', 'In Progress Topics', 'Not Started Topics', 'Completion Percentage (%)'])

    # Write Data Rows
    for item in overview:
        p = item['progress']
        writer.writerow([
            f"Class {item['class'].name}",
            item['subject'].name,
            p['total_topics'],
            p['completed_topics'],
            p['in_progress_topics'],
            p['not_started_topics'],
            f"{p['completion_percentage']}%"
        ])

    output.seek(0)

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=Syllabus_Notebook_Completion_Report.csv"}
    )
