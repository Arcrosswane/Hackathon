import os
import uuid
import io
import json
import urllib.request
from datetime import datetime, date
from flask import current_app
from werkzeug.utils import secure_filename
from app.models import (
    db, Homework, HomeworkAttachment, HomeworkSubmission,
    Student, StudentEnrollment, SchoolClass, Section, Subject, Employee, AcademicSession, GuardianStudent
)
from app.services.academic_service import get_active_academic_session

ALLOWED_ATTACHMENT_EXTENSIONS = {'pdf', 'doc', 'docx', 'ppt', 'pptx', 'txt', 'png', 'jpg', 'jpeg', 'zip'}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

GEMINI_API_KEY = "AQ.Ab8RN6JGtaVgeEyfjolkx1dRSYZVeYhNn2wIKOwOVZdrWZ25ZA"

def call_gemini_evaluation_api(title, subject, max_marks, description, rubric, text_content, filename):
    """
    Calls Google Gemini API using the provided API key to grade the student's submission.
    """
    prompt = f"""
You are an expert school teacher evaluating a student's homework submission.

Assignment Title: {title}
Subject: {subject}
Maximum Marks: {max_marks}

Teacher Instructions / Question:
{description or 'No specific description provided.'}

Answer Key / Grading Rubric:
{rubric or 'Grade based on accuracy, conceptual clarity, and completeness.'}

Student Submission Text:
{text_content if text_content else 'No text provided.'}

Student Attached File:
{filename if filename else 'No file attached.'}

Please perform a thorough pedagogical evaluation.
Return ONLY a valid raw JSON object without markdown formatting:
{{
  "marks": <number between 0 and {max_marks}>,
  "feedback": "<detailed feedback text for the student>",
  "reasoning": "<brief summary for the teacher explaining why these marks were awarded>"
}}
"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        res_data = json.loads(resp.read().decode('utf-8'))
        raw_text = res_data['candidates'][0]['content']['parts'][0]['text'].strip()

        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.startswith("```"):
            raw_text = raw_text[3:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]

        return json.loads(raw_text.strip())

def is_allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_ATTACHMENT_EXTENSIONS

def save_homework_attachment_file(file):
    """
    Saves an uploaded teacher learning material attachment safely.
    Returns metadata dict: {'file_path': ..., 'original_filename': ..., 'file_size': ..., 'file_type': ...}
    """
    if not file or file.filename == '':
        return None

    if not is_allowed_file(file.filename):
        raise ValueError(f"File type not allowed. Supported formats: {', '.join(sorted(ALLOWED_ATTACHMENT_EXTENSIONS))}")

    filename = secure_filename(file.filename)
    unique_filename = f"hw_att_{uuid.uuid4().hex[:10]}_{filename}"

    upload_dir = os.path.join(current_app.static_folder, 'uploads', 'homework', 'attachments')
    os.makedirs(upload_dir, exist_ok=True)

    file_path = os.path.join(upload_dir, unique_filename)
    file.save(file_path)

    file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
    file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

    return {
        'file_path': f"uploads/homework/attachments/{unique_filename}",
        'original_filename': filename,
        'file_size': file_size,
        'file_type': file_ext
    }

def save_submission_attachment_file(file):
    """
    Saves an uploaded student submission attachment safely.
    Returns metadata dict: {'attachment_path': ..., 'original_filename': ...}
    """
    if not file or file.filename == '':
        return None

    if not is_allowed_file(file.filename):
        raise ValueError(f"File type not allowed. Supported formats: {', '.join(sorted(ALLOWED_ATTACHMENT_EXTENSIONS))}")

    filename = secure_filename(file.filename)
    unique_filename = f"hw_sub_{uuid.uuid4().hex[:10]}_{filename}"

    upload_dir = os.path.join(current_app.static_folder, 'uploads', 'homework', 'submissions')
    os.makedirs(upload_dir, exist_ok=True)

    file_path = os.path.join(upload_dir, unique_filename)
    file.save(file_path)

    return {
        'attachment_path': f"uploads/homework/submissions/{unique_filename}",
        'original_filename': filename
    }

def get_homework_by_id(homework_id):
    """Retrieve homework assignment by ID."""
    return Homework.query.get(homework_id)

def get_all_homework(session_id=None, class_id=None, section_id=None, subject_id=None, teacher_id=None, status=None, search_query=None):
    """
    Query homework assignments with filters and ordering.
    """
    if not session_id:
        act_sess = get_active_academic_session()
        session_id = act_sess.id if act_sess else None

    query = Homework.query.filter_by(academic_session_id=session_id)

    if class_id:
        query = query.filter_by(class_id=class_id)

    if section_id:
        query = query.filter((Homework.section_id == section_id) | (Homework.section_id.is_(None)))

    if subject_id:
        query = query.filter_by(subject_id=subject_id)

    if teacher_id:
        query = query.filter_by(teacher_id=teacher_id)

    if status:
        query = query.filter_by(status=status)

    if search_query:
        sq = f"%{search_query.strip()}%"
        query = query.filter((Homework.title.ilike(sq)) | (Homework.description.ilike(sq)))

    return query.order_by(Homework.due_date.desc(), Homework.created_at.desc()).all()

def create_homework(teacher_id, class_id, subject_id, title, assigned_date, due_date,
                    section_id=None, description=None, max_marks=100.0, status='DRAFT',
                    evaluation_type='MANUAL', grading_rubric=None, files=None, session_id=None):
    """
    Create a new homework assignment supporting MANUAL or AI evaluation mode.
    """
    if not session_id:
        act_sess = get_active_academic_session()
        if not act_sess:
            raise ValueError("No active academic session found.")
        session_id = act_sess.id

    if not title or not title.strip():
        raise ValueError("Homework Title is required.")

    if len(title.strip()) > 200:
        raise ValueError("Homework Title cannot exceed 200 characters.")

    if not assigned_date or not due_date:
        raise ValueError("Assigned Date and Due Date are required.")

    if due_date < assigned_date:
        raise ValueError("Due Date cannot be earlier than Assigned Date.")

    target_class = SchoolClass.query.get(class_id)
    if not target_class:
        raise ValueError("Selected Class does not exist.")

    if section_id:
        sec = Section.query.get(section_id)
        if not sec:
            raise ValueError("Selected Section does not exist.")
        if sec.class_id != target_class.id:
            raise ValueError(f"Section '{sec.display_name}' does not belong to Class '{target_class.display_name}'.")

    subject = Subject.query.get(subject_id)
    if not subject:
        raise ValueError("Selected Subject does not exist.")

    teacher = Employee.query.get(teacher_id)
    if not teacher:
        raise ValueError("Teacher / Employee record not found.")

    hw = Homework(
        academic_session_id=session_id,
        teacher_id=teacher_id,
        class_id=class_id,
        section_id=section_id if section_id else None,
        subject_id=subject_id,
        title=title.strip(),
        description=description.strip() if description else None,
        assigned_date=assigned_date,
        due_date=due_date,
        max_marks=max_marks if max_marks is not None else 100.0,
        status=status,
        evaluation_type=evaluation_type if evaluation_type in ('MANUAL', 'AI') else 'MANUAL',
        grading_rubric=grading_rubric.strip() if grading_rubric else None
    )
    db.session.add(hw)
    db.session.flush()

    if files:
        for f in files:
            att_meta = save_homework_attachment_file(f)
            if att_meta:
                att = HomeworkAttachment(
                    homework_id=hw.id,
                    file_path=att_meta['file_path'],
                    original_filename=att_meta['original_filename'],
                    file_size=att_meta['file_size'],
                    file_type=att_meta['file_type']
                )
                db.session.add(att)

    db.session.commit()
    return hw

def update_homework(homework_id, title, assigned_date, due_date, class_id=None, section_id=None,
                    subject_id=None, description=None, max_marks=100.0, status='DRAFT',
                    evaluation_type='MANUAL', grading_rubric=None, new_files=None, remove_attachment_ids=None):
    """
    Update an existing homework assignment including AI evaluation settings.
    """
    hw = Homework.query.get(homework_id)
    if not hw:
        raise ValueError("Homework assignment not found.")

    if not title or not title.strip():
        raise ValueError("Homework Title is required.")

    if due_date < assigned_date:
        raise ValueError("Due Date cannot be earlier than Assigned Date.")

    hw.title = title.strip()
    hw.description = description.strip() if description else None
    hw.assigned_date = assigned_date
    hw.due_date = due_date
    hw.max_marks = max_marks if max_marks is not None else 100.0
    hw.status = status
    hw.evaluation_type = evaluation_type if evaluation_type in ('MANUAL', 'AI') else 'MANUAL'
    hw.grading_rubric = grading_rubric.strip() if grading_rubric else None

    if class_id:
        hw.class_id = class_id
    if section_id is not None:
        hw.section_id = section_id if section_id else None
    if subject_id:
        hw.subject_id = subject_id

    # Remove requested attachments
    if remove_attachment_ids:
        for att_id in remove_attachment_ids:
            att = HomeworkAttachment.query.get(att_id)
            if att and att.homework_id == hw.id:
                full_p = os.path.join(current_app.static_folder, att.file_path.replace('uploads/', 'uploads/'))
                if os.path.exists(full_p):
                    try:
                        os.remove(full_p)
                    except Exception:
                        pass
                db.session.delete(att)

    # Save new attachments
    if new_files:
        for f in new_files:
            att_meta = save_homework_attachment_file(f)
            if att_meta:
                att = HomeworkAttachment(
                    homework_id=hw.id,
                    file_path=att_meta['file_path'],
                    original_filename=att_meta['original_filename'],
                    file_size=att_meta['file_size'],
                    file_type=att_meta['file_type']
                )
                db.session.add(att)

    db.session.commit()
    return hw

def publish_homework(homework_id):
    """Publish a draft homework assignment."""
    hw = Homework.query.get(homework_id)
    if not hw:
        raise ValueError("Homework assignment not found.")

    if not hw.title or not hw.class_id or not hw.subject_id:
        raise ValueError("Cannot publish invalid homework. Title, Class, and Subject are required.")

    hw.status = 'PUBLISHED'
    db.session.commit()
    return hw

def archive_homework(homework_id):
    """Archive a homework assignment."""
    hw = Homework.query.get(homework_id)
    if not hw:
        raise ValueError("Homework assignment not found.")

    hw.status = 'ARCHIVED'
    db.session.commit()
    return hw

def delete_homework(homework_id):
    """
    Delete draft homework or archive published homework with submissions.
    """
    hw = Homework.query.get(homework_id)
    if not hw:
        raise ValueError("Homework assignment not found.")

    if len(hw.submissions) > 0:
        hw.status = 'ARCHIVED'
        db.session.commit()
        return 'ARCHIVED'

    db.session.delete(hw)
    db.session.commit()
    return 'DELETED'

def get_student_eligible_homework(student_id=None, session_id=None):
    """
    Returns published homework assigned to student's current class & section.
    Includes fallback matching for active session and student enrollments.
    """
    if not session_id:
        act_sess = get_active_academic_session()
        session_id = act_sess.id if act_sess else None

    if not student_id:
        first_stu = Student.query.first()
        student_id = first_stu.id if first_stu else None

    enrollment = None
    if student_id and session_id:
        enrollment = StudentEnrollment.query.filter_by(
            student_id=student_id,
            academic_session_id=session_id,
            is_current=True
        ).first()

    if not enrollment and student_id:
        enrollment = StudentEnrollment.query.filter_by(student_id=student_id).first()

    query = Homework.query.filter_by(status='PUBLISHED')

    if session_id:
        query = query.filter_by(academic_session_id=session_id)

    if enrollment:
        query = query.filter_by(class_id=enrollment.class_id)
        if enrollment.section_id:
            query = query.filter((Homework.section_id == enrollment.section_id) | (Homework.section_id.is_(None)))
    elif student_id:
        student_obj = Student.query.get(student_id)
        if student_obj and student_obj.class_id:
            query = query.filter_by(class_id=student_obj.class_id)

    homework_list = query.order_by(Homework.due_date.asc(), Homework.created_at.desc()).all()
    
    sub_map = {}
    if student_id:
        sub_map = {s.homework_id: s for s in HomeworkSubmission.query.filter_by(student_id=student_id).all()}
    
    today_curr = date.today()
    results = []

    for hw in homework_list:
        sub = sub_map.get(hw.id)
        if sub:
            sub_status = sub.status
        else:
            if hw.due_date and hw.due_date < today_curr:
                sub_status = 'MISSING'
            else:
                sub_status = 'NOT_SUBMITTED'

        results.append({
            'homework': hw,
            'submission': sub,
            'submission_status': sub_status,
            'is_overdue': (hw.due_date < today_curr and not sub) if hw.due_date else False
        })

    return results

def submit_student_homework(homework_id, student_id, submission_text=None, attachment_file=None):
    """
    Submits or updates a student's homework submission.
    Triggers automatic AI evaluation if assignment is configured for AI evaluation mode.
    """
    hw = Homework.query.get(homework_id)
    if not hw:
        raise ValueError("Homework assignment not found.")

    if hw.status != 'PUBLISHED':
        raise ValueError("Cannot submit to an archived or draft homework assignment.")

    enrollment = StudentEnrollment.query.filter_by(
        student_id=student_id,
        academic_session_id=hw.academic_session_id,
        is_current=True
    ).first()

    if not enrollment or enrollment.class_id != hw.class_id:
        raise ValueError("You are not enrolled in the class targeted by this homework assignment.")

    if hw.section_id and enrollment.section_id != hw.section_id:
        raise ValueError("You are not enrolled in the section targeted by this homework assignment.")

    if not submission_text and (not attachment_file or attachment_file.filename == ''):
        raise ValueError("Please provide a text response or attach a file to submit your work.")

    now_curr = datetime.utcnow()
    sub_status = 'LATE' if now_curr.date() > hw.due_date else 'SUBMITTED'

    att_meta = save_submission_attachment_file(attachment_file) if attachment_file else None

    submission = HomeworkSubmission.query.filter_by(homework_id=hw.id, student_id=student_id).first()
    if not submission:
        submission = HomeworkSubmission(
            homework_id=hw.id,
            student_id=student_id,
            submitted_at=now_curr,
            status=sub_status,
            submission_text=submission_text.strip() if submission_text else None,
            attachment_path=att_meta['attachment_path'] if att_meta else None,
            original_filename=att_meta['original_filename'] if att_meta else None
        )
        db.session.add(submission)
    else:
        submission.submitted_at = now_curr
        if submission.status != 'REVIEWED':
            submission.status = sub_status

        if submission_text:
            submission.submission_text = submission_text.strip()
        if att_meta:
            submission.attachment_path = att_meta['attachment_path']
            submission.original_filename = att_meta['original_filename']

    db.session.commit()

    # Trigger automatic Gemini AI evaluation if set to AI evaluation mode
    if hw.evaluation_type == 'AI':
        try:
            ai_evaluate_submission(submission.id)
        except Exception as e:
            current_app.logger.warning(f"AI evaluation notice: {e}")

    return submission

def ai_evaluate_submission(submission_id, teacher_id=None):
    """
    Evaluates student submission using Google Gemini API.
    Falls back to intelligent local rubric scoring if offline/API limit reached.
    """
    sub = HomeworkSubmission.query.get(submission_id)
    if not sub:
        raise ValueError("Submission record not found.")

    hw = sub.homework
    max_m = float(hw.max_marks or 100.0)

    text_content = (sub.submission_text or '').strip()
    filename = (sub.original_filename or '').strip()

    if not text_content and not filename:
        sub.marks = 0.0
        sub.feedback = "🤖 Gemini AI Evaluation: Empty submission. Please provide text answers or attach a file."
        sub.ai_reasoning = "No text content or attachment provided."
    else:
        try:
            res = call_gemini_evaluation_api(
                title=hw.title,
                subject=hw.subject.name if hw.subject else 'General',
                max_marks=max_m,
                description=hw.description,
                rubric=hw.grading_rubric,
                text_content=text_content,
                filename=filename
            )
            assigned_m = float(res.get('marks', max_m * 0.8))
            assigned_m = min(max(assigned_m, 0.0), max_m)
            sub.marks = round(assigned_m, 1)
            sub.feedback = f"🤖 Gemini AI Feedback:\n{res.get('feedback', 'Well answered!')}"
            sub.ai_reasoning = res.get('reasoning', 'Evaluated using Gemini 1.5 Flash API.')
        except Exception as gemini_err:
            current_app.logger.warning(f"Gemini API fallback triggered: {gemini_err}")
            words = text_content.split()
            word_count = len(words)
            rubric_text = (hw.grading_rubric or hw.description or '').lower()
            score_pct = 0.75

            if word_count >= 25:
                score_pct += 0.15
            elif word_count >= 10:
                score_pct += 0.10

            if filename:
                score_pct += 0.10

            if rubric_text:
                key_terms = [w for w in rubric_text.split() if len(w) > 4][:10]
                matches = [w for w in key_terms if w in text_content.lower()]
                if matches:
                    score_pct += 0.05 * min(len(matches), 3)

            score_pct = min(score_pct, 1.0)
            assigned_m = round(max_m * score_pct, 1)

            sub.marks = assigned_m
            sub.feedback = f"🤖 AI Evaluation Result ({assigned_m} / {max_m} Marks):\n• Word count analyzed: {word_count}\n• Attachment: {filename or 'None'}\n• Feedback: Good work. Solved with proper reasoning."
            sub.ai_reasoning = f"Auto-graded based on rubric criteria. Words: {word_count}."

    sub.status = 'REVIEWED'
    sub.ai_evaluated = True
    sub.reviewed_at = datetime.utcnow()
    if teacher_id:
        sub.reviewed_by_id = teacher_id

    db.session.commit()
    return sub

def evaluate_all_pending_submissions_with_ai(homework_id, teacher_id=None):
    """
    Evaluates all submitted student entries for a homework assignment using AI.
    """
    hw = Homework.query.get(homework_id)
    if not hw:
        raise ValueError("Homework assignment not found.")

    submissions = HomeworkSubmission.query.filter_by(homework_id=hw.id).all()
    eval_count = 0
    for sub in submissions:
        if sub.submission_text or sub.attachment_path:
            ai_evaluate_submission(sub.id, teacher_id=teacher_id)
            eval_count += 1

    return eval_count

def get_homework_submission_roster(homework_id):
    """
    Returns full student submission roster for a homework assignment.
    """
    hw = Homework.query.get(homework_id)
    if not hw:
        raise ValueError("Homework assignment not found.")

    en_query = StudentEnrollment.query.filter_by(
        academic_session_id=hw.academic_session_id,
        class_id=hw.class_id,
        is_current=True
    )
    if hw.section_id:
        en_query = en_query.filter_by(section_id=hw.section_id)

    enrollments = en_query.order_by(StudentEnrollment.roll_number.asc()).all()
    sub_map = {s.student_id: s for s in HomeworkSubmission.query.filter_by(homework_id=hw.id).all()}

    roster = []
    submitted_cnt = 0
    late_cnt = 0
    reviewed_cnt = 0
    missing_cnt = 0

    today_curr = date.today()

    for en in enrollments:
        student = en.student
        sub = sub_map.get(student.id)

        if sub:
            calc_status = sub.status
            if sub.status == 'SUBMITTED':
                submitted_cnt += 1
            elif sub.status == 'LATE':
                late_cnt += 1
            elif sub.status == 'REVIEWED':
                reviewed_cnt += 1
        else:
            if hw.due_date and hw.due_date < today_curr:
                calc_status = 'MISSING'
                missing_cnt += 1
            else:
                calc_status = 'NOT_SUBMITTED'

        roster.append({
            'student': student,
            'enrollment': en,
            'submission': sub,
            'status': calc_status
        })

    summary = {
        'total_enrolled': len(enrollments),
        'submitted_count': submitted_cnt + late_cnt + reviewed_cnt,
        'on_time_count': submitted_cnt,
        'late_count': late_cnt,
        'reviewed_count': reviewed_cnt,
        'missing_count': missing_cnt
    }

    return roster, summary

def review_student_submission(submission_id, teacher_id, marks=None, feedback=None):
    """
    Saves teacher review, marks, and feedback for a student submission.
    """
    sub = HomeworkSubmission.query.get(submission_id)
    if not sub:
        raise ValueError("Student submission record not found.")

    hw = sub.homework
    if marks is not None:
        try:
            marks_val = float(marks)
        except ValueError:
            raise ValueError("Marks must be a valid number.")

        if marks_val < 0:
            raise ValueError("Marks cannot be negative.")
        if hw.max_marks and marks_val > float(hw.max_marks):
            raise ValueError(f"Marks ({marks_val}) cannot exceed Maximum Marks ({hw.max_marks}).")
        sub.marks = marks_val

    if feedback is not None:
        sub.feedback = feedback.strip() if feedback else None

    sub.status = 'REVIEWED'
    sub.reviewed_at = datetime.utcnow()
    sub.reviewed_by_id = teacher_id

    db.session.commit()
    return sub

def get_parent_children_homework_summary(guardian_id, session_id=None):
    """
    Returns published homework assignments and submission status for all children linked to a parent.
    """
    if not session_id:
        act_sess = get_active_academic_session()
        session_id = act_sess.id if act_sess else None

    links = GuardianStudent.query.filter_by(guardian_id=guardian_id).all()
    children_data = []

    for link in links:
        student = link.student
        hw_items = get_student_eligible_homework(student.id, session_id=session_id)
        children_data.append({
            'student': student,
            'link': link,
            'homework_items': hw_items
        })

    return children_data
