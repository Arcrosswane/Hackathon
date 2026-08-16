import json
import csv
import io
from datetime import datetime, date, time
from app.models import (
    db, Examination, ExaminationClass, ExaminationSubject,
    ExaminationResult, ExamOverallResult, ExamType, GradeRule,
    QuestionPaper, SchoolClass, Section, Subject, Student, User, School, AcademicSession
)
from app.services.academic_service import get_active_academic_session
from app.services.ai_question_service import _call_gemini_api

# ==========================================
# 1. EXAM TYPES & GRADE RULES CONFIGURATION
# ==========================================

def get_exam_types(active_only=True):
    """Returns configured exam types (Unit Test, Half Yearly, etc.)."""
    query = ExamType.query
    if active_only:
        query = query.filter_by(is_active=True)
    return query.order_by(ExamType.name.asc()).all()


def create_exam_type(name, code=None, description=None):
    """Creates a new exam type configuration."""
    if not name or not name.strip():
        raise ValueError("Exam type name is required.")
    
    sch = School.query.first()
    school_id = sch.id if sch else 1

    et = ExamType(
        institute_id=school_id,
        name=name.strip(),
        code=code.strip().upper() if code else None,
        description=description.strip() if description else None
    )
    db.session.add(et)
    db.session.commit()
    return et


def delete_exam_type(exam_type_id):
    """Deletes an exam type if not currently referenced by an active examination."""
    et = ExamType.query.get(exam_type_id)
    if not et:
        raise ValueError("Exam Type not found.")
    
    linked_exams = Examination.query.filter_by(exam_type_id=exam_type_id).count()
    if linked_exams > 0:
        raise ValueError(f"Cannot delete Exam Type '{et.name}' because it is linked to {linked_exams} examination(s).")
    
    db.session.delete(et)
    db.session.commit()
    return True


def delete_grade_rule(grade_rule_id):
    """Deletes a grade rule."""
    gr = GradeRule.query.get(grade_rule_id)
    if not gr:
        raise ValueError("Grade Rule not found.")
    
    db.session.delete(gr)
    db.session.commit()
    return True


def get_grade_rules(active_only=True):
    """Returns active grading scale rules ordered by min_percentage DESC."""
    query = GradeRule.query
    if active_only:
        query = query.filter_by(is_active=True)
    rules = query.order_by(GradeRule.min_percentage.desc()).all()
    
    # If no rules exist in database, seed default CBSE 9-Point Grading Scale
    if not rules:
        default_rules = [
            ("A1", 91.0, 100.0, "Top 1/8th of passed candidates"),
            ("A2", 81.0, 90.99, "Next 1/8th of passed candidates"),
            ("B1", 71.0, 80.99, "Next 1/8th of passed candidates"),
            ("B2", 61.0, 70.99, "Next 1/8th of passed candidates"),
            ("C1", 51.0, 60.99, "Next 1/8th of passed candidates"),
            ("C2", 41.0, 50.99, "Next 1/8th of passed candidates"),
            ("D",  33.0, 40.99, "Pass Grade"),
            ("E",   0.0, 32.99, "Needs Improvement / Essential Repeat")
        ]
        sch = School.query.first()
        school_id = sch.id if sch else 1
        for gr_name, min_p, max_p, desc in default_rules:
            gr = GradeRule(
                institute_id=school_id,
                name="CBSE Standard",
                grade=gr_name,
                min_percentage=min_p,
                max_percentage=max_p,
                description=desc
            )
            db.session.add(gr)
        db.session.commit()
        rules = GradeRule.query.order_by(GradeRule.min_percentage.desc()).all()
        
    return rules


def calculate_grade_from_percentage(percentage):
    """Calculates grade based on active GradeRule configuration."""
    if percentage is None:
        return "N/A"
    
    rules = get_grade_rules(active_only=True)
    pct = float(percentage)
    
    for r in rules:
        if r.min_percentage <= pct <= r.max_percentage:
            return r.grade
    
    if pct >= 90:
        return "A1"
    elif pct >= 80:
        return "A2"
    elif pct >= 70:
        return "B1"
    elif pct >= 60:
        return "B2"
    elif pct >= 50:
        return "C1"
    elif pct >= 40:
        return "C2"
    elif pct >= 33:
        return "D"
    return "E"


