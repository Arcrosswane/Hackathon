from datetime import datetime, date, time
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort, Response
from app.utils.decorators import login_required, role_required
from app.services.academic_service import get_active_academic_session
from app.services.class_service import get_all_classes
from app.services.subject_service import get_all_subjects
from app.models import (
    db, Examination, ExaminationClass, ExaminationSubject,
    ExaminationResult, ExamOverallResult, ExamType, GradeRule,
    QuestionPaper, SchoolClass, Section, Subject, Student, Guardian, GuardianStudent, User
)
from app.services.examination_service import (
    get_exam_types, create_exam_type, delete_exam_type, get_grade_rules, delete_grade_rule, calculate_grade_from_percentage,
    create_examination, update_examination, delete_examination, get_examinations, assign_classes_to_exam, add_exam_subject,
    attach_question_paper_to_exam_subject, check_schedule_conflicts, save_bulk_exam_marks,
    calculate_and_publish_exam_results, correct_published_result, get_student_published_results,
    get_exam_performance_statistics, generate_result_sheet_csv, generate_ai_exam_insights
)

examination_bp = Blueprint('examination', __name__, url_prefix='/examinations')


def resolve_current_student_id():
    """Helper to resolve logged in student's student_id from session/user."""
    linked_id = session.get('linked_entity_id')
    if linked_id:
        return linked_id
    user_id = session.get('user_id')
    if user_id:
        u = User.query.get(user_id)
        if u and u.linked_entity_id:
            return u.linked_entity_id
        if u:
            st = Student.query.filter(
                (Student.first_name.ilike(u.username)) | 
                (Student.registration_number.ilike(u.username)) |
                (Student.full_name.ilike(f"%{u.username}%"))
            ).first()
            if st:
                return st.id
    st = Student.query.first()
    return st.id if st else 1


def resolve_current_guardian_id():
    """Helper to resolve logged in parent's guardian_id from session/user."""
    linked_id = session.get('linked_entity_id')
    if linked_id:
        return linked_id
    user_id = session.get('user_id')
    if user_id:
        u = User.query.get(user_id)
        if u and u.linked_entity_id:
            return u.linked_entity_id
        if u:
            g = Guardian.query.filter_by(first_name=u.username).first()
            if g:
                return g.id
    g = Guardian.query.first()
    return g.id if g else 1


# ==========================================
# 1. EXAM DIRECTORY & MASTER CREATION
# ==========================================

@examination_bp.route('/', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'Teacher')
def exams_list():
    """Exam directory catalog & new exam creation modal."""
    if request.method == 'POST':
        name = request.form.get('name')
        exam_type_id = request.form.get('exam_type_id', type=int)
        desc = request.form.get('description')
        s_date_str = request.form.get('start_date')
        e_date_str = request.form.get('end_date')

        start_d = datetime.strptime(s_date_str, '%Y-%m-%d').date() if s_date_str else None
        end_d = datetime.strptime(e_date_str, '%Y-%m-%d').date() if e_date_str else None

        try:
            exam = create_examination(
                name=name,
                exam_type_id=exam_type_id,
                description=desc,
                start_date=start_d,
                end_date=end_d,
                created_by_id=session.get('user_id')
            )
            flash(f"✅ Examination '{exam.name}' created! Configure classes and schedule subjects below.", "success")
            return redirect(url_for('examination.exam_detail', exam_id=exam.id))
        except ValueError as e:
            flash(str(e), "danger")

    session_id = request.args.get('session_id', type=int)
    status_filter = request.args.get('status')
    class_filter = request.args.get('class_id', type=int)
    search_q = request.args.get('q')

    exams = get_examinations(session_id=session_id, status=status_filter, class_id=class_filter, search_query=search_q)
    exam_types = get_exam_types(active_only=True)
    all_classes = get_all_classes()

    return render_template(
        'examination/exams_list.html',
        exams=exams,
        exam_types=exam_types,
        all_classes=all_classes,
        status_filter=status_filter,
        class_filter=class_filter,
        search_q=search_q
    )


# ==========================================
# 2. EXAM SETUP, SUBJECT SCHEDULING & PAPER ATTACHMENT
# ==========================================

