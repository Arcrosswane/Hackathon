from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, abort
from app.utils.decorators import login_required, role_required
from app.services.academic_service import get_active_academic_session
from app.services.class_service import get_all_classes
from app.services.subject_service import get_all_subjects
from app.models import db, Question, QuestionPaper, QuestionPaperSection, QuestionPaperQuestion, SchoolClass, Subject
from app.services.question_bank_service import (
    create_question, update_question, archive_question, delete_question, delete_question_bank, delete_question_paper, get_questions,
    create_question_paper, add_question_to_paper_section, remove_question_from_paper,
    recalculate_paper_totals, finalize_question_paper, duplicate_question_paper,
    VALID_QUESTION_TYPES, VALID_DIFFICULTIES
)
from app.services.ai_question_service import generate_ai_questions, improve_question_with_ai, convert_document_to_questions

question_bank_bp = Blueprint('question_bank', __name__, url_prefix='/question-bank')


@question_bank_bp.route('/questions/<int:question_id>/delete', methods=['POST'])
@login_required
@role_required('Admin', 'Teacher')
def delete_question_route(question_id):
    """Permanently deletes a question from the Question Bank."""
    try:
        delete_question(question_id)
        flash("🗑️ Question deleted permanently.", "info")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(request.referrer or url_for('question_bank.questions_list'))


@question_bank_bp.route('/delete-bank', methods=['POST'])
@login_required
@role_required('Admin', 'Teacher')
def delete_bank_route():
    """Deletes an entire Question Bank for a specific Class & Subject."""
    cls_id = request.form.get('class_id', type=int)
    sub_id = request.form.get('subject_id', type=int)
    try:
        count = delete_question_bank(cls_id, sub_id)
        flash(f"🗑️ Deleted Question Bank ({count} questions removed).", "info")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for('question_bank.questions_list', view='banks'))


@question_bank_bp.route('/papers/<int:paper_id>/delete', methods=['POST'])
@login_required
@role_required('Admin', 'Teacher')
def delete_paper_route(paper_id):
    """Deletes a Question Paper draft."""
    try:
        delete_question_paper(paper_id)
        flash("🗑️ Question Paper deleted.", "info")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for('question_bank.papers_list'))


# ==========================================
# 5. STUDENT SELF-SERVICE PRACTICE & QUESTION BANKS
# ==========================================

@question_bank_bp.route('/student/banks')
@login_required
def student_banks():
    """Student portal view displaying all available Question Banks for practice."""
    all_classes = get_all_classes()
    all_subjects = get_all_subjects()

    all_active_qs = Question.query.filter_by(status='ACTIVE').all()
    bank_map = {}
    for q in all_active_qs:
        key = (q.class_id, q.subject_id)
        if key not in bank_map:
            bank_map[key] = []
        bank_map[key].append(q)

    student_banks_list = []
    for (c_id, s_id), q_list in bank_map.items():
        cls_obj = SchoolClass.query.get(c_id) if c_id else None
        sub_obj = Subject.query.get(s_id) if s_id else None
        chaps = sorted(list(set(q.chapter for q in q_list if q.chapter)))
        student_banks_list.append({
            'class_id': c_id,
            'subject_id': s_id,
            'class_name': cls_obj.display_name if cls_obj else 'General Class',
            'subject_name': sub_obj.name if sub_obj else 'General Subject',
            'count': len(q_list),
            'chapters': chaps[:4]
        })

    return render_template(
        'question_bank/student_banks.html',
        student_banks=student_banks_list,
        all_classes=all_classes,
        all_subjects=all_subjects
    )


@question_bank_bp.route('/student/practice')
@login_required
def student_practice():
    """Interactive student practice quiz session for selected class & subject."""
    cls_id = request.args.get('class_id', type=int)
    sub_id = request.args.get('subject_id', type=int)

    questions = get_questions(
        class_id=cls_id,
        subject_id=sub_id,
        status='ACTIVE'
    )

    cls_obj = SchoolClass.query.get(cls_id) if cls_id else None
    sub_obj = Subject.query.get(sub_id) if sub_id else None

    return render_template(
        'question_bank/student_practice.html',
        questions=questions,
        cls_obj=cls_obj,
        sub_obj=sub_obj
    )