# ==========================================
# 2. EXAMINATION CRUD & SETUP
# ==========================================

def create_examination(name, academic_session_id=None, exam_type_id=None, description=None, start_date=None, end_date=None, created_by_id=None):
    """Creates a new Examination master record."""
    if not name or not name.strip():
        raise ValueError("Examination name is required.")

    if not academic_session_id:
        act_sess = get_active_academic_session()
        academic_session_id = act_sess.id if act_sess else None
        if not academic_session_id:
            raise ValueError("Active Academic Session is required to create an Examination.")

    sch = School.query.first()
    school_id = sch.id if sch else 1

    exam = Examination(
        institute_id=school_id,
        academic_session_id=academic_session_id,
        exam_type_id=exam_type_id,
        name=name.strip(),
        description=description.strip() if description else None,
        start_date=start_date,
        end_date=end_date,
        status="DRAFT",
        created_by_id=created_by_id
    )
    db.session.add(exam)
    db.session.commit()
    return exam


def update_examination(exam_id, name=None, exam_type_id=None, description=None, start_date=None, end_date=None, status=None):
    """Updates an examination master record."""
    exam = Examination.query.get(exam_id)
    if not exam:
        raise ValueError("Examination not found.")

    if name and name.strip():
        exam.name = name.strip()
    if exam_type_id is not None:
        exam.exam_type_id = exam_type_id
    if description is not None:
        exam.description = description.strip() if description else None
    if start_date is not None:
        exam.start_date = start_date
    if end_date is not None:
        exam.end_date = end_date
    if status and status in ('DRAFT', 'SCHEDULED', 'ONGOING', 'COMPLETED', 'RESULT_PUBLISHED', 'ARCHIVED'):
        exam.status = status

    db.session.commit()
    return exam


def delete_examination(exam_id):
    """Deletes an examination master record along with all associated subjects, results, and classes."""
    exam = Examination.query.get(exam_id)
    if not exam:
        raise ValueError("Examination not found.")
    
    db.session.delete(exam)
    db.session.commit()
    return True


def get_examinations(session_id=None, status=None, class_id=None, search_query=None):
    """Retrieves and filters examinations."""
    query = Examination.query

    if not session_id:
        act_sess = get_active_academic_session()
        session_id = act_sess.id if act_sess else None

    if session_id:
        query = query.filter_by(academic_session_id=session_id)
    if status:
        query = query.filter_by(status=status)
    if class_id:
        query = query.join(ExaminationClass).filter(ExaminationClass.class_id == class_id)
    if search_query:
        term = f"%{search_query}%"
        query = query.filter((Examination.name.ilike(term)) | (Examination.description.ilike(term)))

    return query.order_by(Examination.created_at.desc()).all()


def assign_classes_to_exam(exam_id, class_ids):
    """Assigns one or more classes to an examination."""
    exam = Examination.query.get(exam_id)
    if not exam:
        raise ValueError("Examination not found.")

    # Remove existing class assignments not in new class_ids
    ExaminationClass.query.filter_by(examination_id=exam_id).delete()
    
    for c_id in class_ids:
        if c_id:
            ec = ExaminationClass(
                examination_id=exam_id,
                class_id=int(c_id)
            )
            db.session.add(ec)

    if exam.status == "DRAFT":
        exam.status = "SCHEDULED"

    db.session.commit()
    return exam


