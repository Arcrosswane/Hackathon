from flask import Flask, render_template, redirect, url_for, session
from sqlalchemy import text
from app.config import Config
from app.models import db, School
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
from app.routes.homework import homework_bp
from app.routes.behaviour_skills import behaviour_skills_bp
from app.routes.fees import fees_bp
from app.routes.accounts import accounts_bp
from app.routes.payroll import payroll_bp
from app.utils.navigation import get_navigation_for_role
from app.services.academic_service import get_active_academic_session

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(parent_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(classes_bp)
    app.register_blueprint(school_bp)
    app.register_blueprint(subjects_bp)
    app.register_blueprint(employees_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(guardians_bp)
    app.register_blueprint(timetables_bp)
    app.register_blueprint(homework_bp)
    app.register_blueprint(behaviour_skills_bp)
    app.register_blueprint(fees_bp)
    app.register_blueprint(accounts_bp)
    app.register_blueprint(payroll_bp)

    # Auto table & column check
    with app.app_context():
        try:
            db.create_all()
            alter_statements = [
                "ALTER TABLE users ADD COLUMN school_id INT NULL;",
                "ALTER TABLE classes ADD COLUMN academic_session_id INT NULL;",
                "ALTER TABLE classes ADD COLUMN numeric_order INT DEFAULT 0;",
                "ALTER TABLE classes ADD COLUMN description TEXT NULL;",
                "ALTER TABLE classes ADD COLUMN is_active TINYINT(1) DEFAULT 1;",
                "ALTER TABLE classes ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP;",
                "ALTER TABLE classes ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP;",
                "ALTER TABLE schools ADD COLUMN academic_session VARCHAR(50) NULL;",
                "ALTER TABLE employees MODIFY COLUMN institute_id INT NULL;",
                "ALTER TABLE employees ADD COLUMN first_name VARCHAR(50) NULL;",
                "ALTER TABLE employees ADD COLUMN middle_name VARCHAR(50) NULL;",
                "ALTER TABLE employees ADD COLUMN last_name VARCHAR(50) NULL;",
                "ALTER TABLE employees ADD COLUMN department VARCHAR(50) DEFAULT 'Academic';",
                "ALTER TABLE employees ADD COLUMN designation VARCHAR(100) DEFAULT 'Teacher';",
                "ALTER TABLE employees ADD COLUMN employment_type VARCHAR(30) DEFAULT 'Full-time';",
                "ALTER TABLE employees ADD COLUMN is_teacher TINYINT(1) DEFAULT 1;",
                "ALTER TABLE employees ADD COLUMN is_active TINYINT(1) DEFAULT 1;",
                "ALTER TABLE employees ADD COLUMN alternate_phone VARCHAR(20) NULL;",
                "ALTER TABLE employees ADD COLUMN city VARCHAR(100) NULL;",
                "ALTER TABLE employees ADD COLUMN state VARCHAR(100) NULL;",
                "ALTER TABLE employees ADD COLUMN country VARCHAR(100) DEFAULT 'India';",
                "ALTER TABLE employees ADD COLUMN postal_code VARCHAR(20) NULL;",
                "ALTER TABLE employees ADD COLUMN profile_photo VARCHAR(255) NULL;",
                "ALTER TABLE employees ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP;",
                "ALTER TABLE employees ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP;",
                "ALTER TABLE students MODIFY COLUMN institute_id INT NULL;",
                "ALTER TABLE students MODIFY COLUMN class_id INT NULL;",
                "ALTER TABLE students ADD COLUMN first_name VARCHAR(50) NULL;",
                "ALTER TABLE students ADD COLUMN middle_name VARCHAR(50) NULL;",
                "ALTER TABLE students ADD COLUMN last_name VARCHAR(50) NULL;",
                "ALTER TABLE students ADD COLUMN date_of_birth DATE NULL;",
                "ALTER TABLE students ADD COLUMN status VARCHAR(30) DEFAULT 'Active';",
                "ALTER TABLE students ADD COLUMN is_active TINYINT(1) DEFAULT 1;",
                "ALTER TABLE students ADD COLUMN email_address VARCHAR(120) NULL;",
                "ALTER TABLE students ADD COLUMN mobile_phone_number VARCHAR(20) NULL;",
                "ALTER TABLE students ADD COLUMN home_address TEXT NULL;",
                "ALTER TABLE students ADD COLUMN city VARCHAR(100) NULL;",
                "ALTER TABLE students ADD COLUMN state VARCHAR(100) NULL;",
                "ALTER TABLE students ADD COLUMN country VARCHAR(100) DEFAULT 'India';",
                "ALTER TABLE students ADD COLUMN postal_code VARCHAR(20) NULL;",
                "ALTER TABLE students ADD COLUMN guardian_name VARCHAR(100) NULL;",
                "ALTER TABLE students ADD COLUMN guardian_relation VARCHAR(50) NULL;",
                "ALTER TABLE students ADD COLUMN guardian_phone VARCHAR(20) NULL;",
                "ALTER TABLE students ADD COLUMN guardian_email VARCHAR(120) NULL;",
                "ALTER TABLE students ADD COLUMN guardian_occupation VARCHAR(100) NULL;",
                "ALTER TABLE students ADD COLUMN profile_photo VARCHAR(255) NULL;",
                "ALTER TABLE students ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP;",
                "ALTER TABLE students ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP;",
                "ALTER TABLE guardians MODIFY COLUMN institute_id INT NULL;",
                "ALTER TABLE guardians ADD COLUMN first_name VARCHAR(50) NULL;",
                "ALTER TABLE guardians ADD COLUMN middle_name VARCHAR(50) NULL;",
                "ALTER TABLE guardians ADD COLUMN last_name VARCHAR(50) NULL;",
                "ALTER TABLE guardians ADD COLUMN occupation VARCHAR(100) NULL;",
                "ALTER TABLE guardians ADD COLUMN is_active TINYINT(1) DEFAULT 1;",
                "ALTER TABLE guardians ADD COLUMN status VARCHAR(30) DEFAULT 'Active';",
                "ALTER TABLE guardians ADD COLUMN email_address VARCHAR(120) NULL;",
                "ALTER TABLE guardians ADD COLUMN mobile_phone_number VARCHAR(20) NULL;",
                "ALTER TABLE guardians ADD COLUMN alternate_phone VARCHAR(20) NULL;",
                "ALTER TABLE guardians ADD COLUMN home_address TEXT NULL;",
                "ALTER TABLE guardians ADD COLUMN city VARCHAR(100) NULL;",
                "ALTER TABLE guardians ADD COLUMN state VARCHAR(100) NULL;",
                "ALTER TABLE guardians ADD COLUMN country VARCHAR(100) DEFAULT 'India';",
                "ALTER TABLE guardians ADD COLUMN postal_code VARCHAR(20) NULL;",
                "ALTER TABLE guardians ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP;",
                "ALTER TABLE guardians ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP;",
                "ALTER TABLE timetables ADD COLUMN academic_session_id INT NULL;",
                "ALTER TABLE timetables ADD COLUMN class_id INT NULL;",
                "ALTER TABLE timetables ADD COLUMN section_id INT NULL;",
                "ALTER TABLE timetables ADD COLUMN period_id INT NULL;",
                "ALTER TABLE timetables ADD COLUMN day_of_week VARCHAR(20) NULL;",
                "ALTER TABLE timetables ADD COLUMN subject_id INT NULL;",
                "ALTER TABLE timetables ADD COLUMN employee_id INT NULL;",
                "ALTER TABLE timetables ADD COLUMN room_number VARCHAR(50) NULL;",
                "ALTER TABLE timetables ADD COLUMN entry_type VARCHAR(30) DEFAULT 'CLASS';",
                "ALTER TABLE timetables ADD COLUMN status VARCHAR(30) DEFAULT 'DRAFT';",
                "ALTER TABLE timetables ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP;",
                "ALTER TABLE timetables ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP;",
                "ALTER TABLE periods ADD COLUMN academic_session_id INT NULL;",
                "ALTER TABLE periods ADD COLUMN name VARCHAR(50) NULL;",
                "ALTER TABLE periods ADD COLUMN period_order INT DEFAULT 1;",
                "ALTER TABLE periods ADD COLUMN start_time TIME NULL;",
                "ALTER TABLE periods ADD COLUMN end_time TIME NULL;",
                "ALTER TABLE periods ADD COLUMN period_type VARCHAR(30) DEFAULT 'CLASS';",
                "ALTER TABLE periods ADD COLUMN is_active TINYINT(1) DEFAULT 1;",
                "ALTER TABLE periods ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP;",
                "ALTER TABLE timetables MODIFY COLUMN employee_id INT NULL;",
                "ALTER TABLE timetables MODIFY COLUMN subject_id INT NULL;",
                "ALTER TABLE timetables MODIFY COLUMN section_id INT NULL;",
                "ALTER TABLE timetables MODIFY COLUMN room_number VARCHAR(50) NULL;",
                "ALTER TABLE homework ADD COLUMN school_id INT NULL;",
                "ALTER TABLE homework ADD COLUMN academic_session_id INT NULL;",
                "ALTER TABLE homework ADD COLUMN teacher_id INT NULL;",
                "ALTER TABLE homework ADD COLUMN section_id INT NULL;",
                "ALTER TABLE homework ADD COLUMN subject_id INT NULL;",
                "ALTER TABLE homework ADD COLUMN assigned_date DATE NULL;",
                "ALTER TABLE homework ADD COLUMN max_marks DECIMAL(5,2) DEFAULT 100.00;",
                "ALTER TABLE homework ADD COLUMN status VARCHAR(30) DEFAULT 'DRAFT';",
                "ALTER TABLE homework ADD COLUMN evaluation_type VARCHAR(20) DEFAULT 'MANUAL';",
                "ALTER TABLE homework ADD COLUMN grading_rubric TEXT NULL;",
                "ALTER TABLE homework ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP;",
                "ALTER TABLE homework MODIFY COLUMN created_by_employee_id INT NULL;",
                "ALTER TABLE homework_submissions ADD COLUMN ai_evaluated TINYINT(1) DEFAULT 0;",
                "ALTER TABLE homework_submissions ADD COLUMN ai_reasoning TEXT NULL;"
            ]
            with db.engine.connect() as conn:
                for stmt in alter_statements:
                    try:
                        conn.execute(text(stmt))
                        conn.commit()
                    except Exception:
                        pass

            # Auto-ensure demo Parent user account is seeded and password set
            from app.models import User, Guardian
            p_gdn = Guardian.query.filter_by(registration_number="PAR001").first()
            if p_gdn:
                p_user = User.query.filter_by(username="parent").first()
                if not p_user:
                    sch = School.query.first()
                    p_user = User(username="parent", user_type="Parent", school_id=sch.id if sch else None, linked_entity_id=p_gdn.id, is_active=True)
                    db.session.add(p_user)
                p_user.user_type = "Parent"
                p_user.set_password("Parent@123")
                p_user.linked_entity_id = p_gdn.id
                db.session.commit()

            # Auto-ensure demo student 'student' (4838) is aligned to Grade 9 Section A
            from app.models import Student, StudentEnrollment, Section
            demo_stus = Student.query.filter((Student.registration_number == '4838') | (Student.registration_number == 'ADM001')).all()
            sec_a = Section.query.filter((Section.name == 'A') | (Section.display_name == 'Section A')).first()
            if sec_a:
                for stu in demo_stus:
                    en = StudentEnrollment.query.filter_by(student_id=stu.id).first()
                    if en:
                        en.section_id = sec_a.id
                        en.class_id = sec_a.class_id
                    stu.class_id = sec_a.class_id
                db.session.commit()

            # Auto-seed default Behaviour Categories & Skill Definitions if empty
            from app.models import BehaviourCategory, SkillDefinition, FeeType
            if BehaviourCategory.query.count() == 0:
                default_cats = [
                    ("Positive Conduct", "Demonstrates positive demeanor, kindness, and helpful behavior."),
                    ("Classroom Participation", "Active engagement and participation during classroom discussions."),
                    ("Teamwork", "Cooperates effectively with peers in group activities."),
                    ("Respect", "Shows respect to teachers, staff, and fellow students."),
                    ("Punctuality", "Arrives on time to classes and submits tasks promptly."),
                    ("Discipline", "Adheres to school rules and classroom guidelines.")
                ]
                for cname, cdesc in default_cats:
                    db.session.add(BehaviourCategory(name=cname, description=cdesc, is_active=True))
                db.session.commit()

            if SkillDefinition.query.count() == 0:
                default_skills = [
                    ("Communication", "Communication", "Ability to express ideas clearly in speech and writing."),
                    ("Leadership", "Social", "Guides, motivates, and supports peers in academic tasks."),
                    ("Teamwork", "Social", "Works collaboratively and values contributions from others."),
                    ("Creativity", "Thinking", "Demonstrates original thinking and innovative problem solving."),
                    ("Problem Solving", "Thinking", "Analyzes challenges and finds logical solutions."),
                    ("Time Management", "Self-Management", "Organizes time efficiently to complete assignments.")
                ]
                for sname, sgrp, sdesc in default_skills:
                    db.session.add(SkillDefinition(name=sname, group_name=sgrp, description=sdesc, is_active=True))
                db.session.commit()

            if FeeType.query.count() == 0:
                default_fee_types = [
                    ("Tuition Fee", "Standard academic instruction fee"),
                    ("Admission Fee", "One-time enrollment registration fee"),
                    ("Examination Fee", "Term examination and assessment paper fee"),
                    ("Library Fee", "Library catalog and digital resource usage fee"),
                    ("Activity Fee", "Co-curricular activities, events, and sports fee"),
                    ("Transport Fee", "School bus and shuttle transportation fee")
                ]
                for ftname, ftdesc in default_fee_types:
                    db.session.add(FeeType(name=ftname, description=ftdesc, is_active=True))
                db.session.commit()
        except Exception as e:
            db.session.rollback()
            app.logger.warning(f"Database schema auto-check notice: {e}")

    # Global Context Processor for Navigation, User Session, School Profile, and Active Academic Session
    @app.context_processor
    def inject_global_context():
        user_role = session.get('user_role')
        username = session.get('username')
        nav_items = get_navigation_for_role(user_role)
        
        active_session = None
        current_school = None
        try:
            active_session = get_active_academic_session()
            current_school = School.query.first()
        except Exception:
            pass

        return dict(
            current_user_role=user_role,
            current_username=username,
            nav_items=nav_items,
            active_session=active_session,
            current_school=current_school
        )

    # Root redirect
    @app.route('/')
    def index():
        if 'user_id' in session:
            role = str(session.get('user_role', '')).lower()
            if role == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif role in ('teacher', 'employee'):
                return redirect(url_for('teacher.dashboard'))
            elif role == 'student':
                return redirect(url_for('student.dashboard'))
            elif role in ('parent', 'guardian'):
                return redirect(url_for('parent.dashboard'))
        return redirect(url_for('auth.login'))

    # Error Handlers
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    return app
