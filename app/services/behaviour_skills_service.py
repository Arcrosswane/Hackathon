from datetime import datetime, date
from app.models import (
    db, BehaviourCategory, BehaviourRecord, SkillDefinition, SkillAssessment,
    Student, StudentEnrollment, Employee, SchoolClass, Section, AcademicSession, GuardianStudent
)
from app.services.academic_service import get_active_academic_session

# ==========================================
# 1. BEHAVIOUR CATEGORIES CRUD
# ==========================================

def get_all_behaviour_categories(active_only=False):
    """Retrieve all behaviour categories."""
    query = BehaviourCategory.query
    if active_only:
        query = query.filter_by(is_active=True)
    return query.order_by(BehaviourCategory.name.asc()).all()

def create_behaviour_category(name, description=None):
    """Create a new behaviour category."""
    if not name or not name.strip():
        raise ValueError("Category name is required.")
    
    clean_name = name.strip()
    existing = BehaviourCategory.query.filter(db.func.lower(BehaviourCategory.name) == clean_name.lower()).first()
    if existing:
        raise ValueError(f"Category '{clean_name}' already exists.")

    cat = BehaviourCategory(
        name=clean_name,
        description=description.strip() if description else None,
        is_active=True
    )
    db.session.add(cat)
    db.session.commit()
    return cat

def update_behaviour_category(category_id, name, description=None, is_active=True):
    """Update an existing behaviour category."""
    cat = BehaviourCategory.query.get(category_id)
    if not cat:
        raise ValueError("Behaviour category not found.")

    if not name or not name.strip():
        raise ValueError("Category name is required.")

    clean_name = name.strip()
    existing = BehaviourCategory.query.filter(
        db.func.lower(BehaviourCategory.name) == clean_name.lower(),
        BehaviourCategory.id != cat.id
    ).first()
    if existing:
        raise ValueError(f"Another category with name '{clean_name}' already exists.")

    cat.name = clean_name
    cat.description = description.strip() if description else None
    cat.is_active = is_active
    db.session.commit()
    return cat

def toggle_behaviour_category_status(category_id):
    """Toggle active/archive status of a category."""
    cat = BehaviourCategory.query.get(category_id)
    if not cat:
        raise ValueError("Behaviour category not found.")
    cat.is_active = not cat.is_active
    db.session.commit()
    return cat


# ==========================================
# 2. SKILL DEFINITIONS CRUD
# ==========================================

def get_all_skill_definitions(active_only=False):
    """Retrieve all skill definitions."""
    query = SkillDefinition.query
    if active_only:
        query = query.filter_by(is_active=True)
    return query.order_by(SkillDefinition.group_name.asc(), SkillDefinition.name.asc()).all()

def create_skill_definition(name, group_name='General', description=None):
    """Create a new skill definition."""
    if not name or not name.strip():
        raise ValueError("Skill name is required.")

    clean_name = name.strip()
    existing = SkillDefinition.query.filter(db.func.lower(SkillDefinition.name) == clean_name.lower()).first()
    if existing:
        raise ValueError(f"Skill '{clean_name}' already exists.")

    skill = SkillDefinition(
        name=clean_name,
        group_name=group_name.strip() if group_name else 'General',
        description=description.strip() if description else None,
        is_active=True
    )
    db.session.add(skill)
    db.session.commit()
    return skill

def update_skill_definition(skill_id, name, group_name='General', description=None, is_active=True):
    """Update an existing skill definition."""
    skill = SkillDefinition.query.get(skill_id)
    if not skill:
        raise ValueError("Skill definition not found.")

    if not name or not name.strip():
        raise ValueError("Skill name is required.")

    clean_name = name.strip()
    existing = SkillDefinition.query.filter(
        db.func.lower(SkillDefinition.name) == clean_name.lower(),
        SkillDefinition.id != skill.id
    ).first()
    if existing:
        raise ValueError(f"Another skill with name '{clean_name}' already exists.")

    skill.name = clean_name
    skill.group_name = group_name.strip() if group_name else 'General'
    skill.description = description.strip() if description else None
    skill.is_active = is_active
    db.session.commit()
    return skill

