import json
from datetime import datetime
from app.models import db, Question, QuestionPaper, QuestionPaperSection, QuestionPaperQuestion, SchoolClass, Subject, User, School
from app.services.academic_service import get_active_academic_session

VALID_QUESTION_TYPES = {'MCQ', 'SHORT_ANSWER', 'LONG_ANSWER', 'VERY_SHORT_ANSWER', 'TRUE_FALSE', 'FILL_IN_THE_BLANK', 'CASE_BASED', 'NUMERICAL'}
VALID_DIFFICULTIES = {'EASY', 'MEDIUM', 'HARD'}

def create_question(class_id, subject_id, question_text, question_type="MCQ", difficulty="MEDIUM", marks=1.0, chapter=None, topic=None, option_a=None, option_b=None, option_c=None, option_d=None, correct_option=None, answer_text=None, explanation=None, tags=None, visibility="SCHOOL_SHARED", created_by_id=None, school_id=None):
    """
    Creates a new question entry in the Question Bank.
    """
    if not question_text or not question_text.strip():
        raise ValueError("Question text cannot be empty.")

    q_type = str(question_type).upper().strip()
    if q_type not in VALID_QUESTION_TYPES:
        raise ValueError(f"Invalid question type '{q_type}'. Supported: {', '.join(sorted(VALID_QUESTION_TYPES))}")

    diff = str(difficulty).upper().strip()
    if diff not in VALID_DIFFICULTIES:
        raise ValueError(f"Invalid difficulty '{diff}'. Supported: {', '.join(sorted(VALID_DIFFICULTIES))}")

    if q_type == 'MCQ':
        if not option_a or not option_b:
            raise ValueError("MCQ questions require at least Option A and Option B.")
        if correct_option and str(correct_option).upper() not in ('A', 'B', 'C', 'D'):
            raise ValueError("Correct option for MCQ must be A, B, C, or D.")

    if not school_id:
        sch = School.query.first()
        school_id = sch.id if sch else 1

    try:
        q = Question(
            institute_id=school_id,
            class_id=class_id,
            subject_id=subject_id,
            chapter=chapter.strip() if chapter else None,
            topic=topic.strip() if topic else None,
            question_text=question_text.strip(),
            question_type=q_type,
            difficulty=diff,
            marks=float(marks) if marks else 1.0,
            option_a=option_a.strip() if option_a else None,
            option_b=option_b.strip() if option_b else None,
            option_c=option_c.strip() if option_c else None,
            option_d=option_d.strip() if option_d else None,
            correct_option=str(correct_option).upper().strip() if correct_option else None,
            answer_text=answer_text.strip() if answer_text else None,
            explanation=explanation.strip() if explanation else None,
            tags=tags.strip() if tags else None,
            visibility=visibility,
            status='ACTIVE',
            created_by_id=created_by_id
        )
        db.session.add(q)
        db.session.commit()
        return q
    except Exception as e:
        db.session.rollback()
        raise e


