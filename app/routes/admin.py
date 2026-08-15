from flask import Blueprint, render_template
from app.models import School
from app.utils.decorators import login_required, role_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@login_required
@role_required('admin')
def dashboard():
    school = School.query.first()
    future_modules = [
        {'name': 'School Management', 'desc': 'Manage institute settings, classes, and sections'},
        {'name': 'Students', 'desc': 'Student registration, profile management, and rosters'},
        {'name': 'Teachers & Staff', 'desc': 'Teacher directory, salaries, and class assignments'},
        {'name': 'Attendance', 'desc': 'Daily attendance tracking for students and staff'},
        {'name': 'Academics', 'desc': 'Curriculum, timetable management, and subjects'},
        {'name': 'Finance & Fees', 'desc': 'Fee collection, dues tracking, and payroll'},
        {'name': 'Reports', 'desc': 'Institutional analytics and performance reports'}
    ]
    return render_template('admin/dashboard.html', school=school, future_modules=future_modules)
