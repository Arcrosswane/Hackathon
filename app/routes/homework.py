import os
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file, jsonify, current_app
from app.models import (
    db, Homework, HomeworkAttachment, HomeworkSubmission,
    User, SchoolClass, Section, Subject, Employee, Student, AcademicSession, GuardianStudent
)
from app.utils.decorators import login_required, role_required
from app.services.academic_service import get_active_academic_session
from app.services.class_service import get_classes_for_session, get_sections_for_class
from app.services.subject_service import get_subjects_for_class
from app.services.employee_service import get_teachers, get_employee_by_id
from app.services.homework_service import (
    get_homework_by_id, get_all_homework, create_homework, update_homework,
    publish_homework, archive_homework, delete_homework, get_student_eligible_homework,
    submit_student_homework, get_homework_submission_roster, review_student_submission,
    get_parent_children_homework_summary, ai_evaluate_submission, evaluate_all_pending_submissions_with_ai
)

homework_bp = Blueprint('homework', __name__, url_prefix='/homework')

def get_current_teacher_id():
    """Helper to resolve current logged in user's Employee ID if teacher/employee."""
    user_id = session.get('user_id')
    if not user_id:
        return None
    u = User.query.get(user_id)
    if u and u.user_type in ('Teacher', 'Employee') and u.linked_entity_id:
        return u.linked_entity_id
    first_t = Employee.query.filter_by(is_teacher=True).first()
    return first_t.id if first_t else None

def get_current_student_id():
    """Helper to resolve current logged in user's Student ID."""
    user_id = session.get('user_id')
    if not user_id:
        return None
    u = User.query.get(user_id)
    if u and u.user_type == 'Student' and u.linked_entity_id:
        return u.linked_entity_id
    return session.get('linked_entity_id')

def get_current_guardian_id():
    """Helper to resolve current logged in user's Guardian ID."""
    user_id = session.get('user_id')
    if not user_id:
        return None
    u = User.query.get(user_id)
    if u and u.user_type == 'Parent' and u.linked_entity_id:
        return u.linked_entity_id
    return session.get('linked_entity_id')


# ==========================================
# JSON API ENDPOINTS FOR DYNAMIC FORMS
# ==========================================

@homework_bp.route('/api/classes/<int:class_id>/sections', methods=['GET'])
@login_required
def api_get_class_sections(class_id):
    """AJAX helper returning active sections for dynamic dropdowns."""
    sections = get_sections_for_class(class_id, active_only=True)
    return jsonify([{'id': s.id, 'name': s.display_name} for s in sections])

@homework_bp.route('/api/classes/<int:class_id>/subjects', methods=['GET'])
@login_required
def api_get_class_subjects(class_id):
    """AJAX helper returning subjects for dynamic dropdowns."""
    subjects = get_subjects_for_class(class_id)
    return jsonify([{'id': s.id, 'name': s.name, 'code': s.code or s.name} for s in subjects])


# ==========================================
# TEACHER / ADMIN ROUTES
# ==========================================

@homework_bp.route('/manage', methods=['GET'])
@login_required
@role_required('admin', 'teacher', 'employee')
def manage():
    active_session = get_active_academic_session()
    if not active_session:
        flash("No active academic session found. Please activate an academic session first.", "warning")
        return redirect(url_for('admin.dashboard'))

    user_role = session.get('user_role', '').lower()
    current_t_id = get_current_teacher_id()

    # Filter parameters
    class_id = request.args.get('class_id', type=int)
    section_id = request.args.get('section_id', type=int)
    subject_id = request.args.get('subject_id', type=int)
    status = request.args.get('status', '').strip()
    search_q = request.args.get('q', '').strip()

    # Teachers see their own homework by default, admins see all
    filter_teacher_id = current_t_id if user_role in ('teacher', 'employee') else request.args.get('teacher_id', type=int)

    homework_list = get_all_homework(
        session_id=active_session.id,
        class_id=class_id,
        section_id=section_id,
        subject_id=subject_id,
        teacher_id=filter_teacher_id,
        status=status if status else None,
        search_query=search_q
    )

    classes = get_classes_for_session(active_session.id)
    sections = get_sections_for_class(class_id) if class_id else []
    subjects = get_subjects_for_class(class_id) if class_id else Subject.query.all()
    teachers = get_teachers()

    # Compute submission statistics summary for each homework
    hw_data = []
    for hw in homework_list:
        roster, summary = get_homework_submission_roster(hw.id)
        hw_data.append({
            'homework': hw,
            'summary': summary
        })

    return render_template(
        'homework/manage.html',
        active_session=active_session,
        hw_data=hw_data,
        classes=classes,
        sections=sections,
        subjects=subjects,
        teachers=teachers,
        selected_class_id=class_id,
        selected_section_id=section_id,
        selected_subject_id=subject_id,
        selected_status=status,
        search_q=search_q,
        is_teacher=(user_role in ('teacher', 'employee'))
    )

