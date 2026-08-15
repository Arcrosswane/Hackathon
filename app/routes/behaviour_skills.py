from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from app.models import (
    db, BehaviourCategory, BehaviourRecord, SkillDefinition, SkillAssessment,
    Student, StudentEnrollment, SchoolClass, Section, Employee, User, Guardian, GuardianStudent
)
from app.utils.decorators import login_required, role_required
from app.services.academic_service import get_active_academic_session
from app.services.class_service import get_classes_for_session, get_sections_for_class
from app.services.employee_service import get_teachers, get_employee_by_id
from app.services.student_service import get_all_students, get_student_by_id, get_current_enrollment
from app.services.behaviour_skills_service import (
    get_all_behaviour_categories, create_behaviour_category, update_behaviour_category, toggle_behaviour_category_status,
    get_all_skill_definitions, create_skill_definition, update_skill_definition, toggle_skill_definition_status,
    create_behaviour_record, update_behaviour_record, delete_behaviour_record, get_behaviour_records,
    record_skill_assessment, record_bulk_skill_assessments, get_skill_assessments,
    get_student_development_summary, verify_teacher_student_access, verify_parent_student_access,
    RATING_LABELS, VALID_BEHAVIOUR_TYPES, VALID_SEVERITIES, VALID_VISIBILITIES
)

behaviour_skills_bp = Blueprint('behaviour_skills', __name__, url_prefix='/behaviour-skills')

def get_current_employee_id():
    """Helper to resolve current logged in user's Employee ID if teacher/employee."""
    user_id = session.get('user_id')
    if not user_id:
        return None
    u = User.query.get(user_id)
    if u and u.user_type in ('Teacher', 'Employee') and u.linked_entity_id:
        return u.linked_entity_id
    first_emp = Employee.query.filter_by(is_teacher=True).first() or Employee.query.first()
    return first_emp.id if first_emp else 1

def get_current_guardian_id():
    """Helper to resolve current logged in user's Guardian ID if parent."""
    user_id = session.get('user_id')
    if not user_id:
        return None
    u = User.query.get(user_id)
    if u and u.user_type in ('Parent', 'Guardian') and u.linked_entity_id:
        return u.linked_entity_id
    first_g = Guardian.query.first()
    return first_g.id if first_g else 1

def get_current_student_id():
    """Helper to resolve current logged in user's Student ID if student."""
    user_id = session.get('user_id')
    if not user_id:
        return None
    u = User.query.get(user_id)
    if u and u.user_type == 'Student' and u.linked_entity_id:
        return u.linked_entity_id
    first_s = Student.query.first()
    return first_s.id if first_s else 1


# ==========================================
# 1. ADMIN CATEGORY & SKILL CONFIGURATION
# ==========================================