def add_exam_subject(exam_id, class_id, subject_id, exam_date=None, start_time=None, end_time=None, max_marks=100.0, pass_marks=33.0, section_id=None, question_paper_id=None):
    """Adds or schedules a subject within an examination for a class."""
    exam = Examination.query.get(exam_id)
    if not exam:
        raise ValueError("Examination not found.")

    if not class_id or not subject_id:
        raise ValueError("Class and Subject are required for exam subject scheduling.")

    if float(max_marks) <= 0:
        raise ValueError("Maximum marks must be greater than 0.")
    if float(pass_marks) < 0 or float(pass_marks) > float(max_marks):
        raise ValueError("Passing marks must be between 0 and maximum marks.")

    # Check duplicate subject assignment for class/section
    existing = ExaminationSubject.query.filter_by(
        examination_id=exam_id,
        class_id=class_id,
        subject_id=subject_id,
        section_id=section_id
    ).first()

    if existing:
        es = existing
        es.exam_date = exam_date
        es.start_time = start_time
        es.end_time = end_time
        es.max_marks = float(max_marks)
        es.pass_marks = float(pass_marks)
        if question_paper_id is not None:
            es.question_paper_id = question_paper_id
    else:
        es = ExaminationSubject(
            examination_id=exam_id,
            class_id=class_id,
            section_id=section_id,
            subject_id=subject_id,
            exam_date=exam_date,
            start_time=start_time,
            end_time=end_time,
            max_marks=float(max_marks),
            pass_marks=float(pass_marks),
            question_paper_id=question_paper_id,
            status="SCHEDULED"
        )
        db.session.add(es)

    db.session.commit()
    return es


# ==========================================
# 3. MODULE 15 QUESTION PAPER INTEGRATION & CONFLICT DETECTION
# ==========================================

def attach_question_paper_to_exam_subject(exam_subject_id, paper_id):
    """
    Attaches a Question Paper from Module 15 to an Examination Subject after validating compatibility.
    Returns: (es, warning_message or None)
    """
    es = ExaminationSubject.query.get(exam_subject_id)
    if not es:
        raise ValueError("Exam Subject schedule record not found.")

    if not paper_id:
        es.question_paper_id = None
        db.session.commit()
        return es, None

    paper = QuestionPaper.query.get(paper_id)
    if not paper:
        raise ValueError("Question Paper not found.")

    # Validate class and subject compatibility
    if paper.class_id != es.class_id:
        raise ValueError(f"Question Paper Class (Grade {paper.school_class.display_name if paper.school_class else paper.class_id}) does not match Exam Subject Class (Grade {es.school_class.display_name if es.school_class else es.class_id}).")

    if paper.subject_id != es.subject_id:
        raise ValueError(f"Question Paper Subject ({paper.subject.name if paper.subject else paper.subject_id}) does not match Exam Subject ({es.subject.name if es.subject else es.subject_id}).")

    warning_msg = None
    if paper.total_marks > 0 and abs(paper.total_marks - es.max_marks) > 0.01:
        warning_msg = f"⚠️ Total Marks Mismatch: Attached Question Paper has total marks {paper.total_marks}, but Exam Subject Maximum Marks is set to {es.max_marks}."

    es.question_paper_id = paper.id
    db.session.commit()
    return es, warning_msg


def check_schedule_conflicts(class_id, exam_date, start_time, end_time, exclude_subject_id=None):
    """
    Detects if there are overlapping exam schedules for the same class on the same date/time.
    """
    if not class_id or not exam_date or not start_time or not end_time:
        return []

    conflicts = []
    same_day_exams = ExaminationSubject.query.filter_by(class_id=class_id, exam_date=exam_date).all()

    for item in same_day_exams:
        if exclude_subject_id and item.id == exclude_subject_id:
            continue
        if item.start_time and item.end_time:
            # Overlap check: (start1 < end2) AND (end1 > start2)
            if (start_time < item.end_time) and (end_time > item.start_time):
                subj_name = item.subject.name if item.subject else f"Subject #{item.subject_id}"
                conflicts.append(f"Conflict detected with '{subj_name}' scheduled on {exam_date} from {item.start_time.strftime('%H:%M')} to {item.end_time.strftime('%H:%M')}.")

    return conflicts


# ==========================================
# 4. MARKS ENTRY & VALIDATION ENGINE
# ==========================================