@examination_bp.route('/<int:exam_id>', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'Teacher')
def exam_detail(exam_id):
    """Exam detail view for class assignments, subject scheduling, conflict checks, and Question Paper attachment."""
    exam = Examination.query.get_or_404(exam_id)

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'assign_classes':
            cls_ids = request.form.getlist('class_ids', type=int)
            try:
                assign_classes_to_exam(exam.id, cls_ids)
                flash("✅ Assigned classes updated for examination.", "success")
            except ValueError as e:
                flash(str(e), "danger")
            return redirect(url_for('examination.exam_detail', exam_id=exam.id))

        elif action == 'schedule_subject':
            c_id = request.form.get('class_id', type=int)
            s_id = request.form.get('subject_id', type=int)
            date_str = request.form.get('exam_date')
            st_str = request.form.get('start_time')
            et_str = request.form.get('end_time')
            max_m = request.form.get('max_marks', type=float, default=100.0)
            pass_m = request.form.get('pass_marks', type=float, default=33.0)
            paper_id = request.form.get('question_paper_id', type=int)

            ex_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None
            start_t = datetime.strptime(st_str, '%H:%M').time() if st_str else None
            end_t = datetime.strptime(et_str, '%H:%M').time() if et_str else None

            # Conflict Detection
            conflicts = check_schedule_conflicts(c_id, ex_date, start_t, end_t)
            for c_warn in conflicts:
                flash(f"⚠️ Schedule Alert: {c_warn}", "warning")

            try:
                es = add_exam_subject(
                    exam_id=exam.id,
                    class_id=c_id,
                    subject_id=s_id,
                    exam_date=ex_date,
                    start_time=start_t,
                    end_time=end_t,
                    max_marks=max_m,
                    pass_marks=pass_m,
                    question_paper_id=paper_id
                )
                
                # Check Question Paper attachment warnings if paper selected
                if paper_id:
                    es, paper_warn = attach_question_paper_to_exam_subject(es.id, paper_id)
                    if paper_warn:
                        flash(paper_warn, "warning")

                flash("📅 Exam subject scheduled successfully!", "success")
            except ValueError as e:
                flash(str(e), "danger")
            return redirect(url_for('examination.exam_detail', exam_id=exam.id))

    all_classes = get_all_classes()
    all_subjects = get_all_subjects()
    assigned_class_ids = [ec.class_id for ec in exam.exam_classes]
    available_papers = QuestionPaper.query.filter_by(status='FINAL').all()

    return render_template(
        'examination/exam_detail.html',
        exam=exam,
        all_classes=all_classes,
        all_subjects=all_subjects,
        assigned_class_ids=assigned_class_ids,
        available_papers=available_papers
    )