@behaviour_skills_bp.route('/categories', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def manage_categories():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        try:
            cat = create_behaviour_category(name, description)
            flash(f"Category '{cat.name}' created successfully!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Failed to create category: {str(e)}", "danger")
        return redirect(url_for('behaviour_skills.manage_categories'))

    categories = get_all_behaviour_categories()
    return render_template('behaviour_skills/categories.html', categories=categories)

@behaviour_skills_bp.route('/categories/<int:category_id>/edit', methods=['POST'])
@login_required
@role_required('admin')
def edit_category(category_id):
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    is_active = bool(request.form.get('is_active'))
    try:
        cat = update_behaviour_category(category_id, name, description, is_active=is_active)
        flash(f"Category '{cat.name}' updated successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to update category: {str(e)}", "danger")
    return redirect(url_for('behaviour_skills.manage_categories'))

@behaviour_skills_bp.route('/categories/<int:category_id>/toggle', methods=['POST'])
@login_required
@role_required('admin')
def toggle_category(category_id):
    try:
        cat = toggle_behaviour_category_status(category_id)
        status_str = "activated" if cat.is_active else "archived"
        flash(f"Category '{cat.name}' has been {status_str}.", "info")
    except Exception as e:
        flash(str(e), "danger")
    return redirect(url_for('behaviour_skills.manage_categories'))

@behaviour_skills_bp.route('/skills', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def manage_skills():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        group_name = request.form.get('group_name', 'General').strip()
        description = request.form.get('description', '').strip()
        try:
            skill = create_skill_definition(name, group_name, description)
            flash(f"Skill '{skill.name}' created successfully!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Failed to create skill: {str(e)}", "danger")
        return redirect(url_for('behaviour_skills.manage_skills'))

    skills = get_all_skill_definitions()
    return render_template('behaviour_skills/skills.html', skills=skills)

@behaviour_skills_bp.route('/skills/<int:skill_id>/edit', methods=['POST'])
@login_required
@role_required('admin')
def edit_skill(skill_id):
    name = request.form.get('name', '').strip()
    group_name = request.form.get('group_name', 'General').strip()
    description = request.form.get('description', '').strip()
    is_active = bool(request.form.get('is_active'))
    try:
        skill = update_skill_definition(skill_id, name, group_name, description, is_active=is_active)
        flash(f"Skill '{skill.name}' updated successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to update skill: {str(e)}", "danger")
    return redirect(url_for('behaviour_skills.manage_skills'))

@behaviour_skills_bp.route('/skills/<int:skill_id>/toggle', methods=['POST'])
@login_required
@role_required('admin')
def toggle_skill(skill_id):
    try:
        skill = toggle_skill_definition_status(skill_id)
        status_str = "activated" if skill.is_active else "archived"
        flash(f"Skill '{skill.name}' has been {status_str}.", "info")
    except Exception as e:
        flash(str(e), "danger")
    return redirect(url_for('behaviour_skills.manage_skills'))


# ==========================================
# 2. BEHAVIOUR RECORDS ROUTER & CRUD
# ==========================================

@behaviour_skills_bp.route('/behaviour', methods=['GET'])
@login_required
@role_required('admin', 'teacher', 'employee')
def behaviour_index():
    active_session = get_active_academic_session()
    if not active_session:
        flash("No active academic session found.", "warning")
        return redirect(url_for('admin.dashboard'))

    user_role = session.get('user_role', '').lower()
    current_emp_id = get_current_employee_id()

    class_id = request.args.get('class_id', type=int)
    section_id = request.args.get('section_id', type=int)
    category_id = request.args.get('category_id', type=int)
    type_val = request.args.get('type', '').strip()
    severity = request.args.get('severity', '').strip()
    search_q = request.args.get('q', '').strip()

    records = get_behaviour_records(
        session_id=active_session.id,
        class_id=class_id,
        section_id=section_id,
        category_id=category_id,
        type_val=type_val,
        severity=severity,
        role=user_role,
        search_query=search_q
    )

    classes = get_classes_for_session(active_session.id)
    sections = get_sections_for_class(class_id) if class_id else []
    categories = get_all_behaviour_categories(active_only=True)

    return render_template(
        'behaviour_skills/behaviour_list.html',
        active_session=active_session,
        records=records,
        classes=classes,
        sections=sections,
        categories=categories,
        selected_class_id=class_id,
        selected_section_id=section_id,
        selected_category_id=category_id,
        selected_type=type_val,
        selected_severity=severity,
        search_q=search_q
    )

@behaviour_skills_bp.route('/behaviour/create', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'teacher', 'employee')
def create_behaviour():
    active_session = get_active_academic_session()
    if not active_session:
        flash("No active academic session found.", "warning")
        return redirect(url_for('behaviour_skills.behaviour_index'))

    user_role = session.get('user_role', '').lower()
    current_emp_id = get_current_employee_id()

    if request.method == 'POST':
        student_id = request.form.get('student_id', type=int)
        category_id = request.form.get('category_id', type=int)
        title = request.form.get('title', '').strip()
        type_val = request.form.get('type', 'POSITIVE').strip()
        severity = request.form.get('severity', 'LOW').strip()
        visibility = request.form.get('visibility', 'BOTH').strip()
        date_str = request.form.get('date', '').strip()
        description = request.form.get('description', '').strip()
        assessor_id = current_emp_id if user_role in ('teacher', 'employee') else request.form.get('assessor_id', type=int)

        # IDOR / Security check
        if user_role in ('teacher', 'employee') and not verify_teacher_student_access(current_emp_id, student_id):
            flash("Unauthorized access: You are not authorized to record observations for this student.", "danger")
            return redirect(url_for('behaviour_skills.behaviour_index'))

        try:
            date_val = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else date.today()
            rec = create_behaviour_record(
                student_id=student_id,
                assessor_id=assessor_id or current_emp_id,
                category_id=category_id,
                title=title,
                date_val=date_val,
                type_val=type_val,
                severity=severity,
                visibility=visibility,
                description=description,
                session_id=active_session.id
            )
            flash(f"Behaviour observation '{rec.title}' recorded for {rec.student.full_name}!", "success")
            return redirect(url_for('behaviour_skills.behaviour_index'))
        except Exception as e:
            db.session.rollback()
            flash(f"Failed to record observation: {str(e)}", "danger")

    classes = get_classes_for_session(active_session.id)
    categories = get_all_behaviour_categories(active_only=True)
    teachers = get_teachers()

    return render_template(
        'behaviour_skills/behaviour_form.html',
        active_session=active_session,
        classes=classes,
        categories=categories,
        teachers=teachers,
        record=None,
        today_date=date.today().strftime('%Y-%m-%d')
    )

@behaviour_skills_bp.route('/behaviour/<int:record_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'teacher', 'employee')
def edit_behaviour(record_id):
    active_session = get_active_academic_session()
    rec = BehaviourRecord.query.get(record_id)
    if not rec:
        flash("Behaviour record not found.", "danger")
        return redirect(url_for('behaviour_skills.behaviour_index'))

    user_role = session.get('user_role', '').lower()
    current_emp_id = get_current_employee_id()

    # IDOR Check: Teachers can only edit their own observations
    if user_role in ('teacher', 'employee') and rec.assessor_id != current_emp_id:
        flash("You are not authorized to edit observations recorded by another staff member.", "danger")
        return redirect(url_for('behaviour_skills.behaviour_index'))

    if request.method == 'POST':
        category_id = request.form.get('category_id', type=int)
        title = request.form.get('title', '').strip()
        type_val = request.form.get('type', rec.type).strip()
        severity = request.form.get('severity', rec.severity).strip()
        visibility = request.form.get('visibility', rec.visibility).strip()
        date_str = request.form.get('date', '').strip()
        description = request.form.get('description', '').strip()

        try:
            date_val = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else rec.date
            update_behaviour_record(
                record_id=rec.id,
                title=title,
                date_val=date_val,
                category_id=category_id,
                type_val=type_val,
                severity=severity,
                visibility=visibility,
                description=description
            )
            flash(f"Observation '{rec.title}' updated successfully!", "success")
            return redirect(url_for('behaviour_skills.behaviour_index'))
        except Exception as e:
            db.session.rollback()
            flash(f"Failed to update observation: {str(e)}", "danger")

    categories = get_all_behaviour_categories(active_only=True)
    return render_template(
        'behaviour_skills/behaviour_form.html',
        active_session=active_session,
        categories=categories,
        record=rec,
        today_date=rec.date.strftime('%Y-%m-%d')
    )

@behaviour_skills_bp.route('/behaviour/<int:record_id>/delete', methods=['POST'])
@login_required
@role_required('admin', 'teacher', 'employee')
def delete_behaviour(record_id):
    rec = BehaviourRecord.query.get(record_id)
    if not rec:
        flash("Behaviour record not found.", "danger")
        return redirect(url_for('behaviour_skills.behaviour_index'))

    user_role = session.get('user_role', '').lower()
    current_emp_id = get_current_employee_id()

    if user_role in ('teacher', 'employee') and rec.assessor_id != current_emp_id:
        flash("Unauthorized deletion attempt blocked.", "danger")
        return redirect(url_for('behaviour_skills.behaviour_index'))

    try:
        delete_behaviour_record(rec.id)
        flash("Behaviour observation record deleted successfully.", "info")
    except Exception as e:
        flash(f"Failed to delete record: {str(e)}", "danger")

    return redirect(url_for('behaviour_skills.behaviour_index'))


# ==========================================
# 3. SKILL ASSESSMENTS ROUTER & BULK ASSESS
# ==========================================

@behaviour_skills_bp.route('/assessments', methods=['GET'])
@login_required
@role_required('admin', 'teacher', 'employee')
def assessments_index():
    active_session = get_active_academic_session()
    if not active_session:
        flash("No active academic session found.", "warning")
        return redirect(url_for('admin.dashboard'))

    class_id = request.args.get('class_id', type=int)
    section_id = request.args.get('section_id', type=int)
    skill_id = request.args.get('skill_id', type=int)

    assessments = get_skill_assessments(
        session_id=active_session.id,
        class_id=class_id,
        section_id=section_id,
        skill_id=skill_id
    )

    classes = get_classes_for_session(active_session.id)
    sections = get_sections_for_class(class_id) if class_id else []
    skills = get_all_skill_definitions(active_only=True)

    return render_template(
        'behaviour_skills/assessments_list.html',
        active_session=active_session,
        assessments=assessments,
        classes=classes,
        sections=sections,
        skills=skills,
        selected_class_id=class_id,
        selected_section_id=section_id,
        selected_skill_id=skill_id,
        rating_labels=RATING_LABELS
    )

@behaviour_skills_bp.route('/assessments/create', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'teacher', 'employee')
def create_assessment():
    active_session = get_active_academic_session()
    user_role = session.get('user_role', '').lower()
    current_emp_id = get_current_employee_id()

    if request.method == 'POST':
        student_id = request.form.get('student_id', type=int)
        skill_id = request.form.get('skill_id', type=int)
        rating = request.form.get('rating', type=int)
        date_str = request.form.get('assessment_date', '').strip()
        observation = request.form.get('observation', '').strip()
        assessor_id = current_emp_id if user_role in ('teacher', 'employee') else request.form.get('assessor_id', type=int)

        if user_role in ('teacher', 'employee') and not verify_teacher_student_access(current_emp_id, student_id):
            flash("Unauthorized access to target student.", "danger")
            return redirect(url_for('behaviour_skills.assessments_index'))

        try:
            date_val = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else date.today()
            ass = record_skill_assessment(
                student_id=student_id,
                skill_id=skill_id,
                assessor_id=assessor_id or current_emp_id,
                rating=rating,
                assessment_date=date_val,
                observation=observation,
                session_id=active_session.id
            )
            flash(f"Skill assessment recorded for {ass.student.full_name}!", "success")
            return redirect(url_for('behaviour_skills.assessments_index'))
        except Exception as e:
            db.session.rollback()
            flash(f"Failed to record skill assessment: {str(e)}", "danger")

    classes = get_classes_for_session(active_session.id)
    skills = get_all_skill_definitions(active_only=True)
    teachers = get_teachers()

    return render_template(
        'behaviour_skills/assessment_form.html',
        active_session=active_session,
        classes=classes,
        skills=skills,
        teachers=teachers,
        rating_labels=RATING_LABELS,
        today_date=date.today().strftime('%Y-%m-%d')
    )

@behaviour_skills_bp.route('/assessments/bulk', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'teacher', 'employee')
def bulk_assessments():
    active_session = get_active_academic_session()
    user_role = session.get('user_role', '').lower()
    current_emp_id = get_current_employee_id()

    class_id = request.args.get('class_id', type=int) or request.form.get('class_id', type=int)
    section_id = request.args.get('section_id', type=int) or request.form.get('section_id', type=int)
    skill_id = request.args.get('skill_id', type=int) or request.form.get('skill_id', type=int)

    if request.method == 'POST' and request.form.get('action') == 'save_bulk':
        date_str = request.form.get('assessment_date', '').strip()
        date_val = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else date.today()

        # Extract student ratings from form
        assessments_dict = {}
        for key, val in request.form.items():
            if key.startswith('rating_'):
                stu_id = key.replace('rating_', '')
                obs = request.form.get(f'observation_{stu_id}', '')
                assessments_dict[stu_id] = {
                    'rating': val,
                    'observation': obs
                }

        try:
            cnt = record_bulk_skill_assessments(
                skill_id=skill_id,
                assessor_id=current_emp_id,
                assessment_date=date_val,
                class_id=class_id,
                section_id=section_id,
                assessments_dict=assessments_dict,
                session_id=active_session.id
            )
            flash(f"Bulk skill assessments recorded for {cnt} students!", "success")
            return redirect(url_for('behaviour_skills.assessments_index'))
        except Exception as e:
            db.session.rollback()
            flash(f"Failed to record bulk assessments: {str(e)}", "danger")

    # Fetch eligible roster for selected class/section
    students = []
    if class_id:
        en_query = StudentEnrollment.query.filter_by(
            academic_session_id=active_session.id,
            class_id=class_id,
            is_current=True
        )
        if section_id:
            en_query = en_query.filter_by(section_id=section_id)
        enrollments = en_query.order_by(StudentEnrollment.roll_number.asc()).all()
        students = [en.student for en in enrollments]

    classes = get_classes_for_session(active_session.id)
    sections = get_sections_for_class(class_id) if class_id else []
    skills = get_all_skill_definitions(active_only=True)

    return render_template(
        'behaviour_skills/bulk_assessment_form.html',
        active_session=active_session,
        classes=classes,
        sections=sections,
        skills=skills,
        students=students,
        selected_class_id=class_id,
        selected_section_id=section_id,
        selected_skill_id=skill_id,
        rating_labels=RATING_LABELS,
        today_date=date.today().strftime('%Y-%m-%d')
    )


# ==========================================
# 4. STUDENT & PARENT DEVELOPMENT VIEWS
# ==========================================

@behaviour_skills_bp.route('/my-development', methods=['GET'])
@login_required
@role_required('student')
def student_development():
    student_id = get_current_student_id()
    if not student_id:
        flash("Student profile not found.", "danger")
        return redirect(url_for('student.dashboard'))

    active_session = get_active_academic_session()
    summary_data = get_student_development_summary(student_id, session_id=active_session.id if active_session else None, role='student')

    return render_template('behaviour_skills/student_summary.html', summary=summary_data, view_mode='student')

@behaviour_skills_bp.route('/child', methods=['GET'])
@behaviour_skills_bp.route('/child/<int:student_id>', methods=['GET'])
@login_required
@role_required('parent', 'guardian')
def parent_child_development(student_id=None):
    guardian_id = get_current_guardian_id()

    if not student_id:
        link = GuardianStudent.query.filter_by(guardian_id=guardian_id).first()
        if link:
            student_id = link.student_id
        else:
            flash("No linked children found for your guardian account.", "warning")
            return redirect(url_for('parent.dashboard'))

    # IDOR Protection
    if not verify_parent_student_access(guardian_id, student_id):
        flash("Unauthorized access: You can only view records for your linked child.", "danger")
        return redirect(url_for('parent.dashboard'))

    active_session = get_active_academic_session()
    summary_data = get_student_development_summary(student_id, session_id=active_session.id if active_session else None, role='parent')

    return render_template('behaviour_skills/student_summary.html', summary=summary_data, view_mode='parent')

@behaviour_skills_bp.route('/summary/<int:student_id>', methods=['GET'])
@login_required
@role_required('admin', 'teacher', 'employee')
def student_summary_view(student_id):
    active_session = get_active_academic_session()
    user_role = session.get('user_role', '').lower()
    current_emp_id = get_current_employee_id()

    if user_role in ('teacher', 'employee') and not verify_teacher_student_access(current_emp_id, student_id):
        flash("Unauthorized access to student development summary.", "danger")
        return redirect(url_for('behaviour_skills.behaviour_index'))

    summary_data = get_student_development_summary(student_id, session_id=active_session.id if active_session else None, role=user_role)

    return render_template('behaviour_skills/student_summary.html', summary=summary_data, view_mode='staff')


# ==========================================
# 5. AJAX API ENDPOINTS
# ==========================================

@behaviour_skills_bp.route('/api/classes/<int:class_id>/students', methods=['GET'])
@login_required
def api_get_students(class_id):
    """AJAX helper returning students for selected class & optional section."""
    section_id = request.args.get('section_id', type=int)
    active_session = get_active_academic_session()

    en_query = StudentEnrollment.query.filter_by(
        academic_session_id=active_session.id if active_session else 1,
        class_id=class_id,
        is_current=True
    )
    if section_id:
        en_query = en_query.filter_by(section_id=section_id)

    enrollments = en_query.all()
    students_data = [{
        'id': en.student.id,
        'full_name': en.student.full_name,
        'registration_number': en.student.registration_number,
        'roll_number': en.roll_number
    } for en in enrollments]

    return jsonify(students_data)