def save_bulk_exam_marks(exam_subject_id, marks_data_list, entered_by_id=None):
    """
    Saves/updates student marks for an exam subject in an atomic transaction.
    marks_data_list format: [{'student_id': 1, 'attendance_status': 'PRESENT', 'marks_obtained': 75 font/float}]
    """
    es = ExaminationSubject.query.get(exam_subject_id)
    if not es:
        raise ValueError("Exam Subject not found.")

    exam = es.examination
    max_m = float(es.max_marks)
    pass_m = float(es.pass_marks)

    try:
        with db.session.begin_nested():
            for item in marks_data_list:
                s_id = item.get('student_id')
                if not s_id:
                    continue

                att_status = str(item.get('attendance_status', 'PRESENT')).upper().strip()
                if att_status not in ('PRESENT', 'ABSENT'):
                    att_status = 'PRESENT'

                raw_marks = item.get('marks_obtained')
                obtained_marks = None

                if att_status == 'PRESENT' and raw_marks is not None and str(raw_marks).strip() != '':
                    try:
                        obtained_marks = float(raw_marks)
                    except ValueError:
                        raise ValueError(f"Invalid numeric mark value '{raw_marks}'.")

                    if obtained_marks < 0:
                        raise ValueError(f"Marks obtained ({obtained_marks}) cannot be negative.")
                    if obtained_marks > max_m:
                        raise ValueError(f"Marks obtained ({obtained_marks}) cannot exceed Maximum Marks ({max_m}).")

                # Compute subject percentage, grade, and pass/fail
                pct = None
                grade_val = None
                is_p = None

                if att_status == 'PRESENT' and obtained_marks is not None:
                    pct = round((obtained_marks / max_m) * 100.0, 2)
                    grade_val = calculate_grade_from_percentage(pct)
                    is_p = (obtained_marks >= pass_m)
                elif att_status == 'ABSENT':
                    pct = 0.0
                    grade_val = "E"
                    is_p = False

                student_obj = Student.query.get(s_id)

                res = ExaminationResult.query.filter_by(
                    examination_id=es.examination_id,
                    exam_subject_id=es.id,
                    student_id=s_id
                ).first()

                if res:
                    res.attendance_status = att_status
                    res.marks_obtained = obtained_marks
                    res.max_marks = max_m
                    res.percentage = pct
                    res.grade = grade_val
                    res.is_pass = is_p
                    res.entered_by_id = entered_by_id
                    res.updated_at = datetime.utcnow()
                else:
                    res = ExaminationResult(
                        institute_id=exam.institute_id,
                        academic_session_id=exam.academic_session_id,
                        examination_id=es.examination_id,
                        exam_subject_id=es.id,
                        student_id=s_id,
                        class_id=es.class_id,
                        section_id=getattr(student_obj, 'section_id', None) or es.section_id,
                        attendance_status=att_status,
                        marks_obtained=obtained_marks,
                        max_marks=max_m,
                        percentage=pct,
                        grade=grade_val,
                        is_pass=is_p,
                        status="DRAFT",
                        entered_by_id=entered_by_id
                    )
                    db.session.add(res)

            es.status = "EVALUATED"

        db.session.commit()

        # Automatically calculate overall results for this exam
        try:
            calculate_and_publish_exam_results(es.examination_id, approved_by_id=entered_by_id)
        except Exception:
            pass

        return True

    except Exception as e:
        db.session.rollback()
        raise ValueError(f"Bulk Marks Submission failed: {str(e)}")


# ==========================================
# 5. RESULT CALCULATION & PUBLISHING
# ==========================================