@homework_bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'teacher', 'employee')
def create():
    active_session = get_active_academic_session()
    if not active_session:
        flash("No active academic session found.", "warning")
        return redirect(url_for('homework.manage'))

    user_role = session.get('user_role', '').lower()
    current_t_id = get_current_teacher_id()
    class_id = request.args.get('class_id', type=int)

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        class_id = request.form.get('class_id', type=int)
        section_id = request.form.get('section_id', type=int)
        subject_id = request.form.get('subject_id', type=int)
        teacher_id = current_t_id if user_role in ('teacher', 'employee') else request.form.get('teacher_id', type=int)
        
        assigned_str = request.form.get('assigned_date', '').strip()
        due_str = request.form.get('due_date', '').strip()
        max_marks = request.form.get('max_marks', type=float)
        description = request.form.get('description', '').strip()
        status = request.form.get('status', 'PUBLISHED').strip()
        evaluation_type = request.form.get('evaluation_type', 'MANUAL').strip()
        grading_rubric = request.form.get('grading_rubric', '').strip()

        files = request.files.getlist('attachments')

        try:
            assigned_date = datetime.strptime(assigned_str, '%Y-%m-%d').date() if assigned_str else datetime.utcnow().date()
            due_date = datetime.strptime(due_str, '%Y-%m-%d').date() if due_str else None

            hw = create_homework(
                teacher_id=teacher_id or current_t_id,
                class_id=class_id,
                section_id=section_id if section_id else None,
                subject_id=subject_id,
                title=title,
                description=description,
                assigned_date=assigned_date,
                due_date=due_date,
                max_marks=max_marks or 100.0,
                status=status,
                evaluation_type=evaluation_type,
                grading_rubric=grading_rubric,
                files=[f for f in files if f and f.filename],
                session_id=active_session.id
            )
            flash(f"Homework '{hw.title}' created successfully!", "success")
            return redirect(url_for('homework.manage'))
        except Exception as e:
            db.session.rollback()
            flash(f"Failed to create homework: {str(e)}", "danger")

    classes = get_classes_for_session(active_session.id)
    sections = get_sections_for_class(class_id) if class_id else []
    subjects = get_subjects_for_class(class_id) if class_id else Subject.query.all()
    teachers = get_teachers()

    return render_template(
        'homework/form.html',
        active_session=active_session,
        classes=classes,
        sections=sections,
        subjects=subjects,
        teachers=teachers,
        selected_class_id=class_id,
        homework=None,
        is_teacher=(user_role in ('teacher', 'employee'))
    )

