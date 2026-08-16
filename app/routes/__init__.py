from app.routes.auth import auth_bp
from app.routes.admin import admin_bp
from app.routes.teacher import teacher_bp
from app.routes.student import student_bp
from app.routes.parent import parent_bp
from app.routes.settings import settings_bp
from app.routes.classes import classes_bp
from app.routes.school import school_bp
from app.routes.subjects import subjects_bp
from app.routes.employees import employees_bp
from app.routes.students import students_bp
from app.routes.guardians import guardians_bp
from app.routes.timetables import timetables_bp
from app.routes.fees import fees_bp
from app.routes.accounts import accounts_bp
from app.routes.payroll import payroll_bp
from app.routes.attendance import attendance_bp
from app.routes.question_bank import question_bank_bp

__all__ = [
    'auth_bp', 
    'admin_bp', 
    'teacher_bp', 
    'student_bp', 
    'parent_bp',
    'settings_bp', 
    'classes_bp', 
    'school_bp',
    'subjects_bp',
    'employees_bp',
    'students_bp',
    'guardians_bp',
    'timetables_bp',
    'fees_bp',
    'accounts_bp',
    'payroll_bp',
    'attendance_bp',
    'question_bank_bp'
]