def calculate_and_publish_exam_results(examination_id, approved_by_id=None):
    """
    Computes overall totals, percentages, grades, and pass/fail for all enrolled students
    and publishes results server-side.
    """
    exam = Examination.query.get(examination_id)
    if not exam:
        raise ValueError("Examination not found.")

    exam_classes = ExaminationClass.query.filter_by(examination_id=examination_id).all()
    if not exam_classes:
        raise ValueError("No classes assigned to this examination.")

    published_students_count = 0

    try:
        with db.session.begin_nested():
            for ec in exam_classes:
                # Find all students enrolled in this class/section
                s_query = Student.query.filter_by(class_id=ec.class_id)
                if ec.section_id:
                    s_query = s_query.filter_by(section_id=ec.section_id)
                students = s_query.all()

                for st in students:
                    # Get student subject results for this exam
                    sub_results = ExaminationResult.query.filter_by(
                        examination_id=examination_id,
                        student_id=st.id
                    ).all()

                    if not sub_results:
                        continue

                    tot_obtained = 0.0
                    tot_max = 0.0
                    has_failure = False
                    all_absent = True

                    for r in sub_results:
                        # Update status to PUBLISHED
                        r.status = "PUBLISHED"
                        r.approved_by_id = approved_by_id

                        if r.attendance_status == 'PRESENT' and r.marks_obtained is not None:
                            tot_obtained += float(r.marks_obtained)
                            all_absent = False
                        tot_max += float(r.max_marks)

                        if r.is_pass is False:
                            has_failure = True

                    overall_pct = round((tot_obtained / tot_max) * 100.0, 2) if tot_max > 0 else 0.0
                    overall_grd = calculate_grade_from_percentage(overall_pct) if not all_absent else "E"
                    overall_res = "FAIL" if (has_failure or all_absent or overall_pct < 33.0) else "PASS"

                    overall = ExamOverallResult.query.filter_by(
                        examination_id=examination_id,
                        student_id=st.id
                    ).first()

                    if overall:
                        overall.class_id = st.class_id
                        overall.section_id = st.section_id
                        overall.total_obtained = tot_obtained
                        overall.total_max = tot_max
                        overall.overall_percentage = overall_pct
                        overall.overall_grade = overall_grd
                        overall.overall_result = overall_res
                        overall.status = "PUBLISHED"
                        overall.updated_at = datetime.utcnow()
                    else:
                        overall = ExamOverallResult(
                            institute_id=exam.institute_id,
                            academic_session_id=exam.academic_session_id,
                            examination_id=examination_id,
                            student_id=st.id,
                            class_id=st.class_id,
                            section_id=st.section_id,
                            total_obtained=tot_obtained,
                            total_max=tot_max,
                            overall_percentage=overall_pct,
                            overall_grade=overall_grd,
                            overall_result=overall_res,
                            status="PUBLISHED"
                        )
                        db.session.add(overall)

                    published_students_count += 1

            exam.status = "RESULT_PUBLISHED"

        db.session.commit()
        return published_students_count

    except Exception as e:
        db.session.rollback()
        raise ValueError(f"Result publication failed: {str(e)}")


def correct_published_result(result_id, new_marks=None, new_attendance_status=None, admin_user_id=None):
    """
    Unlocks and corrects a single published result record with admin audit trail.
    """
    res = ExaminationResult.query.get(result_id)
    if not res:
        raise ValueError("Result record not found.")

    if new_attendance_status:
        res.attendance_status = str(new_attendance_status).upper()

    if res.attendance_status == 'PRESENT' and new_marks is not None:
        val = float(new_marks)
        if val < 0 or val > res.max_marks:
            raise ValueError(f"Marks must be between 0 and {res.max_marks}.")
        res.marks_obtained = val
        res.percentage = round((val / res.max_marks) * 100.0, 2)
        res.grade = calculate_grade_from_percentage(res.percentage)
        res.is_pass = (val >= res.exam_subject.pass_marks if res.exam_subject else val >= 33.0)
    elif res.attendance_status == 'ABSENT':
        res.marks_obtained = None
        res.percentage = 0.0
        res.grade = "E"
        res.is_pass = False

    res.entered_by_id = admin_user_id
    res.updated_at = datetime.utcnow()
    db.session.commit()

    # Recalculate student overall result
    calculate_and_publish_exam_results(res.examination_id, approved_by_id=admin_user_id)
    return res


# ==========================================
# 6. RESULT RETRIEVAL & STATISTICS
# ==========================================