# ==========================================
# 1. QUESTION BANK CATALOG & CRUD
# ==========================================

@question_bank_bp.route('/questions', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'Teacher')
def questions_list():
    """Browses, searches, and manages reusable questions in the Question Bank."""
    if request.method == 'POST':
        cls_id = request.form.get('class_id', type=int)
        sub_id = request.form.get('subject_id', type=int)
        q_text = request.form.get('question_text')
        q_type = request.form.get('question_type', 'MCQ')
        diff = request.form.get('difficulty', 'MEDIUM')
        marks = request.form.get('marks', type=float, default=1.0)
        chapter = request.form.get('chapter')
        topic = request.form.get('topic')
        opt_a = request.form.get('option_a')
        opt_b = request.form.get('option_b')
        opt_c = request.form.get('option_c')
        opt_d = request.form.get('option_d')
        corr_opt = request.form.get('correct_option')
        ans_text = request.form.get('answer_text')
        explanation = request.form.get('explanation')
        tags = request.form.get('tags')

        try:
            q = create_question(
                class_id=cls_id,
                subject_id=sub_id,
                question_text=q_text,
                question_type=q_type,
                difficulty=diff,
                marks=marks,
                chapter=chapter,
                topic=topic,
                option_a=opt_a,
                option_b=opt_b,
                option_c=opt_c,
                option_d=opt_d,
                correct_option=corr_opt,
                answer_text=ans_text,
                explanation=explanation,
                tags=tags,
                created_by_id=session.get('user_id')
            )
            flash(f"✅ Question #{q.id} created successfully!", "success")
            return redirect(url_for('question_bank.questions_list', class_id=cls_id or '', subject_id=sub_id or '', view='questions'))
        except ValueError as e:
            flash(str(e), "danger")

    # Filters
    selected_class_id = request.args.get('class_id', type=int)
    selected_subject_id = request.args.get('subject_id', type=int)
    chapter_filter = request.args.get('chapter')
    difficulty_filter = request.args.get('difficulty')
    type_filter = request.args.get('question_type')
    search_q = request.args.get('q')
    view_mode = request.args.get('view', 'banks') # 'banks' or 'questions'

    if selected_class_id or selected_subject_id or chapter_filter or difficulty_filter or type_filter or search_q:
        view_mode = 'questions'

    questions = get_questions(
        class_id=selected_class_id,
        subject_id=selected_subject_id,
        chapter=chapter_filter,
        difficulty=difficulty_filter,
        question_type=type_filter,
        search_query=search_q,
        status='ACTIVE'
    )

    all_classes = get_all_classes()
    all_subjects = get_all_subjects()

    # Calculate grouped Question Banks (Class + Subject)
    grouped_banks = []
    all_active_qs = Question.query.filter_by(status='ACTIVE').all()
    
    # Map (class_id, subject_id) -> list of questions
    bank_map = {}
    for q in all_active_qs:
        key = (q.class_id, q.subject_id)
        if key not in bank_map:
            bank_map[key] = []
        bank_map[key].append(q)

    for (c_id, s_id), q_list in bank_map.items():
        cls_obj = SchoolClass.query.get(c_id) if c_id else None
        sub_obj = Subject.query.get(s_id) if s_id else None
        chaps = sorted(list(set(q.chapter for q in q_list if q.chapter)))
        grouped_banks.append({
            'class_id': c_id,
            'subject_id': s_id,
            'class_name': cls_obj.display_name if cls_obj else 'General Class',
            'subject_name': sub_obj.name if sub_obj else 'General Subject',
            'count': len(q_list),
            'chapters': chaps[:4]
        })

    return render_template(
        'question_bank/questions_list.html',
        questions=questions,
        grouped_banks=grouped_banks,
        view_mode=view_mode,
        all_classes=all_classes,
        all_subjects=all_subjects,
        selected_class_id=selected_class_id,
        selected_subject_id=selected_subject_id,
        chapter_filter=chapter_filter,
        difficulty_filter=difficulty_filter,
        type_filter=type_filter,
        search_q=search_q,
        valid_types=sorted(list(VALID_QUESTION_TYPES)),
        valid_difficulties=sorted(list(VALID_DIFFICULTIES))
    )