def update_question(question_id, **kwargs):
    """
    Edits an existing question in the Question Bank.
    """
    q = Question.query.get(question_id)
    if not q:
        raise ValueError("Question not found.")

    if 'question_text' in kwargs and kwargs['question_text']:
        q.question_text = kwargs['question_text'].strip()

    if 'question_type' in kwargs and kwargs['question_type']:
        q_type = str(kwargs['question_type']).upper().strip()
        if q_type in VALID_QUESTION_TYPES:
            q.question_type = q_type

    if 'difficulty' in kwargs and kwargs['difficulty']:
        diff = str(kwargs['difficulty']).upper().strip()
        if diff in VALID_DIFFICULTIES:
            q.difficulty = diff

    if 'marks' in kwargs and kwargs['marks'] is not None:
        q.marks = float(kwargs['marks'])

    for field in ('chapter', 'topic', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_option', 'answer_text', 'explanation', 'tags', 'visibility', 'class_id', 'subject_id'):
        if field in kwargs:
            val = kwargs[field]
            setattr(q, field, val.strip() if isinstance(val, str) else val)

    q.updated_at = datetime.utcnow()
    db.session.commit()
    return q


def archive_question(question_id):
    """
    Archives a question so it no longer appears in new searches while preserving references.
    """
    q = Question.query.get(question_id)
    if not q:
        raise ValueError("Question not found.")
    q.status = 'ARCHIVED'
    db.session.commit()
    return q


def delete_question(question_id):
    """
    Permanently deletes a question from the Question Bank.
    """
    q = Question.query.get(question_id)
    if not q:
        raise ValueError("Question not found.")

    QuestionPaperQuestion.query.filter_by(question_id=q.id, question_snapshot_json=None).delete(synchronize_session=False)
    db.session.delete(q)
    db.session.commit()
    return True


def delete_question_bank(class_id, subject_id):
    """
    Deletes an entire Question Bank for a specific Class & Subject.
    """
    query = Question.query.filter_by(class_id=class_id, subject_id=subject_id)
    q_ids = [q.id for q in query.all()]
    count = len(q_ids)
    if q_ids:
        QuestionPaperQuestion.query.filter(QuestionPaperQuestion.question_id.in_(q_ids))\
                                   .filter(QuestionPaperQuestion.question_snapshot_json.is_(None))\
                                   .delete(synchronize_session=False)
        query.delete(synchronize_session=False)
        db.session.commit()
    return count


def delete_question_paper(paper_id):
    """
    Deletes a QuestionPaper and its sections/links.
    """
    p = QuestionPaper.query.get(paper_id)
    if not p:
        raise ValueError("Question Paper not found.")
    db.session.delete(p)
    db.session.commit()
    return True


def get_questions(class_id=None, subject_id=None, chapter=None, difficulty=None, question_type=None, search_query=None, status='ACTIVE', user_id=None):
    """
    Queries and filters questions from the Question Bank.
    """
    query = Question.query

    if status:
        query = query.filter_by(status=status)
    if class_id:
        query = query.filter_by(class_id=class_id)
    if subject_id:
        query = query.filter_by(subject_id=subject_id)
    if chapter:
        query = query.filter(Question.chapter.ilike(f"%{chapter}%"))
    if difficulty:
        query = query.filter_by(difficulty=difficulty)
    if question_type:
        query = query.filter_by(question_type=question_type)
    if search_query:
        search_term = f"%{search_query}%"
        query = query.filter((Question.question_text.ilike(search_term)) | (Question.tags.ilike(search_term)) | (Question.chapter.ilike(search_term)))

    return query.order_by(Question.created_at.desc()).all()


def create_question_paper(title, class_id, subject_id, instructions=None, duration_minutes=90, created_by_id=None, session_id=None):
    """
    Initializes a new QuestionPaper draft with default sections (Section A, Section B).
    """
    if not title or not title.strip():
        raise ValueError("Question paper title is required.")

    if not session_id:
        act_sess = get_active_academic_session()
        session_id = act_sess.id if act_sess else None

    sch = School.query.first()
    school_id = sch.id if sch else 1

    paper = QuestionPaper(
        institute_id=school_id,
        academic_session_id=session_id,
        class_id=class_id,
        subject_id=subject_id,
        title=title.strip(),
        instructions=instructions.strip() if instructions else "1. All questions are compulsory. 2. Read each question carefully before answering.",
        duration_minutes=int(duration_minutes) if duration_minutes else 90,
        total_marks=0.0,
        status='DRAFT',
        created_by_id=created_by_id
    )
    db.session.add(paper)
    db.session.flush()

    # Create default sections: Section A (MCQs / Short), Section B (Long Answers)
    sec_a = QuestionPaperSection(
        paper_id=paper.id,
        section_name="Section A",
        section_instructions="Objective & Multiple Choice Questions",
        section_order=1,
        total_section_marks=0.0
    )
    sec_b = QuestionPaperSection(
        paper_id=paper.id,
        section_name="Section B",
        section_instructions="Short & Long Answer Questions",
        section_order=2,
        total_section_marks=0.0
    )
    db.session.add_all([sec_a, sec_b])
    db.session.commit()
    return paper


def add_question_to_paper_section(section_id, question_id, marks=None):
    """
    Attaches a Question from the Question Bank into a QuestionPaperSection.
    """
    sec = QuestionPaperSection.query.get(section_id)
    if not sec:
        raise ValueError("Paper section not found.")

    q = Question.query.get(question_id)
    if not q:
        raise ValueError("Question not found.")

    # Calculate question order
    current_count = QuestionPaperQuestion.query.filter_by(section_id=sec.id).count()

    q_marks = float(marks) if marks is not None else float(q.marks)

    qpq = QuestionPaperQuestion(
        section_id=sec.id,
        question_id=q.id,
        question_order=current_count + 1,
        marks=q_marks
    )
    db.session.add(qpq)
    db.session.flush()

    recalculate_paper_totals(sec.paper_id)
    db.session.commit()
    return qpq


def remove_question_from_paper(paper_question_id):
    """
    Removes a question link from a paper section.
    """
    qpq = QuestionPaperQuestion.query.get(paper_question_id)
    if not qpq:
        raise ValueError("Paper question not found.")
    
    paper_id = qpq.section.paper_id
    db.session.delete(qpq)
    db.session.flush()

    recalculate_paper_totals(paper_id)
    db.session.commit()


def recalculate_paper_totals(paper_id):
    """
    Calculates total marks for each section and the overall paper.
    """
    paper = QuestionPaper.query.get(paper_id)
    if not paper:
        return 0.0

    grand_total = 0.0

    for sec in paper.sections:
        sec_total = 0.0
        for pq in sec.paper_questions:
            sec_total += float(pq.marks or 0.0)
        sec.total_section_marks = sec_total
        grand_total += sec_total

    paper.total_marks = grand_total
    return grand_total


def finalize_question_paper(paper_id):
    """
    Finalizes a QuestionPaper. Serializes immutable JSON snapshots for all included questions
    into `QuestionPaperQuestion.question_snapshot_json` so future edits in the Question Bank
    never rewrite historical exam papers!
    """
    paper = QuestionPaper.query.get(paper_id)
    if not paper:
        raise ValueError("Question paper not found.")

    if not paper.sections or sum(len(s.paper_questions) for s in paper.sections) == 0:
        raise ValueError("Cannot finalize an empty question paper. Add at least one question.")

    recalculate_paper_totals(paper.id)

    # Serialize immutable snapshots
    for sec in paper.sections:
        for pq in sec.paper_questions:
            if pq.question:
                snap = pq.question.to_dict()
                snap['paper_marks'] = pq.marks # Snapshot specific marks used in paper
                pq.question_snapshot_json = json.dumps(snap)

    paper.status = 'FINAL'
    paper.updated_at = datetime.utcnow()
    db.session.commit()
    return paper


def duplicate_question_paper(paper_id, created_by_id=None):
    """
    Clones an existing question paper into an independent DRAFT paper.
    """
    orig_paper = QuestionPaper.query.get(paper_id)
    if not orig_paper:
        raise ValueError("Original question paper not found.")

    new_paper = QuestionPaper(
        institute_id=orig_paper.institute_id,
        academic_session_id=orig_paper.academic_session_id,
        class_id=orig_paper.class_id,
        subject_id=orig_paper.subject_id,
        title=f"Copy of {orig_paper.title}",
        instructions=orig_paper.instructions,
        duration_minutes=orig_paper.duration_minutes,
        total_marks=orig_paper.total_marks,
        status='DRAFT',
        created_by_id=created_by_id or orig_paper.created_by_id
    )
    db.session.add(new_paper)
    db.session.flush()

    for orig_sec in orig_paper.sections:
        new_sec = QuestionPaperSection(
            paper_id=new_paper.id,
            section_name=orig_sec.section_name,
            section_instructions=orig_sec.section_instructions,
            section_order=orig_sec.section_order,
            total_section_marks=orig_sec.total_section_marks
        )
        db.session.add(new_sec)
        db.session.flush()

        for orig_pq in orig_sec.paper_questions:
            new_pq = QuestionPaperQuestion(
                section_id=new_sec.id,
                question_id=orig_pq.question_id,
                question_order=orig_pq.question_order,
                marks=orig_pq.marks,
                question_snapshot_json=orig_pq.question_snapshot_json
            )
            db.session.add(new_pq)

    db.session.commit()
    return new_paper