@examination_bp.route('/subjects/<int:exam_subject_id>/attach-paper', methods=['POST'])
@login_required
@role_required('Admin', 'Teacher')
def attach_paper_route(exam_subject_id):
    """Attaches or detaches Module 15 Question Paper."""
    paper_id = request.form.get('question_paper_id', type=int)
    try:
        es, warn_msg = attach_question_paper_to_exam_subject(exam_subject_id, paper_id)
        if warn_msg:
            flash(warn_msg, "warning")
        else:
            flash("✅ Question Paper attached to exam subject.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(request.referrer or url_for('examination.exams_list'))


# ==========================================
# 3. BULK MARKS ENTRY SHEET
# ==========================================

@examination_bp.route('/teacher/marks-roster')
@login_required
@role_required('Teacher', 'Admin')
def teacher_marks_dashboard():
    """Teacher-facing marks evaluation roster dashboard."""
    exam_id = request.args.get('exam_id', type=int)
    class_id = request.args.get('class_id', type=int)

    query = ExaminationSubject.query.join(Examination)
    if exam_id:
        query = query.filter(ExaminationSubject.examination_id == exam_id)
    if class_id:
        query = query.filter(ExaminationSubject.class_id == class_id)

    exam_subjects = query.order_by(ExaminationSubject.exam_date.desc(), ExaminationSubject.id.desc()).all()
    all_exams = Examination.query.order_by(Examination.created_at.desc()).all()
    all_classes = get_all_classes()

    return render_template(
        'examination/teacher_marks_dashboard.html',
        exam_subjects=exam_subjects,
        all_exams=all_exams,
        all_classes=all_classes,
        selected_exam_id=exam_id,
        selected_class_id=class_id
    )


@examination_bp.route('/subjects/<int:exam_subject_id>/marks', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'Teacher')
def marks_entry(exam_subject_id):
    """Bulk marks entry table for authorized teachers and admins."""
    es = ExaminationSubject.query.get_or_404(exam_subject_id)
    exam = es.examination

    if request.method == 'POST':
        student_ids = request.form.getlist('student_ids', type=int)
        marks_payload = []

        for s_id in student_ids:
            att = request.form.get(f'attendance_{s_id}', 'PRESENT')
            m_val = request.form.get(f'marks_{s_id}')
            marks_payload.append({
                'student_id': s_id,
                'attendance_status': att,
                'marks_obtained': m_val
            })

        try:
            save_bulk_exam_marks(es.id, marks_payload, entered_by_id=session.get('user_id'))
            flash(f"✅ Marks saved for {len(marks_payload)} students!", "success")
            return redirect(url_for('examination.marks_entry', exam_subject_id=es.id, mode='view'))
        except ValueError as e:
            flash(str(e), "danger")

    # Retrieve students enrolled in this exam class/section
    st_query = Student.query.filter_by(class_id=es.class_id)
    if es.section_id:
        st_query = st_query.filter_by(section_id=es.section_id)
    students = st_query.order_by(Student.registration_number, Student.first_name).all()

    # Existing saved results map: student_id -> ExaminationResult
    existing_results = {}
    saved_res_list = ExaminationResult.query.filter_by(exam_subject_id=es.id).all()
    for r in saved_res_list:
        existing_results[r.student_id] = r

    # Display mode: 'view' (read-only view) or 'edit' (editable roster)
    default_mode = 'view' if saved_res_list else 'edit'
    mode = request.args.get('mode', default_mode)

    available_papers = QuestionPaper.query.filter_by(status='FINAL').all()

    return render_template(
        'examination/marks_entry.html',
        es=es,
        exam=exam,
        students=students,
        existing_results=existing_results,
        mode=mode,
        available_papers=available_papers
    )


@examination_bp.route('/subjects/<int:exam_subject_id>/edit-schedule', methods=['POST'])
@login_required
@role_required('Admin', 'Teacher')
def edit_exam_subject_route(exam_subject_id):
    """Edits a scheduled subject's parameters (date, time, max marks, pass marks, question paper)."""
    es = ExaminationSubject.query.get_or_404(exam_subject_id)
    
    date_str = request.form.get('exam_date')
    st_str = request.form.get('start_time')
    et_str = request.form.get('end_time')
    max_m = request.form.get('max_marks', type=float, default=100.0)
    pass_m = request.form.get('pass_marks', type=float, default=33.0)
    paper_id = request.form.get('question_paper_id', type=int)

    ex_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None
    start_t = datetime.strptime(st_str, '%H:%M').time() if st_str else None
    end_t = datetime.strptime(et_str, '%H:%M').time() if et_str else None

    try:
        es.exam_date = ex_date
        es.start_time = start_t
        es.end_time = end_t
        es.max_marks = float(max_m)
        es.pass_marks = float(pass_m)
        if paper_id is not None:
            es.question_paper_id = paper_id if paper_id != 0 else None
        
        db.session.commit()
        flash("⚙️ Exam subject schedule and parameters updated!", "success")
    except ValueError as e:
        flash(str(e), "danger")

    return redirect(request.referrer or url_for('examination.exam_detail', exam_id=es.examination_id))


# ==========================================
# 4. RESULT PUBLICATION & RESULT MATRIX SHEET
# ==========================================

@examination_bp.route('/<int:exam_id>/publish', methods=['POST'])
@login_required
@role_required('Admin')
def publish_results_route(exam_id):
    """Triggers server-side authoritative result calculation and publishes results."""
    try:
        published_count = calculate_and_publish_exam_results(exam_id, approved_by_id=session.get('user_id'))
        flash(f"🎉 Results calculated and published for {published_count} students!", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for('examination.result_sheet', exam_id=exam_id))


@examination_bp.route('/<int:exam_id>/result-sheet')
@login_required
@role_required('Admin', 'Teacher')
def result_sheet(exam_id):
    """Displays school/class result matrix with pass/fail badges, statistics, and AI insights."""
    exam = Examination.query.get_or_404(exam_id)
    selected_class_id = request.args.get('class_id', type=int)

    es_query = ExaminationSubject.query.filter_by(examination_id=exam.id)
    if selected_class_id:
        es_query = es_query.filter_by(class_id=selected_class_id)
    exam_subjects = es_query.order_by(ExaminationSubject.class_id, ExaminationSubject.subject_id).all()

    st_query = Student.query
    if selected_class_id:
        st_query = st_query.filter_by(class_id=selected_class_id)
    else:
        assigned_cls_ids = [ec.class_id for ec in exam.exam_classes]
        if assigned_cls_ids:
            st_query = st_query.filter(Student.class_id.in_(assigned_cls_ids))
    students = st_query.order_by(Student.class_id, Student.registration_number, Student.first_name).all()

    # Pre-fetch result map: (student_id, exam_subject_id) -> ExaminationResult
    results_map = {}
    res_list = ExaminationResult.query.filter_by(examination_id=exam.id).all()
    for r in res_list:
        results_map[(r.student_id, r.exam_subject_id)] = r

    # Pre-fetch overall map: student_id -> ExamOverallResult
    overalls_map = {}
    ov_list = ExamOverallResult.query.filter_by(examination_id=exam.id).all()
    for ov in ov_list:
        overalls_map[ov.student_id] = ov

    stats = get_exam_performance_statistics(exam.id, selected_class_id)
    all_classes = get_all_classes()

    return render_template(
        'examination/result_sheet.html',
        exam=exam,
        exam_subjects=exam_subjects,
        students=students,
        results_map=results_map,
        overalls_map=overalls_map,
        stats=stats,
        all_classes=all_classes,
        selected_class_id=selected_class_id
    )


@examination_bp.route('/<int:exam_id>/export-csv')
@login_required
@role_required('Admin', 'Teacher')
def export_result_csv(exam_id):
    """Downloads authoritative result sheet as CSV."""
    selected_class_id = request.args.get('class_id', type=int)
    try:
        csv_data = generate_result_sheet_csv(exam_id, selected_class_id)
        filename = f"Exam_Result_Sheet_{exam_id}.csv"
        return Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-disposition": f"attachment; filename={filename}"}
        )
    except ValueError as e:
        flash(str(e), "danger")
        return redirect(url_for('examination.result_sheet', exam_id=exam_id))