@question_bank_bp.route('/import-document', methods=['POST'])
@login_required
@role_required('Admin', 'Teacher')
def import_document():
    """Uploads and converts an Excel, PDF, or text question paper file into structured Question Bank items."""
    file = request.files.get('document')
    cls_id = request.form.get('class_id', type=int)
    sub_id = request.form.get('subject_id', type=int)

    if not file or not file.filename:
        flash("Please select a document file (.xlsx, .csv, .pdf, .txt).", "warning")
        return redirect(url_for('question_bank.questions_list'))

    try:
        raw_bytes = file.read()
        candidate_questions = convert_document_to_questions(
            raw_file_bytes=raw_bytes,
            filename=file.filename,
            class_id=cls_id,
            subject_id=sub_id,
            user_id=session.get('user_id')
        )
        flash(f"📄 Successfully converted '{file.filename}' into {len(candidate_questions)} candidate questions! Review and edit below.", "success")
        
        all_classes = get_all_classes()
        all_subjects = get_all_subjects()

        return render_template(
            'question_bank/ai_generate.html',
            candidate_questions=candidate_questions,
            all_classes=all_classes,
            all_subjects=all_subjects,
            valid_types=sorted(list(VALID_QUESTION_TYPES)),
            valid_difficulties=sorted(list(VALID_DIFFICULTIES))
        )
    except Exception as e:
        flash(str(e), "danger")
        return redirect(url_for('question_bank.questions_list'))