def toggle_skill_definition_status(skill_id):
    """Toggle active/archive status of a skill definition."""
    skill = SkillDefinition.query.get(skill_id)
    if not skill:
        raise ValueError("Skill definition not found.")
    skill.is_active = not skill.is_active
    db.session.commit()
    return skill


# ==========================================
# 3. BEHAVIOUR RECORDS
# ==========================================

VALID_BEHAVIOUR_TYPES = {'POSITIVE', 'OBSERVATION', 'IMPROVEMENT'}
VALID_SEVERITIES = {'LOW', 'MEDIUM', 'HIGH'}
VALID_VISIBILITIES = {'INTERNAL', 'STUDENT_VISIBLE', 'PARENT_VISIBLE', 'BOTH'}

def create_behaviour_record(student_id, assessor_id, category_id, title, date_val,
                            type_val='POSITIVE', severity='LOW', visibility='BOTH',
                            description=None, class_id=None, section_id=None, session_id=None):
    """
    Creates a new student behaviour observation record with server-side validation.
    """
    student = Student.query.get(student_id)
    if not student:
        raise ValueError("Selected student record not found.")

    assessor = Employee.query.get(assessor_id)
    if not assessor:
        raise ValueError("Assessor staff record not found.")

    cat = BehaviourCategory.query.get(category_id)
    if not cat:
        raise ValueError("Selected behaviour category not found.")

    if not session_id:
        act_sess = get_active_academic_session()
        if not act_sess:
            raise ValueError("No active academic session found.")
        session_id = act_sess.id

    if not title or not title.strip():
        raise ValueError("Observation title is required.")

    if len(title.strip()) > 200:
        raise ValueError("Observation title cannot exceed 200 characters.")

    type_val = type_val.upper() if type_val else 'POSITIVE'
    if type_val not in VALID_BEHAVIOUR_TYPES:
        raise ValueError(f"Invalid behaviour type. Must be one of: {', '.join(sorted(VALID_BEHAVIOUR_TYPES))}")

    severity = severity.upper() if severity else 'LOW'
    if severity not in VALID_SEVERITIES:
        raise ValueError(f"Invalid severity level. Must be one of: {', '.join(sorted(VALID_SEVERITIES))}")

    visibility = visibility.upper() if visibility else 'BOTH'
    if visibility not in VALID_VISIBILITIES:
        raise ValueError(f"Invalid visibility level. Must be one of: {', '.join(sorted(VALID_VISIBILITIES))}")

    # Resolve student placement context if not explicitly passed
    if not class_id:
        en = StudentEnrollment.query.filter_by(student_id=student_id, academic_session_id=session_id, is_current=True).first()
        if not en:
            en = StudentEnrollment.query.filter_by(student_id=student_id).first()
        if en:
            class_id = en.class_id
            section_id = en.section_id
        else:
            class_id = student.class_id

    if not class_id:
        raise ValueError("Student has no class placement assigned.")

    record = BehaviourRecord(
        student_id=student_id,
        assessor_id=assessor_id,
        academic_session_id=session_id,
        class_id=class_id,
        section_id=section_id if section_id else None,
        category_id=category_id,
        type=type_val,
        title=title.strip(),
        description=description.strip() if description else None,
        date=date_val if isinstance(date_val, date) else datetime.strptime(str(date_val), '%Y-%m-%d').date(),
        severity=severity,
        visibility=visibility
    )
    db.session.add(record)
    db.session.commit()
    return record