@examination_bp.route('/<int:exam_id>/ai-insights', methods=['POST'])
@login_required
@role_required('Admin', 'Teacher')
def generate_ai_insights_route(exam_id):
    """Generates Gemini AI anonymized class performance summary."""
    class_id = request.form.get('class_id', type=int)
    try:
        ai_summary = generate_ai_exam_insights(exam_id, class_id)
        flash("✨ AI Exam Performance Summary Generated!", "success")
        return render_template(
            'examination/result_sheet.html',
            exam=Examination.query.get_or_404(exam_id),
            exam_subjects=ExaminationSubject.query.filter_by(examination_id=exam_id).all(),
            students=Student.query.all(),
            results_map={},
            overalls_map={},
            stats=get_exam_performance_statistics(exam_id, class_id),
            all_classes=get_all_classes(),
            selected_class_id=class_id,
            ai_summary=ai_summary
        )
    except Exception as e:
        flash(str(e), "danger")
        return redirect(url_for('examination.result_sheet', exam_id=exam_id))


@examination_bp.route('/results/<int:result_id>/correct', methods=['POST'])
@login_required
@role_required('Admin')
def correct_result_route(result_id):
    """Unlocks and corrects a single published result with admin authorization."""
    new_m = request.form.get('marks_obtained', type=float)
    new_att = request.form.get('attendance_status', 'PRESENT')
    try:
        res = correct_published_result(result_id, new_m, new_att, admin_user_id=session.get('user_id'))
        flash("✏️ Published result corrected and overall grades recalculated.", "success")
        return redirect(url_for('examination.result_sheet', exam_id=res.examination_id))
    except ValueError as e:
        flash(str(e), "danger")
        return redirect(request.referrer or url_for('examination.exams_list'))