@homework_bp.route('/<int:homework_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'teacher', 'employee')
def edit(homework_id):
    active_session = get_active_academic_session()
    hw = get_homework_by_id(homework_id)
    if not hw:
        flash("Homework assignment not found.", "danger")
        return redirect(url_for('homework.manage'))

    user_role = session.get('user_role', '').lower()
    current_t_id = get_current_teacher_id()

    # IDOR / Security check: Teacher can only edit their own homework
    if user_role in ('teacher', 'employee') and hw.teacher_id != current_t_id:
        flash("You are not authorized to edit homework created by another teacher.", "danger")
        return redirect(url_for('homework.manage'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        class_id = request.form.get('class_id', type=int)
        section_id = request.form.get('section_id', type=int)
        subject_id = request.form.get('subject_id', type=int)
        assigned_str = request.form.get('assigned_date', '').strip()
        due_str = request.form.get('due_date', '').strip()
        max_marks = request.form.get('max_marks', type=float)
        description = request.form.get('description', '').strip()
        status = request.form.get('status', hw.status).strip()
        evaluation_type = request.form.get('evaluation_type', hw.evaluation_type).strip()
        grading_rubric = request.form.get('grading_rubric', hw.grading_rubric or '').strip()

        remove_att_ids = request.form.getlist('remove_attachment_ids', type=int)
        new_files = request.files.getlist('attachments')

        try:
            assigned_date = datetime.strptime(assigned_str, '%Y-%m-%d').date() if assigned_str else hw.assigned_date
            due_date = datetime.strptime(due_str, '%Y-%m-%d').date() if due_str else hw.due_date

            update_homework(
                homework_id=hw.id,
                title=title,
                description=description,
                assigned_date=assigned_date,
                due_date=due_date,
                class_id=class_id,
                section_id=section_id,
                subject_id=subject_id,
                max_marks=max_marks or 100.0,
                status=status,
                evaluation_type=evaluation_type,
                grading_rubric=grading_rubric,
                new_files=[f for f in new_files if f and f.filename],
                remove_attachment_ids=remove_att_ids
            )
            flash(f"Homework '{hw.title}' updated successfully!", "success")
            return redirect(url_for('homework.manage'))
        except Exception as e:
            db.session.rollback()
            flash(f"Failed to update homework: {str(e)}", "danger")

    classes = get_classes_for_session(active_session.id)
    sections = get_sections_for_class(hw.class_id)
    subjects = get_subjects_for_class(hw.class_id)
    teachers = get_teachers()

    return render_template(
        'homework/form.html',
        active_session=active_session,
        classes=classes,
        sections=sections,
        subjects=subjects,
        teachers=teachers,
        selected_class_id=hw.class_id,
        homework=hw,
        is_teacher=(user_role in ('teacher', 'employee'))
    )

@homework_bp.route('/<int:homework_id>/publish', methods=['POST'])
@login_required
@role_required('admin', 'teacher', 'employee')
def publish(homework_id):
    try:
        hw = publish_homework(homework_id)
        flash(f"Homework '{hw.title}' has been published to students!", "success")
    except Exception as e:
        flash(f"Failed to publish homework: {str(e)}", "danger")
    return redirect(url_for('homework.manage'))

@homework_bp.route('/<int:homework_id>/archive', methods=['POST'])
@login_required
@role_required('admin', 'teacher', 'employee')
def archive(homework_id):
    try:
        hw = archive_homework(homework_id)
        flash(f"Homework '{hw.title}' archived successfully.", "info")
    except Exception as e:
        flash(f"Failed to archive homework: {str(e)}", "danger")
    return redirect(url_for('homework.manage'))

@homework_bp.route('/<int:homework_id>/delete', methods=['POST'])
@login_required
@role_required('admin', 'teacher', 'employee')
def delete(homework_id):
    try:
        res = delete_homework(homework_id)
        if res == 'ARCHIVED':
            flash("Homework has student submissions, so it was archived instead of deleted.", "warning")
        else:
            flash("Homework draft deleted successfully.", "success")
    except Exception as e:
        flash(f"Failed to delete homework: {str(e)}", "danger")
    return redirect(url_for('homework.manage'))

@homework_bp.route('/<int:homework_id>/submissions', methods=['GET'])
@login_required
@role_required('admin', 'teacher', 'employee')
def submissions(homework_id):
    hw = get_homework_by_id(homework_id)
    if not hw:
        flash("Homework assignment not found.", "danger")
        return redirect(url_for('homework.manage'))

    user_role = session.get('user_role', '').lower()
    current_t_id = get_current_teacher_id()

    # IDOR Protection
    if user_role in ('teacher', 'employee') and hw.teacher_id != current_t_id:
        flash("You are not authorized to view submissions for another teacher's homework.", "danger")
        return redirect(url_for('homework.manage'))

    roster, summary = get_homework_submission_roster(hw.id)

    return render_template(
        'homework/submissions.html',
        homework=hw,
        roster=roster,
        summary=summary
    )

@homework_bp.route('/submissions/<int:submission_id>/review', methods=['POST'])
@login_required
@role_required('admin', 'teacher', 'employee')
def review_submission_route(submission_id):
    sub = HomeworkSubmission.query.get(submission_id)
    if not sub:
        flash("Submission record not found.", "danger")
        return redirect(url_for('homework.manage'))

    teacher_id = get_current_teacher_id()
    marks = request.form.get('marks')
    feedback = request.form.get('feedback')

    try:
        review_student_submission(submission_id, teacher_id, marks=marks, feedback=feedback)
        flash(f"Review saved for {sub.student.full_name}.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to save review: {str(e)}", "danger")

    return redirect(url_for('homework.submissions', homework_id=sub.homework_id))


@homework_bp.route('/<int:homework_id>/ai-evaluate-all', methods=['POST'])
@login_required
@role_required('admin', 'teacher', 'employee')
def ai_evaluate_all(homework_id):
    hw = get_homework_by_id(homework_id)
    if not hw:
        flash("Homework assignment not found.", "danger")
        return redirect(url_for('homework.manage'))

    teacher_id = get_current_teacher_id()
    try:
        cnt = evaluate_all_pending_submissions_with_ai(homework_id, teacher_id=teacher_id)
        flash(f"🤖 AI Auto-Evaluation completed for {cnt} student submissions!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"AI Evaluation failed: {str(e)}", "danger")

    return redirect(url_for('homework.submissions', homework_id=hw.id))


@homework_bp.route('/submissions/<int:submission_id>/ai-evaluate', methods=['POST'])
@login_required
@role_required('admin', 'teacher', 'employee')
def ai_evaluate_single(submission_id):
    sub = HomeworkSubmission.query.get(submission_id)
    if not sub:
        flash("Submission record not found.", "danger")
        return redirect(url_for('homework.manage'))

    teacher_id = get_current_teacher_id()
    try:
        ai_evaluate_submission(submission_id, teacher_id=teacher_id)
        flash(f"🤖 AI Evaluation completed for {sub.student.full_name}'s submission!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"AI Evaluation failed: {str(e)}", "danger")

    return redirect(url_for('homework.submissions', homework_id=sub.homework_id))


# ==========================================
# STUDENT ROUTES
# ==========================================

@homework_bp.route('/student', methods=['GET'])
@login_required
@role_required('student')
def student_index():
    student_id = get_current_student_id()
    if not student_id:
        flash("Student profile not associated with your account.", "danger")
        return redirect(url_for('student.dashboard'))

    active_session = get_active_academic_session()
    items = get_student_eligible_homework(student_id, session_id=active_session.id if active_session else None)

    return render_template('homework/student_list.html', homework_items=items, active_session=active_session)

@homework_bp.route('/student/<int:homework_id>', methods=['GET'])
@login_required
@role_required('student')
def student_detail(homework_id):
    student_id = get_current_student_id()
    hw = get_homework_by_id(homework_id)
    if not hw or hw.status != 'PUBLISHED':
        flash("Homework assignment not available.", "danger")
        return redirect(url_for('homework.student_index'))

    # Verify student is in eligible class & section
    items = get_student_eligible_homework(student_id)
    matched_item = next((item for item in items if item['homework'].id == hw.id), None)
    if not matched_item:
        flash("You are not authorized to view this homework assignment.", "danger")
        return redirect(url_for('homework.student_index'))

    return render_template(
        'homework/student_detail.html',
        homework=hw,
        submission=matched_item['submission'],
        submission_status=matched_item['submission_status'],
        is_overdue=matched_item['is_overdue']
    )

@homework_bp.route('/student/<int:homework_id>/submit', methods=['POST'])
@login_required
@role_required('student')
def student_submit(homework_id):
    student_id = get_current_student_id()
    submission_text = request.form.get('submission_text', '').strip()
    attachment_file = request.files.get('attachment')

    try:
        sub = submit_student_homework(
            homework_id=homework_id,
            student_id=student_id,
            submission_text=submission_text,
            attachment_file=attachment_file
        )
        flash("Your homework has been submitted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Submission failed: {str(e)}", "danger")

    return redirect(url_for('homework.student_detail', homework_id=homework_id))


# ==========================================
# PARENT ROUTES
# ==========================================

@homework_bp.route('/parent', methods=['GET'])
@login_required
@role_required('parent', 'guardian')
def parent_index():
    guardian_id = get_current_guardian_id()
    if not guardian_id:
        flash("Parent profile not associated with your account.", "danger")
        return redirect(url_for('parent.dashboard'))

    active_session = get_active_academic_session()
    children_data = get_parent_children_homework_summary(guardian_id, session_id=active_session.id if active_session else None)

    return render_template('homework/parent_list.html', children_data=children_data, active_session=active_session)


# ==========================================
# SECURE FILE PROXY DOWNLOAD ROUTES
# ==========================================

@homework_bp.route('/attachment/<int:attachment_id>/download', methods=['GET'])
@login_required
def download_attachment(attachment_id):
    att = HomeworkAttachment.query.get(attachment_id)
    if not att:
        flash("Requested file attachment does not exist.", "danger")
        return redirect(url_for('admin.dashboard'))

    hw = att.homework
    user_role = session.get('user_role', '').lower()

    # IDOR Security Validation
    if user_role == 'student':
        student_id = get_current_student_id()
        items = get_student_eligible_homework(student_id)
        if not any(item['homework'].id == hw.id for item in items):
            flash("Unauthorized file access.", "danger")
            return redirect(url_for('homework.student_index'))
    elif user_role in ('parent', 'guardian'):
        guardian_id = get_current_guardian_id()
        children = get_parent_children_homework_summary(guardian_id)
        allowed = False
        for c in children:
            if any(item['homework'].id == hw.id for item in c['homework_items']):
                allowed = True
                break
        if not allowed:
            flash("Unauthorized file access.", "danger")
            return redirect(url_for('homework.parent_index'))

    # Serve file from static uploads
    full_path = os.path.join(current_app.static_folder, att.file_path)
    if not os.path.exists(full_path):
        flash("File not found on server.", "danger")
        return redirect(request.referrer or url_for('admin.dashboard'))

    return send_file(full_path, as_attachment=True, download_name=att.original_filename)

@homework_bp.route('/submission/<int:submission_id>/download', methods=['GET'])
@login_required
def download_submission(submission_id):
    sub = HomeworkSubmission.query.get(submission_id)
    if not sub or not sub.attachment_path:
        flash("Submission file attachment not found.", "danger")
        return redirect(url_for('admin.dashboard'))

    hw = sub.homework
    user_role = session.get('user_role', '').lower()
    current_t_id = get_current_teacher_id()
    current_s_id = get_current_student_id()
    current_g_id = get_current_guardian_id()

    # IDOR Security Validation
    if user_role == 'student' and sub.student_id != current_s_id:
        flash("Unauthorized file access.", "danger")
        return redirect(url_for('homework.student_index'))
    elif user_role in ('teacher', 'employee') and hw.teacher_id != current_t_id:
        flash("Unauthorized file access.", "danger")
        return redirect(url_for('homework.manage'))
    elif user_role in ('parent', 'guardian'):
        links = GuardianStudent.query.filter_by(guardian_id=current_g_id).all()
        if not any(link.student_id == sub.student_id for link in links):
            flash("Unauthorized file access.", "danger")
            return redirect(url_for('homework.parent_index'))

    full_path = os.path.join(current_app.static_folder, sub.attachment_path)
    if not os.path.exists(full_path):
        flash("File not found on server.", "danger")
        return redirect(request.referrer or url_for('admin.dashboard'))

    return send_file(full_path, as_attachment=True, download_name=sub.original_filename)