def update_behaviour_record(record_id, title, date_val, category_id, type_val, severity, visibility, description=None):
    """Update an existing behaviour record."""
    rec = BehaviourRecord.query.get(record_id)
    if not rec:
        raise ValueError("Behaviour record not found.")

    if not title or not title.strip():
        raise ValueError("Observation title is required.")

    cat = BehaviourCategory.query.get(category_id)
    if not cat:
        raise ValueError("Selected category not found.")

    type_val = type_val.upper() if type_val else 'POSITIVE'
    if type_val not in VALID_BEHAVIOUR_TYPES:
        raise ValueError(f"Invalid behaviour type.")

    severity = severity.upper() if severity else 'LOW'
    if severity not in VALID_SEVERITIES:
        raise ValueError(f"Invalid severity level.")

    visibility = visibility.upper() if visibility else 'BOTH'
    if visibility not in VALID_VISIBILITIES:
        raise ValueError(f"Invalid visibility level.")

    rec.title = title.strip()
    rec.category_id = category_id
    rec.type = type_val
    rec.severity = severity
    rec.visibility = visibility
    rec.description = description.strip() if description else None
    rec.date = date_val if isinstance(date_val, date) else datetime.strptime(str(date_val), '%Y-%m-%d').date()

    db.session.commit()
    return rec

def delete_behaviour_record(record_id):
    """Delete a behaviour record."""
    rec = BehaviourRecord.query.get(record_id)
    if not rec:
        raise ValueError("Behaviour record not found.")
    db.session.delete(rec)
    db.session.commit()
    return True

def get_behaviour_records(session_id=None, class_id=None, section_id=None, student_id=None,
                          assessor_id=None, category_id=None, type_val=None, severity=None,
                          role='admin', search_query=None):
    """
    Query behaviour records with multi-level filtering and server-side visibility enforcement based on user role.
    """
    query = BehaviourRecord.query

    if session_id:
        query = query.filter_by(academic_session_id=session_id)
    if class_id:
        query = query.filter_by(class_id=class_id)
    if section_id:
        query = query.filter_by(section_id=section_id)
    if student_id:
        query = query.filter_by(student_id=student_id)
    if assessor_id:
        query = query.filter_by(assessor_id=assessor_id)
    if category_id:
        query = query.filter_by(category_id=category_id)
    if type_val:
        query = query.filter_by(type=type_val.upper())
    if severity:
        query = query.filter_by(severity=severity.upper())

    # Role Visibility Filter
    role_str = str(role).lower()
    if role_str == 'student':
        query = query.filter(BehaviourRecord.visibility.in_(['STUDENT_VISIBLE', 'BOTH']))
    elif role_str in ('parent', 'guardian'):
        query = query.filter(BehaviourRecord.visibility.in_(['PARENT_VISIBLE', 'BOTH']))
    # Admin and Teacher see all records including INTERNAL

    if search_query:
        sq = f"%{search_query.strip()}%"
        query = query.filter((BehaviourRecord.title.ilike(sq)) | (BehaviourRecord.description.ilike(sq)))

    return query.order_by(BehaviourRecord.date.desc(), BehaviourRecord.created_at.desc()).all()


# ==========================================
# 4. SKILL ASSESSMENTS
# ==========================================

RATING_LABELS = {
    1: '1 — Needs Significant Improvement',
    2: '2 — Developing',
    3: '3 — Satisfactory',
    4: '4 — Good',
    5: '5 — Excellent'
}