# ==========================================
# 5. STUDENT & PARENT SELF-SERVICE RESULT PORTALS
# ==========================================

@examination_bp.route('/student/results')
@login_required
def student_results():
    """Student portal view for published exam results only."""
    student_id = resolve_current_student_id()
    student_obj = Student.query.get(student_id)
    results_data = get_student_published_results(student_id)

    return render_template(
        'examination/student_results.html',
        student_obj=student_obj,
        results_data=results_data,
        is_parent=False
    )


@examination_bp.route('/parent/results')
@login_required
def parent_results():
    """Parent portal view for linked child's published exam results only."""
    guardian_id = resolve_current_guardian_id()
    
    # IDOR check: Get linked children
    links = GuardianStudent.query.filter_by(guardian_id=guardian_id).all()
    child_ids = [l.student_id for l in links]

    selected_student_id = request.args.get('student_id', type=int)
    if not selected_student_id and child_ids:
        selected_student_id = child_ids[0]

    if selected_student_id and selected_student_id not in child_ids:
        flash("Unauthorized access to student results.", "danger")
        abort(403)

    student_obj = Student.query.get(selected_student_id) if selected_student_id else None
    results_data = get_student_published_results(selected_student_id) if selected_student_id else []

    linked_students = Student.query.filter(Student.id.in_(child_ids)).all() if child_ids else []

    return render_template(
        'examination/student_results.html',
        student_obj=student_obj,
        linked_students=linked_students,
        results_data=results_data,
        is_parent=True
    )


# ==========================================
# 6. CONFIGURABLE EXAM TYPES & GRADE RULES
# ==========================================

@examination_bp.route('/types', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def exam_types_page():
    """Configures Exam Types and Grade Rules."""
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'create_exam_type':
            name = request.form.get('name')
            code = request.form.get('code')
            desc = request.form.get('description')
            try:
                create_exam_type(name, code, desc)
                flash("✅ Exam Type created successfully!", "success")
            except ValueError as e:
                flash(str(e), "danger")

        elif action == 'create_grade_rule':
            g_name = request.form.get('grade')
            min_p = request.form.get('min_percentage', type=float)
            max_p = request.form.get('max_percentage', type=float)
            desc = request.form.get('description')

            sch = School.query.first()
            school_id = sch.id if sch else 1

            gr = GradeRule(
                institute_id=school_id,
                grade=g_name,
                min_percentage=min_p,
                max_percentage=max_p,
                description=desc
            )
            db.session.add(gr)
            db.session.commit()
            flash("✅ Grade Rule created successfully!", "success")

        return redirect(url_for('examination.exam_types_page'))

    exam_types = get_exam_types(active_only=False)
    grade_rules = get_grade_rules(active_only=False)

    return render_template(
        'examination/exam_types.html',
        exam_types=exam_types,
        grade_rules=grade_rules
    )


@examination_bp.route('/<int:exam_id>/delete', methods=['POST'])
@login_required
@role_required('Admin')
def delete_exam_route(exam_id):
    """Deletes an examination and all associated subject schedules and results."""
    try:
        delete_examination(exam_id)
        flash("🗑️ Examination deleted successfully.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for('examination.exams_list'))


@examination_bp.route('/types/<int:type_id>/delete', methods=['POST'])
@login_required
@role_required('Admin')
def delete_exam_type_route(type_id):
    """Deletes an exam category type."""
    try:
        delete_exam_type(type_id)
        flash("🗑️ Exam Type deleted successfully.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for('examination.exam_types_page'))


@examination_bp.route('/grades/<int:rule_id>/delete', methods=['POST'])
@login_required
@role_required('Admin')
def delete_grade_rule_route(rule_id):
    """Deletes a grade rule."""
    try:
        delete_grade_rule(rule_id)
        flash("🗑️ Grade Rule deleted successfully.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for('examination.exam_types_page'))