@question_bank_bp.route('/questions/<int:question_id>/edit', methods=['POST'])
@login_required
@role_required('Admin', 'Teacher')
def edit_question(question_id):
    """Updates an existing question in the Question Bank."""
    try:
        update_question(
            question_id=question_id,
            question_text=request.form.get('question_text'),
            question_type=request.form.get('question_type'),
            difficulty=request.form.get('difficulty'),
            marks=request.form.get('marks', type=float),
            chapter=request.form.get('chapter'),
            topic=request.form.get('topic'),
            option_a=request.form.get('option_a'),
            option_b=request.form.get('option_b'),
            option_c=request.form.get('option_c'),
            option_d=request.form.get('option_d'),
            correct_option=request.form.get('correct_option'),
            answer_text=request.form.get('answer_text'),
            explanation=request.form.get('explanation'),
            tags=request.form.get('tags')
        )
        flash("⚡ Question updated successfully!", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(request.referrer or url_for('question_bank.questions_list'))


@question_bank_bp.route('/questions/<int:question_id>/archive', methods=['POST'])
@login_required
@role_required('Admin', 'Teacher')
def archive_question_route(question_id):
    """Archives a question."""
    try:
        archive_question(question_id)
        flash("📦 Question archived.", "info")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(request.referrer or url_for('question_bank.questions_list'))


# ==========================================
# 2. GEMINI AI QUESTION GENERATION & REVIEW
# ==========================================

@question_bank_bp.route('/ai-generate', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'Teacher')
def ai_generate():
    """AI Question Generator Wizard: Inputs parameters, calls Gemini API, and presents candidate review cards."""
    candidate_questions = []
    selected_cls_id = None
    selected_sub_id = None

    if request.method == 'POST':
        cls_id = request.form.get('class_id', type=int)
        sub_id = request.form.get('subject_id', type=int)
        chapters_input = request.form.get('chapters')
        diff = request.form.get('difficulty', 'MEDIUM')
        num_q = request.form.get('num_questions', type=int, default=5)
        q_types = request.form.getlist('question_types')
        instructions = request.form.get('teacher_instructions')

        selected_cls_id = cls_id
        selected_sub_id = sub_id

        s_class = SchoolClass.query.get(cls_id) if cls_id else None
        subject = Subject.query.get(sub_id) if sub_id else None

        class_name = s_class.display_name if s_class else "General"
        subject_name = subject.name if subject else "General Studies"
        chap_list = [c.strip() for c in chapters_input.split(',')] if chapters_input else ["General Topics"]

        try:
            candidate_questions = generate_ai_questions(
                class_name=class_name,
                subject_name=subject_name,
                chapters=chap_list,
                difficulty=diff,
                num_questions=num_q,
                question_types=q_types if q_types else ['MCQ', 'SHORT_ANSWER'],
                teacher_instructions=instructions,
                user_id=session.get('user_id'),
                class_id=cls_id,
                subject_id=sub_id
            )
            flash(f"✨ Gemini AI generated {len(candidate_questions)} candidate questions! Review and accept below.", "success")
        except Exception as e:
            flash(f"AI Question Generation error: {str(e)}", "danger")

    all_classes = get_all_classes()
    all_subjects = get_all_subjects()

    return render_template(
        'question_bank/ai_generate.html',
        candidate_questions=candidate_questions,
        selected_cls_id=selected_cls_id,
        selected_sub_id=selected_sub_id,
        all_classes=all_classes,
        all_subjects=all_subjects,
        valid_types=sorted(list(VALID_QUESTION_TYPES)),
        valid_difficulties=sorted(list(VALID_DIFFICULTIES))
    )


@question_bank_bp.route('/ai-accept', methods=['POST'])
@login_required
@role_required('Admin', 'Teacher')
def ai_accept():
    """Converts accepted AI candidate questions into permanent Question Bank entries."""
    selected_indices = request.form.getlist('accept_indices', type=int)
    global_class_id = request.form.get('global_class_id', type=int)
    global_subject_id = request.form.get('global_subject_id', type=int)
    accepted_count = 0
    errors = []

    if not global_class_id:
        fc = SchoolClass.query.first()
        global_class_id = fc.id if fc else 1
    if not global_subject_id:
        fs = Subject.query.first()
        global_subject_id = fs.id if fs else 1

    for idx in selected_indices:
        q_text = request.form.get(f'question_text_{idx}')
        if not q_text:
            continue

        item_class_id = request.form.get(f'class_id_{idx}', type=int) or global_class_id
        item_subject_id = request.form.get(f'subject_id_{idx}', type=int) or global_subject_id

        try:
            create_question(
                class_id=item_class_id,
                subject_id=item_subject_id,
                question_text=q_text,
                question_type=request.form.get(f'question_type_{idx}', 'MCQ'),
                difficulty=request.form.get(f'difficulty_{idx}', 'MEDIUM'),
                marks=request.form.get(f'marks_{idx}', type=float, default=1.0),
                chapter=request.form.get(f'chapter_{idx}'),
                option_a=request.form.get(f'option_a_{idx}'),
                option_b=request.form.get(f'option_b_{idx}'),
                option_c=request.form.get(f'option_c_{idx}'),
                option_d=request.form.get(f'option_d_{idx}'),
                correct_option=request.form.get(f'correct_option_{idx}'),
                answer_text=request.form.get(f'answer_text_{idx}'),
                explanation=request.form.get(f'explanation_{idx}'),
                tags="AI_GENERATED,Accepted",
                created_by_id=session.get('user_id')
            )
            accepted_count += 1
        except Exception as e:
            errors.append(str(e))

    if accepted_count > 0:
        flash(f"🎉 Accepted and saved {accepted_count} questions into the Question Bank!", "success")
    if errors:
        flash(f"⚠️ Warning: {len(errors)} items could not be saved: {errors[0]}", "warning")

    return redirect(url_for('question_bank.questions_list', class_id=global_class_id, subject_id=global_subject_id, view='questions'))


# ==========================================
# 3. QUESTION PAPER DIRECTORY & BUILDER
# ==========================================

@question_bank_bp.route('/papers', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'Teacher')
def papers_list():
    """Lists question papers directory & handles new paper creation."""
    if request.method == 'POST':
        title = request.form.get('title')
        cls_id = request.form.get('class_id', type=int)
        sub_id = request.form.get('subject_id', type=int)
        duration = request.form.get('duration_minutes', type=int, default=90)
        instructions = request.form.get('instructions')

        try:
            paper = create_question_paper(
                title=title,
                class_id=cls_id,
                subject_id=sub_id,
                instructions=instructions,
                duration_minutes=duration,
                created_by_id=session.get('user_id')
            )
            flash(f"📄 Draft Question Paper '{paper.title}' created! Add questions in the builder below.", "success")
            return redirect(url_for('question_bank.paper_builder', paper_id=paper.id))
        except ValueError as e:
            flash(str(e), "danger")

    papers = QuestionPaper.query.order_by(QuestionPaper.updated_at.desc()).all()
    all_classes = get_all_classes()
    all_subjects = get_all_subjects()

    return render_template(
        'question_bank/papers_list.html',
        papers=papers,
        all_classes=all_classes,
        all_subjects=all_subjects
    )


@question_bank_bp.route('/papers/<int:paper_id>/builder', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'Teacher')
def paper_builder(paper_id):
    """Interactive Paper Builder: Add questions from bank, manage sections, adjust marks."""
    paper = QuestionPaper.query.get_or_404(paper_id)

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add_question':
            sec_id = request.form.get('section_id', type=int)
            q_id = request.form.get('question_id', type=int)
            marks = request.form.get('marks', type=float)
            try:
                add_question_to_paper_section(sec_id, q_id, marks)
                flash("➕ Question added to section.", "success")
            except ValueError as e:
                flash(str(e), "danger")

        elif action == 'remove_question':
            pq_id = request.form.get('paper_question_id', type=int)
            try:
                remove_question_from_paper(pq_id)
                flash("🗑️ Question removed from paper.", "info")
            except ValueError as e:
                flash(str(e), "danger")

        elif action == 'add_section':
            sec_name = request.form.get('section_name')
            sec_inst = request.form.get('section_instructions')
            if sec_name:
                curr_sec_count = len(paper.sections)
                new_sec = QuestionPaperSection(
                    paper_id=paper.id,
                    section_name=sec_name.strip(),
                    section_instructions=sec_inst.strip() if sec_inst else None,
                    section_order=curr_sec_count + 1
                )
                db.session.add(new_sec)
                db.session.commit()
                flash(f"➕ Added section '{sec_name}'.", "success")

        return redirect(url_for('question_bank.paper_builder', paper_id=paper.id))

    # Available questions for this class and subject
    available_questions = get_questions(
        class_id=paper.class_id,
        subject_id=paper.subject_id,
        status='ACTIVE'
    )

    return render_template(
        'question_bank/paper_builder.html',
        paper=paper,
        available_questions=available_questions
    )


@question_bank_bp.route('/papers/<int:paper_id>/finalize', methods=['POST'])
@login_required
@role_required('Admin', 'Teacher')
def finalize_paper_route(paper_id):
    """Finalizes a QuestionPaper and locks immutable question snapshots."""
    try:
        finalize_question_paper(paper_id)
        flash("🔒 Question paper finalized and locked! Immutable question snapshots saved.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for('question_bank.papers_list'))


@question_bank_bp.route('/papers/<int:paper_id>/duplicate', methods=['POST'])
@login_required
@role_required('Admin', 'Teacher')
def duplicate_paper_route(paper_id):
    """Duplicates a question paper into an independent draft."""
    try:
        new_p = duplicate_question_paper(paper_id, created_by_id=session.get('user_id'))
        flash(f"📋 Duplicated paper into '{new_p.title}'!", "success")
        return redirect(url_for('question_bank.paper_builder', paper_id=new_p.id))
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for('question_bank.papers_list'))


# ==========================================
# 4. PRINTABLE VIEWS (STUDENT PAPER & TEACHER ANSWER KEY)
# ==========================================

@question_bank_bp.route('/papers/<int:paper_id>/view')
@login_required
def view_paper_print(paper_id):
    """Clean, print-formatted student question paper document (0 correct answers exposed)."""
    paper = QuestionPaper.query.get_or_404(paper_id)
    return render_template('question_bank/paper_print.html', paper=paper)


@question_bank_bp.route('/papers/<int:paper_id>/answer-key')
@login_required
@role_required('Admin', 'Teacher')
def view_answer_key_print(paper_id):
    """Teacher-only printable answer key & solution guide. Protected from student access!"""
    user_role = str(session.get('user_role', '')).lower()
    if user_role not in ('admin', 'teacher', 'employee'):
        flash("Unauthorized access to Answer Key.", "danger")
        return redirect(url_for('question_bank.papers_list'))

    paper = QuestionPaper.query.get_or_404(paper_id)
    return render_template('question_bank/answer_key_print.html', paper=paper)
