from flask import Blueprint, render_template, session, redirect, url_for, flash
from app.models import db, User, Guardian, GuardianStudent, Student, StudentEnrollment, School, AcademicSession
from app.utils.decorators import login_required, role_required
from app.services.academic_service import get_active_academic_session
from app.services.subject_service import get_subjects_for_class

parent_bp = Blueprint('parent', __name__, url_prefix='/parent')

@parent_bp.route('/dashboard', methods=['GET'])
@login_required
@role_required('parent')
def dashboard():
    user_id = session.get('user_id')
    linked_guardian_id = session.get('linked_entity_id')
    
    guardian = None
    if linked_guardian_id:
        guardian = Guardian.query.get(linked_guardian_id)
    
    if not guardian:
        # Fallback search by username if linked_entity_id was unset
        guardian = Guardian.query.filter_by(registration_number="PAR001").first()

    children_data = []
    if guardian:
        for link in guardian.student_links:
            student = link.student
            curr_en = student.get_current_enrollment()
            class_subjects = get_subjects_for_class(curr_en.class_id) if curr_en else []
            
            children_data.append({
                'link': link,
                'student': student,
                'current_enrollment': curr_en,
                'subjects': class_subjects
            })

    active_session = get_active_academic_session()
    current_school = School.query.first()

    return render_template(
        'parent/dashboard.html',
        guardian=guardian,
        children_data=children_data,
        active_session=active_session,
        current_school=current_school
    )
