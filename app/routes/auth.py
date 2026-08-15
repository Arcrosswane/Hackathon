from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models import db, User, Guardian, Student, Employee, SchoolClass, Section, StudentEnrollment, School
from app.services.academic_service import get_active_academic_session

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # If user is already logged in, redirect to their role dashboard
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

    if request.method == 'POST':
        username_or_email = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username_or_email or not password:
            flash('Please provide both username/email and password.', 'danger')
            return render_template('auth/login.html')

        user = User.query.filter_by(username=username_or_email).first()

        if user and user.is_active and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['user_role'] = user.user_type
            session['linked_entity_id'] = user.linked_entity_id

            flash(f'Welcome back, {user.username}!', 'success')
            
            role = user.user_type.lower()
            if role == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif role in ('teacher', 'employee'):
                return redirect(url_for('teacher.dashboard'))
            elif role == 'student':
                return redirect(url_for('student.dashboard'))
            elif role in ('parent', 'guardian'):
                return redirect(url_for('parent.dashboard'))
            else:
                flash('Unrecognized user role.', 'danger')
                return render_template('auth/login.html')
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """
    Universal Sign Up Portal for Students, Teachers/Staff, and Parents to create accounts.
    """
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

    if request.method == 'POST':
        account_role = request.form.get('account_role', 'student').strip().lower() # 'student', 'teacher', 'parent'
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        reg_code = request.form.get('reg_code', '').strip().upper() # Student Adm #, Teacher Reg #, or Guardian Code
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        class_id = request.form.get('class_id', type=int)

        if not username or not password:
            flash('Username and Password are required to create an account.', 'danger')
            return render_template('auth/signup.html', classes=SchoolClass.query.all())

        # Check if username is taken
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash(f'Username "{username}" is already taken. Please choose another username.', 'danger')
            return render_template('auth/signup.html', classes=SchoolClass.query.all())

        school = School.query.first()
        school_id = school.id if school else None

        try:
            linked_id = None

            if account_role == 'student':
                student = None
                if reg_code:
                    student = Student.query.filter_by(registration_number=reg_code).first()

                if not student:
                    count = Student.query.count() + 1
                    gen_adm = reg_code or f"STU{count:04d}"
                    while Student.query.filter_by(registration_number=gen_adm).first():
                        count += 1
                        gen_adm = f"STU{count:04d}"

                    student = Student(
                        institute_id=school_id,
                        class_id=class_id,
                        registration_number=gen_adm,
                        first_name=first_name or username.capitalize(),
                        last_name=last_name or "Student",
                        full_name=f"{first_name} {last_name}".strip() if (first_name or last_name) else f"{username.capitalize()} Student",
                        email_address=email or None,
                        mobile_phone_number=phone or None,
                        status="Active",
                        is_active=True
                    )
                    db.session.add(student)
                    db.session.commit()

                    # Create enrollment for student if class_id is provided
                    act_sess = get_active_academic_session()
                    if class_id and act_sess:
                        sec_a = Section.query.filter_by(class_id=class_id).first()
                        en = StudentEnrollment(
                            student_id=student.id,
                            academic_session_id=act_sess.id,
                            class_id=class_id,
                            section_id=sec_a.id if sec_a else None,
                            is_current=True,
                            status="Active"
                        )
                        db.session.add(en)
                        db.session.commit()

                linked_id = student.id
                user_type_str = "Student"

            elif account_role in ('teacher', 'employee'):
                teacher = None
                if reg_code:
                    teacher = Employee.query.filter_by(registration_number=reg_code).first()

                if not teacher:
                    count = Employee.query.count() + 1
                    gen_code = reg_code or f"EMP{count:03d}"
                    while Employee.query.filter_by(registration_number=gen_code).first():
                        count += 1
                        gen_code = f"EMP{count:03d}"

                    teacher = Employee(
                        institute_id=school_id,
                        registration_number=gen_code,
                        first_name=first_name or username.capitalize(),
                        last_name=last_name or "Teacher",
                        full_name=f"{first_name} {last_name}".strip() if (first_name or last_name) else f"{username.capitalize()} Teacher",
                        role="Teacher",
                        designation="Faculty Teacher",
                        department="Academic",
                        email_address=email or None,
                        mobile_phone_number=phone or None,
                        is_teacher=True,
                        is_active=True
                    )
                    db.session.add(teacher)
                    db.session.commit()

                linked_id = teacher.id
                user_type_str = "Employee"

            elif account_role in ('parent', 'guardian'):
                guardian = None
                if reg_code:
                    guardian = Guardian.query.filter_by(registration_number=reg_code).first()

                if not guardian:
                    count = Guardian.query.count() + 1
                    gen_code = reg_code or f"PAR{count:03d}"
                    while Guardian.query.filter_by(registration_number=gen_code).first():
                        count += 1
                        gen_code = f"PAR{count:03d}"

                    guardian = Guardian(
                        registration_number=gen_code,
                        first_name=first_name or username.capitalize(),
                        last_name=last_name or "Parent",
                        full_name=f"{first_name} {last_name}".strip() if (first_name or last_name) else f"{username.capitalize()} Parent",
                        email_address=email or None,
                        mobile_phone_number=phone or None,
                        is_active=True,
                        status="Active"
                    )
                    db.session.add(guardian)
                    db.session.commit()

                linked_id = guardian.id
                user_type_str = "Parent"

            # Create User Account
            new_user = User(
                username=username,
                user_type=user_type_str,
                school_id=school_id,
                linked_entity_id=linked_id,
                is_active=True
            )
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()

            # Automatically log in the user after registration
            session['user_id'] = new_user.id
            session['username'] = new_user.username
            session['user_role'] = new_user.user_type
            session['linked_entity_id'] = new_user.linked_entity_id

            flash(f'Account created successfully! Welcome to StratLearn, {new_user.username}.', 'success')

            if user_type_str == "Student":
                return redirect(url_for('student.dashboard'))
            elif user_type_str == "Employee":
                return redirect(url_for('teacher.dashboard'))
            elif user_type_str == "Parent":
                return redirect(url_for('parent.dashboard'))

        except Exception as e:
            db.session.rollback()
            flash(f'Failed to create account: {str(e)}', 'danger')

    classes = SchoolClass.query.all()
    return render_template('auth/signup.html', classes=classes)


@auth_bp.route('/parent-signup', methods=['GET', 'POST'])
def parent_signup():
    """Legacy redirect to unified signup route."""
    return redirect(url_for('auth.signup'))


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))