def get_student_published_results(student_id):
    """
    Retrieves all examination results for a specific student.
    Returns: list of dicts { 'exam': Examination, 'overall': ExamOverallResult, 'subject_results': [...] }
    """
    overalls = ExamOverallResult.query.filter_by(
        student_id=student_id
    ).order_by(ExamOverallResult.updated_at.desc()).all()

    output = []
    seen_exam_ids = set()

    for ov in overalls:
        seen_exam_ids.add(ov.examination_id)
        sub_res = ExaminationResult.query.filter_by(
            examination_id=ov.examination_id,
            student_id=student_id
        ).all()

        output.append({
            'exam': ov.examination,
            'overall': ov,
            'subject_results': sub_res
        })

    # Fallback if subject results exist but overall result record hasn't been written
    subject_results_all = ExaminationResult.query.filter_by(student_id=student_id).all()
    for r in subject_results_all:
        if r.examination_id not in seen_exam_ids and r.examination:
            seen_exam_ids.add(r.examination_id)
            sub_res = [x for x in subject_results_all if x.examination_id == r.examination_id]
            tot_ob = sum(float(x.marks_obtained or 0) for x in sub_res if x.attendance_status == 'PRESENT')
            tot_mx = sum(float(x.max_marks) for x in sub_res)
            pct = round((tot_ob / tot_mx * 100.0), 2) if tot_mx > 0 else 0.0
            grd = calculate_grade_from_percentage(pct)
            has_fail = any(x.is_pass is False for x in sub_res)

            mock_overall = ExamOverallResult(
                examination_id=r.examination_id,
                student_id=student_id,
                total_obtained=tot_ob,
                total_max=tot_mx,
                overall_percentage=pct,
                overall_grade=grd,
                overall_result="FAIL" if has_fail else "PASS",
                status="PUBLISHED"
            )
            mock_overall.examination = r.examination

            output.append({
                'exam': r.examination,
                'overall': mock_overall,
                'subject_results': sub_res
            })

    return output


def get_exam_performance_statistics(examination_id, class_id=None):
    """
    Computes aggregate stats (Appeared, Absent, Passed, Failed, Average, Highest, Lowest).
    """
    query = ExaminationResult.query.filter_by(examination_id=examination_id)
    if class_id:
        query = query.filter_by(class_id=class_id)

    results = query.all()
    if not results:
        return {
            'total_records': 0, 'appeared': 0, 'absent': 0,
            'passed': 0, 'failed': 0, 'pass_rate': 0.0,
            'average_pct': 0.0, 'highest_pct': 0.0, 'lowest_pct': 0.0
        }

    total_rec = len(results)
    appeared = [r for r in results if r.attendance_status == 'PRESENT' and r.percentage is not None]
    absent = [r for r in results if r.attendance_status == 'ABSENT']
    passed = [r for r in appeared if r.is_pass is True]
    failed = [r for r in appeared if r.is_pass is False]

    pcts = [r.percentage for r in appeared]
    avg_pct = round(sum(pcts) / len(pcts), 2) if pcts else 0.0
    high_pct = round(max(pcts), 2) if pcts else 0.0
    low_pct = round(min(pcts), 2) if pcts else 0.0
    pass_rate = round((len(passed) / len(appeared)) * 100.0, 1) if appeared else 0.0

    return {
        'total_records': total_rec,
        'appeared': len(appeared),
        'absent': len(absent),
        'passed': len(passed),
        'failed': len(failed),
        'pass_rate': pass_rate,
        'average_pct': avg_pct,
        'highest_pct': high_pct,
        'lowest_pct': low_pct
    }