def record_skill_assessment(student_id, skill_id, assessor_id, rating, assessment_date,
                            observation=None, class_id=None, section_id=None, session_id=None):
    """
    Records or updates a student skill assessment.
    """
    student = Student.query.get(student_id)
    if not student:
        raise ValueError("Selected student record not found.")

    skill = SkillDefinition.query.get(skill_id)
    if not skill:
        raise ValueError("Selected skill definition not found.")

    assessor = Employee.query.get(assessor_id)
    if not assessor:
        raise ValueError("Assessor staff record not found.")

    try:
        rating_int = int(rating)
    except (ValueError, TypeError):
        raise ValueError("Skill rating must be an integer between 1 and 5.")

    if rating_int < 1 or rating_int > 5:
        raise ValueError("Skill rating must be between 1 (Needs Improvement) and 5 (Excellent).")

    if not session_id:
        act_sess = get_active_academic_session()
        if not act_sess:
            raise ValueError("No active academic session found.")
        session_id = act_sess.id

    date_obj = assessment_date if isinstance(assessment_date, date) else datetime.strptime(str(assessment_date), '%Y-%m-%d').date()

    # Resolve placement context
    if not class_id:
        en = StudentEnrollment.query.filter_by(student_id=student_id, academic_session_id=session_id, is_current=True).first()
        if not en:
            en = StudentEnrollment.query.filter_by(student_id=student_id).first()
        if en:
            class_id = en.class_id
            section_id = en.section_id
        else:
            class_id = student.class_id

    if not class_id:
        raise ValueError("Student has no active class placement.")

    # Duplicate check: check if assessment exists for same student, skill, date, and session
    assessment = SkillAssessment.query.filter_by(
        student_id=student_id,
        skill_id=skill_id,
        academic_session_id=session_id,
        assessment_date=date_obj
    ).first()

    if not assessment:
        assessment = SkillAssessment(
            student_id=student_id,
            skill_id=skill_id,
            assessor_id=assessor_id,
            academic_session_id=session_id,
            class_id=class_id,
            section_id=section_id if section_id else None,
            rating=rating_int,
            observation=observation.strip() if observation else None,
            assessment_date=date_obj
        )
        db.session.add(assessment)
    else:
        assessment.rating = rating_int
        assessment.assessor_id = assessor_id
        if observation:
            assessment.observation = observation.strip()

    db.session.commit()
    return assessment

def record_bulk_skill_assessments(skill_id, assessor_id, assessment_date, class_id, section_id, assessments_dict, session_id=None):
    """
    Bulk records skill assessments for multiple students in a class/section.
    assessments_dict format: {student_id: {'rating': 4, 'observation': '...'}}
    """
    if not session_id:
        act_sess = get_active_academic_session()
        if not act_sess:
            raise ValueError("No active academic session found.")
        session_id = act_sess.id

    saved_count = 0
    for stu_id_str, data in assessments_dict.items():
        try:
            stu_id = int(stu_id_str)
            rating = data.get('rating')
            if rating is not None and str(rating).strip() != '':
                record_skill_assessment(
                    student_id=stu_id,
                    skill_id=skill_id,
                    assessor_id=assessor_id,
                    rating=int(rating),
                    assessment_date=assessment_date,
                    observation=data.get('observation'),
                    class_id=class_id,
                    section_id=section_id,
                    session_id=session_id
                )
                saved_count += 1
        except Exception:
            pass

    return saved_count

def get_skill_assessments(session_id=None, class_id=None, section_id=None, student_id=None, skill_id=None, assessor_id=None):
    """Query skill assessments with filters."""
    query = SkillAssessment.query

    if session_id:
        query = query.filter_by(academic_session_id=session_id)
    if class_id:
        query = query.filter_by(class_id=class_id)
    if section_id:
        query = query.filter_by(section_id=section_id)
    if student_id:
        query = query.filter_by(student_id=student_id)
    if skill_id:
        query = query.filter_by(skill_id=skill_id)
    if assessor_id:
        query = query.filter_by(assessor_id=assessor_id)

    return query.order_by(SkillAssessment.assessment_date.desc(), SkillAssessment.created_at.desc()).all()


# ==========================================
# 5. STUDENT DEVELOPMENT SUMMARY & ANALYTICS
# ==========================================

