from app.models import db, SchoolClass, Section, Subject, SubjectClass, Employee, Student, StudentEnrollment, Guardian, GuardianStudent

# ---------------------------------------------------------
# CLASS & SECTION SERVICES
# ---------------------------------------------------------

def get_classes_for_session(school_id, session_id):
    return SchoolClass.query.filter_by(school_id=school_id, academic_session_id=session_id).all()

def create_class(school_id, session_id, class_name):
    sc = SchoolClass(school_id=school_id, academic_session_id=session_id, class_name=class_name)
    db.session.add(sc)
    db.session.commit()
    return sc

def create_section(school_class_id, section_name):
    sec = Section(school_class_id=school_class_id, section_name=section_name)
    db.session.add(sec)
    db.session.commit()
    return sec


# ---------------------------------------------------------
# SUBJECT SERVICES
# ---------------------------------------------------------

def get_all_subjects(school_id):
    return Subject.query.filter_by(school_id=school_id).all()

def get_subjects_for_class(school_class_id):
    sc_list = SubjectClass.query.filter_by(school_class_id=school_class_id).all()
    sub_ids = [sc.subject_id for sc in sc_list]
    return Subject.query.filter(Subject.id.in_(sub_ids)).all() if sub_ids else []

def assign_subject_to_class(school_class_id, subject_id, teacher_id=None):
    sc = SubjectClass.query.filter_by(school_class_id=school_class_id, subject_id=subject_id).first()
    if not sc:
        sc = SubjectClass(school_class_id=school_class_id, subject_id=subject_id, teacher_id=teacher_id)
        db.session.add(sc)
    else:
        sc.teacher_id = teacher_id
    db.session.commit()
    return sc


# ---------------------------------------------------------
# EMPLOYEE / TEACHER SERVICES
# ---------------------------------------------------------

def get_all_employees(school_id):
    return Employee.query.filter_by(school_id=school_id).all()

def get_teachers(school_id):
    return Employee.query.filter_by(school_id=school_id, designation='Teacher').all()

def get_employee_by_id(employee_id, school_id):
    return Employee.query.filter_by(id=employee_id, school_id=school_id).first()


# ---------------------------------------------------------
# STUDENT SERVICES
# ---------------------------------------------------------

def get_all_students(school_id):
    return Student.query.filter_by(school_id=school_id).all()

def get_current_enrollment(student_id, session_id):
    return StudentEnrollment.query.filter_by(student_id=student_id, academic_session_id=session_id, is_active=True).first()

def transfer_student(student_id, new_school_class_id, new_section_id, session_id):
    enr = StudentEnrollment.query.filter_by(student_id=student_id, academic_session_id=session_id, is_active=True).first()
    if enr:
        enr.school_class_id = new_school_class_id
        enr.section_id = new_section_id
        db.session.commit()
        return enr
    return None


# ---------------------------------------------------------
# GUARDIAN / PARENT SERVICES
# ---------------------------------------------------------

def get_all_guardians(school_id):
    return Guardian.query.filter_by(school_id=school_id).all()

def link_guardian_student(guardian_id, student_id, relationship="Parent"):
    link = GuardianStudent.query.filter_by(guardian_id=guardian_id, student_id=student_id).first()
    if not link:
        link = GuardianStudent(guardian_id=guardian_id, student_id=student_id, relationship=relationship)
        db.session.add(link)
        db.session.commit()
    return link

def unlink_guardian_student(guardian_id, student_id):
    GuardianStudent.query.filter_by(guardian_id=guardian_id, student_id=student_id).delete()
    db.session.commit()