def generate_result_sheet_csv(examination_id, class_id=None):
    """
    Generates a CSV result matrix stream for an examination.
    """
    exam = Examination.query.get(examination_id)
    if not exam:
        raise ValueError("Examination not found.")

    es_query = ExaminationSubject.query.filter_by(examination_id=examination_id)
    if class_id:
        es_query = es_query.filter_by(class_id=class_id)
    exam_subjects = es_query.order_by(ExaminationSubject.class_id, ExaminationSubject.subject_id).all()

    st_query = Student.query
    if class_id:
        st_query = st_query.filter_by(class_id=class_id)
    else:
        assigned_cls_ids = [ec.class_id for ec in exam.exam_classes]
        if assigned_cls_ids:
            st_query = st_query.filter(Student.class_id.in_(assigned_cls_ids))
    students = st_query.order_by(Student.class_id, Student.registration_number, Student.first_name).all()

    output = io.StringIO()
    writer = csv.writer(output)

    # Header Row
    header = ["Roll No", "Student Name", "Class", "Section"]
    for es in exam_subjects:
        subj_name = es.subject.name if es.subject else f"Subj #{es.subject_id}"
        header.append(f"{subj_name} ({int(es.max_marks)}m)")
    header.extend(["Total Obtained", "Total Max", "Percentage (%)", "Grade", "Result"])

    writer.writerow(header)

    # Data Rows
    for st in students:
        ov = ExamOverallResult.query.filter_by(examination_id=examination_id, student_id=st.id).first()
        row = [
            st.roll_number or '—',
            st.full_name,
            st.school_class.display_name if st.school_class else '—',
            st.section.name if st.section else '—'
        ]

        for es in exam_subjects:
            res = ExaminationResult.query.filter_by(
                examination_id=examination_id,
                exam_subject_id=es.id,
                student_id=st.id
            ).first()

            if not res:
                row.append("—")
            elif res.attendance_status == 'ABSENT':
                row.append("ABSENT")
            else:
                row.append(f"{res.marks_obtained or 0} ({res.grade or ''})")

        if ov:
            row.extend([ov.total_obtained, ov.total_max, f"{ov.overall_percentage}%", ov.overall_grade, ov.overall_result])
        else:
            row.extend(["—", "—", "—", "—", "DRAFT"])

        writer.writerow(row)

    output.seek(0)
    return output.getvalue()


# ==========================================
# 7. ANONYMIZED AI CLASS EXAM INSIGHTS
# ==========================================

def generate_ai_exam_insights(examination_id, class_id=None):
    """
    Sends anonymized, aggregated exam performance data to Gemini API to generate teacher-facing insights.
    (No student names, roll numbers, or PII sent).
    """
    exam = Examination.query.get(examination_id)
    if not exam:
        raise ValueError("Examination not found.")

    stats = get_exam_performance_statistics(examination_id, class_id)
    
    es_query = ExaminationSubject.query.filter_by(examination_id=examination_id)
    if class_id:
        es_query = es_query.filter_by(class_id=class_id)
    exam_subjects = es_query.all()

    subject_summaries = []
    for es in exam_subjects:
        res_list = ExaminationResult.query.filter_by(exam_subject_id=es.id, attendance_status='PRESENT').all()
        pcts = [r.percentage for r in res_list if r.percentage is not None]
        avg_p = round(sum(pcts) / len(pcts), 1) if pcts else 0.0
        subj_name = es.subject.name if es.subject else f"Subject #{es.subject_id}"
        subject_summaries.append(f"- {subj_name}: Average {avg_p}%, Pass Rate {round((len([p for p in pcts if p >= 33])/len(pcts))*100, 1) if pcts else 0}%")

    prompt = f"""
You are an expert educational analytics advisor. Analyze the following anonymized class examination statistics and provide teacher-facing academic insights:

Examination: {exam.name}
Total Students Appeared: {stats['appeared']}
Total Absent: {stats['absent']}
Class Average Percentage: {stats['average_pct']}%
Highest Percentage: {stats['highest_pct']}%
Lowest Percentage: {stats['lowest_pct']}%
Overall Pass Rate: {stats['pass_rate']}%

Subject-wise Breakdown:
{chr(10).join(subject_summaries)}

Instructions:
1. Provide a concise 3-bullet summary of key class strengths.
2. Identify 2 key areas of academic weakness or concern.
3. Suggest 3 actionable teaching strategies for classroom revision.

DO NOT include student PII. Return clean markdown formatted output.
"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.5}
    }

    try:
        res_data = _call_gemini_api(payload, timeout=25)
        candidates = res_data.get('candidates', [])
        if candidates:
            return candidates[0]['content']['parts'][0]['text']
        return "AI Service returned no insights."
    except Exception as e:
        return f"AI Insights unavailable: {str(e)}"