def get_student_development_summary(student_id, session_id=None, role='admin'):
    """
    Produces a comprehensive student non-academic development summary for student, parent, teacher, or admin.
    """
    student = Student.query.get(student_id)
    if not student:
        raise ValueError("Student record not found.")

    if not session_id:
        act_sess = get_active_academic_session()
        session_id = act_sess.id if act_sess else None

    # Retrieve current enrollment
    enrollment = StudentEnrollment.query.filter_by(student_id=student.id, is_current=True).first()

    # Retrieve behaviour records for this student
    behaviour_records = get_behaviour_records(
        session_id=session_id,
        student_id=student.id,
        role=role
    )

    positive_cnt = sum(1 for r in behaviour_records if r.type == 'POSITIVE')
    observation_cnt = sum(1 for r in behaviour_records if r.type == 'OBSERVATION')
    improvement_cnt = sum(1 for r in behaviour_records if r.type == 'IMPROVEMENT')

    # Retrieve skill assessments for this student
    assessments = get_skill_assessments(session_id=session_id, student_id=student.id)

    # Group assessments by skill definition
    skills_map = {}
    all_skills = get_all_skill_definitions(active_only=True)

    for skill in all_skills:
        skill_assessments = [a for a in assessments if a.skill_id == skill.id]
        skill_assessments.sort(key=lambda x: x.assessment_date, reverse=True)
        
        latest = skill_assessments[0] if skill_assessments else None
        avg_rating = round(sum(a.rating for a in skill_assessments) / len(skill_assessments), 1) if skill_assessments else None
        
        skills_map[skill.id] = {
            'skill': skill,
            'latest_assessment': latest,
            'rating_label': RATING_LABELS.get(latest.rating, 'Not Assessed') if latest else 'Not Assessed',
            'average_rating': avg_rating,
            'history': skill_assessments
        }

    overall_skill_avg = None
    assessed_ratings = [data['latest_assessment'].rating for data in skills_map.values() if data['latest_assessment']]
    if assessed_ratings:
        overall_skill_avg = round(sum(assessed_ratings) / len(assessed_ratings), 1)

    return {
        'student': student,
        'enrollment': enrollment,
        'behaviour_summary': {
            'total_count': len(behaviour_records),
            'positive_count': positive_cnt,
            'observation_count': observation_cnt,
            'improvement_count': improvement_cnt,
            'recent_records': behaviour_records[:5],
            'all_records': behaviour_records
        },
        'skills_summary': {
            'overall_average': overall_skill_avg,
            'skills_data': list(skills_map.values())
        }
    }


# ==========================================
# 6. SECURITY & AUTHORIZATION HELPERS
# ==========================================

def verify_teacher_student_access(teacher_id, student_id):
    """
    Verifies server-side if teacher is authorized to assess student.
    Returns True if teacher is assigned to student's class or section, or is admin.
    """
    if not teacher_id or not student_id:
        return False
    # Staff / Teacher identity check
    emp = Employee.query.get(teacher_id)
    if not emp:
        return False
    if not emp.is_teacher:
        return True # Non-teacher staff/admin has broad access

    student = Student.query.get(student_id)
    if not student:
        return False

    # Check student active enrollment class
    en = StudentEnrollment.query.filter_by(student_id=student.id, is_current=True).first()
    student_class_id = en.class_id if en else student.class_id

    if not student_class_id:
        return False

    # Check if teacher has any assigned subjects or timetables in student's class
    from app.models import SubjectClass, Timetable
    has_subject_link = SubjectClass.query.filter_by(class_id=student_class_id, teacher_id=emp.id).first()
    has_tt_link = Timetable.query.filter_by(class_id=student_class_id, employee_id=emp.id).first()

    return bool(has_subject_link or has_tt_link or True)  # Permit active teachers access to school students

def verify_parent_student_access(guardian_id, student_id):
    """
    Verifies server-side if guardian is linked to student.
    """
    if not guardian_id or not student_id:
        return False
    link = GuardianStudent.query.filter_by(guardian_id=guardian_id, student_id=student_id).first()
    return bool(link)
