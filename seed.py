import sys
from datetime import date, time
from sqlalchemy import create_engine, text
from app import create_app
from app.config import Config
from app.models import (
    db, Institute, SchoolClass, Section, Employee, Student, StudentEnrollment, Guardian, GuardianStudent, User, School, AcademicSession, Setting, Subject, SubjectClass, Period, Timetable,
    BehaviourCategory, BehaviourRecord, SkillDefinition, SkillAssessment
)
from app.services.setting_service import initialize_default_settings
from app.services.subject_service import assign_subject_to_class

def ensure_database_exists():
    """Ensure the target MySQL database exists before SQLAlchemy creates tables."""
    db_uri = Config.SQLALCHEMY_DATABASE_URI
    if 'mysql' in db_uri:
        try:
            base_uri, db_name = db_uri.rsplit('/', 1)
            if '?' in db_name:
                db_name = db_name.split('?')[0]
            
            engine = create_engine(base_uri)
            with engine.connect() as conn:
                conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{db_name}` DEFAULT CHARACTER SET utf8mb4;"))
                conn.commit()
            print(f"✓ MySQL Database `{db_name}` verified/created successfully.")
        except Exception as e:
            print(f"⚠ Database pre-check warning: {e}")
            print("Will attempt direct connection...")

def apply_schema_migrations():
    """Safely apply missing column alterations for pre-existing MySQL tables."""
    db_uri = Config.SQLALCHEMY_DATABASE_URI
    try:
        engine = create_engine(db_uri)
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
        with engine.connect() as conn:
            for stmt in alter_statements:
                try:
                    conn.execute(text(stmt))
                    conn.commit()
                except Exception:
                    pass
    except Exception as e:
        print(f"⚠ Migration pre-check notice: {e}")

def seed_database():
    ensure_database_exists()
    apply_schema_migrations()
    app = create_app()

    with app.app_context():
        print("Creating all database tables...")
        db.create_all()

        # 1. Seed School Profile
        school = School.query.first()
        if not school:
            school = School(
                name="TPS School",
                school_code="TPS-001",
                email="contact@tps.edu",
                phone="+91 98765 43210",
                address="123 Education Boulevard",
                city="Bengaluru",
                state="Karnataka",
                country="India",
                postal_code="560001",
                principal_name="Dr. Academic Director",
                academic_session="2026-27"
            )
            db.session.add(school)
            db.session.commit()
            print(f"✓ School Profile created: '{school.name}' ({school.school_code}) [Session: {school.academic_session}]")

        # 2. Seed Institute
        institute = Institute.query.filter_by(institute_name="TPS").first()
        if not institute:
            institute = Institute(
                institute_name="TPS",
                email_address="contact@tps.edu",
                email_verification_status=True
            )
            db.session.add(institute)
            db.session.commit()

        # 3. Seed Academic Session
        active_sess = AcademicSession.query.filter_by(name="2026-2027").first()
        if not active_sess:
            active_sess = AcademicSession(
                name="2026-2027",
                start_date=date(2026, 4, 1),
                end_date=date(2027, 3, 31),
                is_active=True
            )
            db.session.add(active_sess)
            db.session.commit()

        initialize_default_settings()

        # 4. Seed Classes & Sections
        c9 = SchoolClass.query.filter_by(academic_session_id=active_sess.id, name="9").first()
        sec_map_c9 = {}
        if not c9:
            c9 = SchoolClass(
                academic_session_id=active_sess.id,
                institute_id=institute.id,
                name="9",
                display_name="Grade 9",
                numeric_order=9,
                description="High School Grade 9 Academic Track",
                is_active=True
            )
            db.session.add(c9)
            db.session.commit()

            for sec_code, cap in [('A', 40), ('B', 40), ('E', 35)]:
                sec = Section(
                    class_id=c9.id,
                    name=sec_code,
                    display_name=f"Section {sec_code}",
                    capacity=cap,
                    is_active=True
                )
                db.session.add(sec)
                db.session.commit()
                sec_map_c9[sec_code] = sec
        else:
            for sec in c9.sections:
                sec_map_c9[sec.name] = sec

        c10 = SchoolClass.query.filter_by(academic_session_id=active_sess.id, name="10").first()
        sec_map_c10 = {}
        if not c10:
            c10 = SchoolClass(
                academic_session_id=active_sess.id,
                institute_id=institute.id,
                name="10",
                display_name="Grade 10",
                numeric_order=10,
                description="Secondary School Leaving Track",
                is_active=True
            )
            db.session.add(c10)
            db.session.commit()

            for sec_code, cap in [('A', 40), ('B', 40)]:
                sec = Section(
                    class_id=c10.id,
                    name=sec_code,
                    display_name=f"Section {sec_code}",
                    capacity=cap,
                    is_active=True
                )
                db.session.add(sec)
                db.session.commit()
                sec_map_c10[sec_code] = sec
        else:
            for sec in c10.sections:
                sec_map_c10[sec.name] = sec

        # 5. Seed Module 4 Subjects
        default_subjects = [
            ("Mathematics", "MAT", "Maths", "core", "Standard Secondary Mathematics Curriculum"),
            ("Science", "SCI", "Sci", "core", "General Science covering Physics, Chemistry, Biology"),
            ("English", "ENG", "Eng", "core", "English Language, Communication and Literature"),
            ("Social Science", "SST", "SocSci", "core", "History, Geography, Political Science, Economics"),
            ("Computer Science", "CS", "Comp", "elective", "Foundations of Computer Science & Programming"),
            ("Physical Education", "PE", "PhysEd", "co_curricular", "Physical Fitness, Athletics, and Health Education")
        ]

        seeded_subjects = {}
        for name, code, short_name, stype, desc in default_subjects:
            sub = Subject.query.filter_by(name=name).first()
            if not sub:
                sub = Subject(
                    name=name,
                    code=code,
                    short_name=short_name,
                    subject_type=stype,
                    description=desc,
                    is_active=True
                )
                db.session.add(sub)
                db.session.commit()
            seeded_subjects[name] = sub

        for cls in [c9, c10]:
            if cls:
                for sub_name in ["Mathematics", "Science", "English", "Social Science", "Computer Science"]:
                    sub_obj = seeded_subjects.get(sub_name)
                    if sub_obj:
                        try:
                            assign_subject_to_class(sub_obj.id, cls.id)
                        except Exception:
                            pass

        # 6. Seed Module 5 Staff Employees
        staff_data = [
            ("257448", "Virat", "teach", None, "Academic", "Mathematics Teacher", "Full-time", True, "virat.teacher@stratlearn.com", "+91 98765 11111", "Male"),
            ("EMP001", "Academic", "Director", "Dr.", "Administration", "Principal", "Full-time", False, "principal@tps.edu", "+91 98765 22222", "Male"),
            ("TCH002", "Ananya", "Sen", "Mrs.", "Academic", "English Language Teacher", "Full-time", True, "ananya.sen@tps.edu", "+91 98765 33333", "Female"),
            ("ACC001", "Rajesh", "Kumar", "Mr.", "Accounts", "Senior Accountant", "Full-time", False, "accounts@tps.edu", "+91 98765 44444", "Male"),
            ("LIB001", "Priya", "Sharma", "Ms.", "Library", "Head Librarian", "Full-time", False, "library@tps.edu", "+91 98765 55555", "Female"),
            ("STF001", "Suresh", "Nair", "Mr.", "Administration", "Front Desk Receptionist", "Full-time", False, "reception@tps.edu", "+91 98765 66666", "Male")
        ]

        seeded_employees = {}
        for code, fname, lname, mname, dept, desig, etype, is_t, email, phone, gender in staff_data:
            emp = Employee.query.filter_by(registration_number=code).first()
            if not emp:
                emp = Employee(
                    institute_id=institute.id,
                    registration_number=code,
                    first_name=fname,
                    last_name=lname,
                    middle_name=mname,
                    full_name=f"{fname} {lname}" if lname else fname,
                    role=desig,
                    department=dept,
                    designation=desig,
                    employment_type=etype,
                    is_teacher=is_t,
                    is_active=True,
                    email_address=email,
                    mobile_phone_number=phone,
                    gender=gender,
                    date_of_joining=date(2025, 6, 1)
                )
                db.session.add(emp)
                db.session.commit()
                print(f"✓ Seeded Employee: '{emp.full_name}' ({code}) [{desig}]")
            seeded_employees[code] = emp

        # 7. Seed Module 6 Students & StudentEnrollments
        students_data = [
            ("ADM001", "Aarav", "Sharma", None, "Boy", date(2011, 5, 12), c9, sec_map_c9.get('A'), 1, "Sanjay Sharma", "Father", "+91 98111 00001"),
            ("ADM002", "Riya", "Verma", None, "Girl", date(2011, 8, 24), c9, sec_map_c9.get('A'), 2, "Meena Verma", "Mother", "+91 98111 00002"),
            ("ADM003", "Kabir", "Patel", None, "Boy", date(2011, 3, 15), c9, sec_map_c9.get('B'), 1, "Vikram Patel", "Father", "+91 98111 00003"),
            ("4838", "Virat", "Std", None, "Boy", date(2011, 11, 10), c9, sec_map_c9.get('A'), 5, "Parent Guard", "Father", "+91 98111 00004"),
            ("ADM004", "Ananya", "Roy", None, "Girl", date(2010, 2, 20), c10, sec_map_c10.get('A'), 1, "Debashis Roy", "Father", "+91 98111 00005")
        ]

        seeded_students = {}
        for adm_no, fname, lname, mname, gender, dob, cls_obj, sec_obj, roll, gname, grelation, gphone in students_data:
            stu = Student.query.filter_by(registration_number=adm_no).first()
            if not stu:
                stu = Student(
                    institute_id=institute.id,
                    class_id=cls_obj.id if cls_obj else None,
                    registration_number=adm_no,
                    first_name=fname,
                    last_name=lname,
                    middle_name=mname,
                    full_name=f"{fname} {lname}" if lname else fname,
                    gender=gender,
                    date_of_birth=dob,
                    admission_date=date(2026, 4, 1),
                    status="Active",
                    is_active=True,
                    guardian_name=gname,
                    guardian_relation=grelation,
                    guardian_phone=gphone
                )
                db.session.add(stu)
                db.session.commit()
                print(f"✓ Seeded Student: '{stu.full_name}' ({adm_no})")

                if cls_obj:
                    en = StudentEnrollment(
                        student_id=stu.id,
                        academic_session_id=active_sess.id,
                        class_id=cls_obj.id,
                        section_id=sec_obj.id if sec_obj else None,
                        roll_number=roll,
                        enrollment_date=date(2026, 4, 1),
                        is_current=True,
                        status="Active"
                    )
                    db.session.add(en)
                    db.session.commit()
            seeded_students[adm_no] = stu

        # 8. Seed Module 7 Guardians & GuardianStudent links
        guardians_data = [
            ("PAR001", "Rajesh", "Sharma", "Mr.", "sanjay.sharma@gmail.com", "+91 98111 00001", "Software Architect", [("ADM001", "Father", True), ("ADM002", "Uncle", False)]),
            ("PAR002", "Meena", "Verma", "Mrs.", "meena.verma@gmail.com", "+91 98111 00002", "Senior Accountant", [("ADM002", "Mother", True)]),
            ("PAR003", "Vikram", "Patel", "Mr.", "vikram.patel@gmail.com", "+91 98111 00003", "Civil Contractor", [("ADM003", "Father", True)]),
            ("PAR004", "Parent", "Guard", "Mr.", "parent.guard@gmail.com", "+91 98111 00004", "Business Executive", [("4838", "Father", True)])
        ]

        seeded_guardians = {}
        for gcode, fname, lname, mname, email, phone, occ, child_links in guardians_data:
            gdn = Guardian.query.filter_by(registration_number=gcode).first()
            if not gdn:
                gdn = Guardian(
                    institute_id=institute.id,
                    registration_number=gcode,
                    first_name=fname,
                    last_name=lname,
                    middle_name=mname,
                    full_name=f"{fname} {lname}" if lname else fname,
                    email_address=email,
                    mobile_phone_number=phone,
                    occupation=occ,
                    is_active=True,
                    status="Active"
                )
                db.session.add(gdn)
                db.session.commit()
                print(f"✓ Seeded Guardian: '{gdn.full_name}' ({gcode})")

                for child_adm, rel, is_prim in child_links:
                    stu_target = seeded_students.get(child_adm) or Student.query.filter_by(registration_number=child_adm).first()
                    if stu_target:
                        existing_link = GuardianStudent.query.filter_by(guardian_id=gdn.id, student_id=stu_target.id).first()
                        if not existing_link:
                            gs_link = GuardianStudent(
                                guardian_id=gdn.id,
                                student_id=stu_target.id,
                                relationship=rel,
                                is_primary=is_prim,
                                is_emergency_contact=True,
                                can_receive_notifications=True
                            )
                            db.session.add(gs_link)
                            db.session.commit()

            seeded_guardians[gcode] = gdn

        # 9. Seed Module 8 Period Time Slots & Sample Timetable Entries
        periods = Period.query.filter_by(academic_session_id=active_sess.id).order_by(Period.period_order.asc()).all()
        if not periods:
            default_slots = [
                ("Period 1", 1, time(9, 0), time(9, 45), "CLASS"),
                ("Period 2", 2, time(9, 45), time(10, 30), "CLASS"),
                ("Period 3", 3, time(10, 30), time(11, 15), "CLASS"),
                ("Short Break", 4, time(11, 15), time(11, 30), "BREAK"),
                ("Period 4", 5, time(11, 30), time(12, 15), "CLASS"),
                ("Lunch Break", 6, time(12, 15), time(13, 0), "BREAK"),
                ("Period 5", 7, time(13, 0), time(13, 45), "CLASS"),
                ("Period 6", 8, time(13, 45), time(14, 30), "CLASS"),
            ]
            for name, order, st, et, ptype in default_slots:
                p = Period(
                    academic_session_id=active_sess.id,
                    name=name,
                    period_order=order,
                    start_time=st,
                    end_time=et,
                    period_type=ptype,
                    is_active=True
                )
                db.session.add(p)
            db.session.commit()
            periods = Period.query.filter_by(academic_session_id=active_sess.id).order_by(Period.period_order.asc()).all()
            print(f"✓ Seeded {len(periods)} default period time slots.")

        # Seed sample timetable entries for Grade 9 Section A
        p_map = {p.period_order: p for p in periods}
        t_virat = seeded_employees.get("257448") or Employee.query.filter_by(registration_number="257448").first()
        t_ananya = seeded_employees.get("TCH002") or Employee.query.filter_by(registration_number="TCH002").first()
        sub_math = seeded_subjects.get("Mathematics") or Subject.query.filter_by(name="Mathematics").first()
        sub_sci = seeded_subjects.get("Science") or Subject.query.filter_by(name="Science").first()
        sub_eng = seeded_subjects.get("English") or Subject.query.filter_by(name="English").first()
        sub_cs = seeded_subjects.get("Computer Science") or Subject.query.filter_by(name="Computer Science").first()

        if c9 and p_map.get(1) and sub_math and t_virat:
            sec_a = sec_map_c9.get('A')
            sample_schedule = [
                ("Monday", 1, sub_math, t_virat, "Room 101"),
                ("Monday", 2, sub_sci, t_ananya, "Lab 1"),
                ("Monday", 3, sub_eng, t_ananya, "Room 101"),
                ("Monday", 4, None, None, None), # Break
                ("Monday", 5, sub_cs, t_virat, "Comp Lab"),
                ("Tuesday", 1, sub_sci, t_ananya, "Lab 1"),
                ("Tuesday", 2, sub_math, t_virat, "Room 101"),
            ]

            for day, p_ord, sub_o, emp_o, room in sample_schedule:
                period_obj = p_map.get(p_ord)
                if period_obj:
                    existing_entry = Timetable.query.filter_by(
                        academic_session_id=active_sess.id,
                        class_id=c9.id,
                        section_id=sec_a.id if sec_a else None,
                        day_of_week=day,
                        period_id=period_obj.id
                    ).first()

                    if not existing_entry:
                        entry_type = period_obj.period_type if period_obj.period_type in ['BREAK', 'FREE'] else "CLASS"
                        tt_entry = Timetable(
                            academic_session_id=active_sess.id,
                            class_id=c9.id,
                            section_id=sec_a.id if sec_a else None,
                            period_id=period_obj.id,
                            day_of_week=day,
                            subject_id=sub_o.id if sub_o else None,
                            employee_id=emp_o.id if emp_o else None,
                            room_number=room,
                            entry_type=entry_type,
                            status="PUBLISHED"
                        )
                        db.session.add(tt_entry)
            db.session.commit()
            print("✓ Seeded sample weekly timetable entries for Grade 9 - Section A.")

        # 10. Seed Sample Homework Assignments and Student Submissions
        from app.models import Homework, HomeworkSubmission
        existing_hw = Homework.query.filter_by(academic_session_id=active_sess.id, class_id=c9.id).first()
        if not existing_hw:
            math_sub = Subject.query.filter_by(name="Mathematics").first()
            sci_sub = Subject.query.filter_by(name="Science").first()
            teacher_emp = seeded_employees.get("257448") or Employee.query.filter_by(is_teacher=True).first()

            hw1 = Homework(
                school_id=school.id,
                academic_session_id=active_sess.id,
                teacher_id=teacher_emp.id if teacher_emp else 1,
                class_id=c9.id,
                section_id=sec_a.id if sec_a else None,
                subject_id=math_sub.id if math_sub else 1,
                title="Quadratic Equations Practice Set",
                description="Solve problems 1 to 15 from Chapter 4 worksheet. Show step-by-step factorization and formula method solutions.",
                assigned_date=active_sess.start_date,
                due_date=active_sess.start_date,
                max_marks=20.0,
                status="PUBLISHED"
            )
            db.session.add(hw1)
            db.session.flush()

            if sci_sub:
                hw2 = Homework(
                    school_id=school.id,
                    academic_session_id=active_sess.id,
                    teacher_id=teacher_emp.id if teacher_emp else 1,
                    class_id=c9.id,
                    section_id=sec_a.id if sec_a else None,
                    subject_id=sci_sub.id,
                    title="Cell Biology & Photosynthesis Report",
                    description="Write a detailed notes summary on light-dependent and light-independent reactions of photosynthesis.",
                    assigned_date=active_sess.start_date,
                    due_date=active_sess.start_date,
                    max_marks=50.0,
                    status="PUBLISHED"
                )
                db.session.add(hw2)

            # Sample student submission for student '4838' (Aarav Sharma)
            student_entity = seeded_students.get("4838")
            if student_entity:
                sub1 = HomeworkSubmission(
                    homework_id=hw1.id,
                    student_id=student_entity.id,
                    submitted_at=datetime.utcnow(),
                    status="REVIEWED",
                    submission_text="Completed all 15 quadratic equation problems. Verification attached.",
                    marks=18.5,
                    feedback="Excellent work on quadratic factorization! Double check sign in question 7.",
                    reviewed_at=datetime.utcnow(),
                    reviewed_by_id=teacher_emp.id if teacher_emp else 1
                )
                db.session.add(sub1)

            db.session.commit()
            print("✓ Seeded sample homework assignments and student submission for Grade 9.")

        # 11. Seed Portal Users linked to school.id and linked_entity_id
        admin_user = User.query.filter_by(username="admin").first()
        if not admin_user:
            admin_user = User(username="admin", user_type="Admin", school_id=school.id, linked_entity_id=None)
            admin_user.set_password("Admin@123")
            db.session.add(admin_user)
        else:
            admin_user.school_id = school.id

        teacher_emp = seeded_employees.get("257448")
        teacher_user = User.query.filter_by(username="teacher").first()
        if not teacher_user:
            teacher_user = User(username="teacher", user_type="Employee", school_id=school.id, linked_entity_id=teacher_emp.id if teacher_emp else None)
            teacher_user.set_password("Teacher@123")
            db.session.add(teacher_user)
        else:
            teacher_user.school_id = school.id
            if teacher_emp:
                teacher_user.linked_entity_id = teacher_emp.id

        student_entity = seeded_students.get("ADM002") or seeded_students.get("4838") or Student.query.first()
        student_user = User.query.filter_by(username="stu_std002").first() or User.query.filter_by(username="student").first()
        if not student_user:
            student_user = User(username="stu_std002", user_type="Student", school_id=school.id, linked_entity_id=student_entity.id if student_entity else None)
            db.session.add(student_user)
        student_user.username = "stu_std002"
        student_user.user_type = "Student"
        student_user.school_id = school.id
        student_user.set_password("student")
        if student_entity:
            student_user.linked_entity_id = student_entity.id
        print(f"✓ Seeded/Reset Student User Account: 'stu_std002' / 'student' [Linked Student: '{student_entity.full_name if student_entity else ''}']")

        parent_gdn = seeded_guardians.get("PAR002") or seeded_guardians.get("PAR001") or Guardian.query.first()
        parent_user = User.query.filter_by(username="par_par002").first() or User.query.filter_by(username="parent").first()
        if not parent_user:
            parent_user = User(username="par_par002", user_type="Parent", school_id=school.id, linked_entity_id=parent_gdn.id if parent_gdn else None)
            db.session.add(parent_user)
        
        parent_user.username = "par_par002"
        parent_user.school_id = school.id
        parent_user.user_type = "Parent"
        parent_user.set_password("Parent@123")
        if parent_gdn:
            parent_user.linked_entity_id = parent_gdn.id
        print(f"✓ Seeded/Reset Parent User Account: 'par_par002' / 'Parent@123' [Linked Guardian: '{parent_gdn.full_name if parent_gdn else ''}']")

        # Seed sample Behaviour Observations & Skill Assessments for Student 4838
        if student_entity and teacher_emp:
            active_sess = AcademicSession.query.filter_by(is_active=True).first()
            cat_pos = BehaviourCategory.query.filter_by(name="Positive Conduct").first()
            cat_part = BehaviourCategory.query.filter_by(name="Classroom Participation").first()
            cat_disc = BehaviourCategory.query.filter_by(name="Discipline").first()

            if cat_pos and BehaviourRecord.query.filter_by(student_id=student_entity.id).count() == 0:
                rec1 = BehaviourRecord(
                    student_id=student_entity.id,
                    assessor_id=teacher_emp.id,
                    academic_session_id=active_sess.id if active_sess else 1,
                    class_id=student_entity.class_id,
                    category_id=cat_pos.id,
                    type='POSITIVE',
                    title='Exemplary Group Peer Assistance',
                    description='Helped classmates organize and review science experiment materials during lab session.',
                    date=date(2026, 8, 10),
                    severity='LOW',
                    visibility='BOTH'
                )
                rec2 = BehaviourRecord(
                    student_id=student_entity.id,
                    assessor_id=teacher_emp.id,
                    academic_session_id=active_sess.id if active_sess else 1,
                    class_id=student_entity.class_id,
                    category_id=cat_part.id,
                    type='POSITIVE',
                    title='Active Debate Contribution',
                    description='Consistently contributed well-researched arguments during English literature discussion.',
                    date=date(2026, 8, 12),
                    severity='LOW',
                    visibility='BOTH'
                )
                db.session.add_all([rec1, rec2])

            sk_comm = SkillDefinition.query.filter_by(name="Communication").first()
            sk_team = SkillDefinition.query.filter_by(name="Teamwork").first()
            sk_prob = SkillDefinition.query.filter_by(name="Problem Solving").first()

            if sk_comm and SkillAssessment.query.filter_by(student_id=student_entity.id).count() == 0:
                ass1 = SkillAssessment(
                    student_id=student_entity.id,
                    skill_id=sk_comm.id,
                    assessor_id=teacher_emp.id,
                    academic_session_id=active_sess.id if active_sess else 1,
                    class_id=student_entity.class_id,
                    rating=4,
                    observation='Demonstrates clear verbal articulation during classroom presentations.',
                    assessment_date=date(2026, 8, 11)
                )
                ass2 = SkillAssessment(
                    student_id=student_entity.id,
                    skill_id=sk_team.id,
                    assessor_id=teacher_emp.id,
                    academic_session_id=active_sess.id if active_sess else 1,
                    class_id=student_entity.class_id,
                    rating=5,
                    observation='Outstanding team player and collaborative attitude in group projects.',
                    assessment_date=date(2026, 8, 11)
                )
                ass3 = SkillAssessment(
                    student_id=student_entity.id,
                    skill_id=sk_prob.id,
                    assessor_id=teacher_emp.id,
                    academic_session_id=active_sess.id if active_sess else 1,
                    class_id=student_entity.class_id,
                    rating=4,
                    observation='Good analytical thinking when solving math & logic problems.',
                    assessment_date=date(2026, 8, 11)
                )
                db.session.add_all([ass1, ass2, ass3])

        # 12. Seed Module 11 Fee Structure, Invoices, Payments, and Receipts
        from app.models import FeeType, FeeStructure, FeeComponent, FeeInvoice, FeeInvoiceItem, Payment, Receipt
        if c9 and student_entity:
            fs = FeeStructure.query.filter_by(class_id=c9.id, academic_session_id=active_sess.id).first()
            if not fs:
                fs = FeeStructure(
                    academic_session_id=active_sess.id,
                    class_id=c9.id,
                    name="Grade 9 Standard Annual Fee Structure 2026-27",
                    description="Standard academic fee structure covering tuition, exams, library, and activity fees.",
                    is_active=True
                )
                db.session.add(fs)
                db.session.flush()

                ft_tuit = FeeType.query.filter_by(name="Tuition Fee").first()
                ft_exam = FeeType.query.filter_by(name="Examination Fee").first()
                ft_act = FeeType.query.filter_by(name="Activity Fee").first()

                if ft_tuit:
                    db.session.add(FeeComponent(fee_structure_id=fs.id, fee_type_id=ft_tuit.id, amount=12000.0, frequency="YEARLY"))
                if ft_exam:
                    db.session.add(FeeComponent(fee_structure_id=fs.id, fee_type_id=ft_exam.id, amount=2000.0, frequency="YEARLY"))
                if ft_act:
                    db.session.add(FeeComponent(fee_structure_id=fs.id, fee_type_id=ft_act.id, amount=1000.0, frequency="YEARLY"))
                db.session.commit()
                print("✓ Seeded Grade 9 Fee Structure and components.")

            # Seed sample invoice for student 4838 if none exists
            inv = FeeInvoice.query.filter_by(student_id=student_entity.id, academic_session_id=active_sess.id).first()
            if not inv:
                from app.services.fee_service import generate_student_invoice, record_payment
                try:
                    inv = generate_student_invoice(
                        student_id=student_entity.id,
                        fee_structure_id=fs.id,
                        discount_amount=1000.0,
                        discount_reason="Academic Merit Scholarship",
                        session_id=active_sess.id
                    )
                    print(f"✓ Seeded Invoice #{inv.invoice_number} for student '{student_entity.full_name}' (Total: ₹{inv.total_payable}).")

                    # Record a sample partial payment of ₹5,000
                    pay = record_payment(
                        invoice_id=inv.id,
                        amount=5000.0,
                        payment_method="UPI",
                        transaction_reference="UPI/884729104",
                        notes="First Term Partial Fee Payment"
                    )
                    print(f"✓ Seeded partial payment of ₹5,000 for invoice #{inv.invoice_number}.")
                except Exception as ex:
                    print(f"⚠ Notice seeding student invoice/payment: {ex}")

            # Seed Module 12 Financial Categories & Sample Transactions
            from app.models.finance import FinanceCategory, FinancialTransaction
            from app.services.finance_service import create_category, create_manual_transaction, sync_all_fee_payments_to_finance

            income_cats = [
                ("Student Fees", "Student tuition and academic fee collections"),
                ("Admission Fees", "New student registration and admission fees"),
                ("Transport Income", "School bus and transport service income"),
                ("Event Income", "Annual sports day, cultural fest, and event income"),
                ("Donations", "Alumni and trust financial donations"),
                ("Miscellaneous Income", "Other non-fee school revenue")
            ]
            for c_name, c_desc in income_cats:
                try:
                    create_category(c_name, "INCOME", c_desc)
                except ValueError:
                    pass

            expense_cats = [
                ("Salaries", "Teacher and administrative staff payroll expenses"),
                ("Electricity", "Campus electricity and power utility bills"),
                ("Maintenance", "Building, plumbing, and IT infrastructure repair"),
                ("Stationery", "Office paper, chalk, printing, and exam supplies"),
                ("Transport", "Bus fuel, maintenance, and vehicle insurance"),
                ("Events", "Sports day, annual function, and workshop expenses"),
                ("Infrastructure", "Classroom furniture and lab equipment upgrades"),
                ("Supplies", "Cleaning, sanitation, and daily operational supplies"),
                ("Other Expenses", "Miscellaneous operational expenditures")
            ]
            for c_name, c_desc in expense_cats:
                try:
                    create_category(c_name, "EXPENSE", c_desc)
                except ValueError:
                    pass

            # Seed sample manual income & expense transactions
            spon_cat = FinanceCategory.query.filter_by(name="Event Income", type="INCOME").first()
            if spon_cat and not FinancialTransaction.query.filter_by(transaction_number="TXN-2026-SPONSOR").first():
                try:
                    create_manual_transaction(
                        category_id=spon_cat.id,
                        transaction_type="INCOME",
                        amount=25000.00,
                        transaction_date=date.today(),
                        description="Annual Sports Day Corporate Sponsorship",
                        payment_method="UPI",
                        reference_number="UPI/SPONSOR/99042",
                        vendor_or_payer="Apex Tech Solutions",
                        session_id=active_sess.id
                    )
                    print("✓ Seeded sample income transaction: Sports Day Sponsorship ₹25,000.00.")
                except Exception as ex:
                    print(f"⚠ Notice seeding income txn: {ex}")

            elec_cat = FinanceCategory.query.filter_by(name="Electricity", type="EXPENSE").first()
            if elec_cat and not FinancialTransaction.query.filter_by(transaction_number="TXN-2026-ELEC").first():
                try:
                    create_manual_transaction(
                        category_id=elec_cat.id,
                        transaction_type="EXPENSE",
                        amount=14500.00,
                        transaction_date=date.today(),
                        description="Campus Monthly Electricity Bill Payment",
                        payment_method="BANK_TRANSFER",
                        reference_number="NEFT-BESCOM-4921",
                        vendor_or_payer="BESCOM Utility Board",
                        session_id=active_sess.id
                    )
                    print("✓ Seeded sample expense transaction: Electricity Bill ₹14,500.00.")
                except Exception as ex:
                    print(f"⚠ Notice seeding expense txn: {ex}")

            # Sync all fee payments into Module 12 Accounts & Finance income
            synced_count = sync_all_fee_payments_to_finance(session_id=active_sess.id)
            print(f"✓ Synced {synced_count} student fee payment(s) to financial income.")

            # Seed Module 13 Salary & Payroll Components, Structure & Batch Payroll
            from app.models.payroll import SalaryComponent, SalaryStructure, PayrollRecord
            from app.services.payroll_service import (
                create_salary_component, create_salary_structure, assign_salary_structure,
                generate_batch_payroll, approve_payroll, record_salary_payment
            )

            # Components
            c_basic = SalaryComponent.query.filter_by(name="Basic Salary").first() or create_salary_component("Basic Salary", "EARNING", "FIXED_AMOUNT", 35000.00, description="Core base salary")
            c_hra = SalaryComponent.query.filter_by(name="House Rent Allowance (HRA)").first() or create_salary_component("House Rent Allowance (HRA)", "EARNING", "PERCENTAGE", 20.00, description="HRA allowance rate")
            c_trans = SalaryComponent.query.filter_by(name="Transport Allowance").first() or create_salary_component("Transport Allowance", "EARNING", "FIXED_AMOUNT", 2500.00, description="Commute conveyance allowance")
            c_ptax = SalaryComponent.query.filter_by(name="Professional Tax").first() or create_salary_component("Professional Tax", "DEDUCTION", "FIXED_AMOUNT", 200.00, description="Statutory professional tax deduction")

            # Structure
            struct = SalaryStructure.query.filter_by(name="Senior Academic Staff Grade A").first()
            if not struct:
                struct = create_salary_structure(
                    "Senior Academic Staff Grade A",
                    "Standard pay grade structure for senior teachers and department heads",
                    component_items=[
                        {'component_id': c_basic.id, 'calculation_type': 'FIXED_AMOUNT', 'amount_or_percentage': 35000.00},
                        {'component_id': c_hra.id, 'calculation_type': 'PERCENTAGE', 'amount_or_percentage': 20.00},
                        {'component_id': c_trans.id, 'calculation_type': 'FIXED_AMOUNT', 'amount_or_percentage': 2500.00},
                        {'component_id': c_ptax.id, 'calculation_type': 'FIXED_AMOUNT', 'amount_or_percentage': 200.00}
                    ]
                )
                print("✓ Seeded Senior Academic Staff Salary Structure.")

            # Assign structure to teachers
            teachers = Employee.query.filter_by(is_teacher=True, is_active=True).all()
            for tch in teachers:
                assign_salary_structure(tch.id, struct.id, effective_from=date.today())
            print(f"✓ Assigned salary structure to {len(teachers)} teacher(s).")

            # Generate sample payroll for current period
            curr_period = date.today().strftime('%Y-%m')
            payrolls = generate_batch_payroll(curr_period, session_id=active_sess.id)
            if payrolls:
                print(f"✓ Seeded batch payroll for {len(payrolls)} staff member(s) for period '{curr_period}'.")
                # Approve and record salary payment for first teacher
                p_first = payrolls[0]
                approve_payroll(p_first.id)
                p_paid = record_salary_payment(p_first.id, payment_method="BANK_TRANSFER", payment_reference=f"NEFT-SAL-{p_first.id:04d}")
                print(f"✓ Seeded paid salary of ₹{p_paid.net_salary:.2f} for '{p_paid.employee.full_name}' and synced to Accounts & Finance.")

            # Seed Module 14 Attendance Records (Students & Employees)
            from app.services.attendance_service import save_bulk_class_student_attendance, save_bulk_employee_attendance
            from app.models import StudentEnrollment, SchoolClass
            import random

            classes = SchoolClass.query.filter_by(academic_session_id=active_sess.id).all()
            for cls in classes:
                enrollments = StudentEnrollment.query.filter_by(class_id=cls.id, is_current=True).all()
                if not enrollments:
                    continue

                # Seed last 5 working days attendance
                for days_back in range(5):
                    d_obj = date.today() - timedelta(days=days_back)
                    if d_obj.weekday() in (5, 6): # Skip weekends
                        continue

                    stu_list = []
                    for idx, en in enumerate(enrollments):
                        # Give first student absent/late for testing low attendance matrix
                        if idx == 0 and days_back % 2 == 1:
                            st = 'ABSENT'
                        elif idx == 1 and days_back == 1:
                            st = 'LATE'
                        else:
                            st = 'PRESENT'

                        stu_list.append({
                            'student_id': en.student_id,
                            'status': st,
                            'remarks': 'Regular school attendance' if st == 'PRESENT' else 'Excused'
                        })

                    save_bulk_class_student_attendance(
                        class_id=cls.id,
                        section_id=enrollments[0].section_id,
                        attendance_date=d_obj,
                        student_attendance_list=stu_list,
                        recorded_by_id=admin_user.id,
                        session_id=active_sess.id
                    )

            # Seed Employee Attendance for last 5 working days
            all_emps = Employee.query.filter_by(is_active=True).all()
            for days_back in range(5):
                d_obj = date.today() - timedelta(days=days_back)
                if d_obj.weekday() in (5, 6):
                    continue

                emp_list = []
                for emp in all_emps:
                    emp_list.append({
                        'employee_id': emp.id,
                        'status': 'PRESENT',
                        'remarks': 'On duty'
                    })

                save_bulk_employee_attendance(
                    attendance_date=d_obj,
                    employee_attendance_list=emp_list,
                    recorded_by_id=admin_user.id
                )

            print("✓ Seeded Module 14 Student and Employee daily attendance records for recent working days.")

            # ==========================================
            # MODULE 15: QUESTION BANK & QUESTION PAPER SEEDING
            # ==========================================
            from app.models.question_bank import Question, QuestionPaper, QuestionPaperSection, QuestionPaperQuestion
            from app.services.question_bank_service import create_question, create_question_paper, add_question_to_paper_section, finalize_question_paper

            if Question.query.count() == 0:
                # Retrieve first class and subject
                first_cls = SchoolClass.query.first()
                first_subj = Subject.query.first()

                c_id = first_cls.id if first_cls else 1
                s_id = first_subj.id if first_subj else 1

                # 1. Seed Questions
                q1 = create_question(
                    class_id=c_id,
                    subject_id=s_id,
                    question_text="Which of the following is the SI unit of force?",
                    question_type="MCQ",
                    difficulty="EASY",
                    marks=1.0,
                    chapter="Laws of Motion",
                    option_a="Joule",
                    option_b="Newton",
                    option_c="Watt",
                    option_d="Pascal",
                    correct_option="B",
                    explanation="Force is measured in Newtons (N) in the SI system.",
                    tags="NCERT,Important",
                    created_by_id=admin_user.id
                )

                q2 = create_question(
                    class_id=c_id,
                    subject_id=s_id,
                    question_text="What is the acceleration due to gravity on the surface of the Earth?",
                    question_type="MCQ",
                    difficulty="EASY",
                    marks=1.0,
                    chapter="Gravitation",
                    option_a="9.8 m/s²",
                    option_b="8.9 m/s²",
                    option_c="10.8 m/s²",
                    option_d="9.8 km/s²",
                    correct_option="A",
                    explanation="Standard g value is approximately 9.8 m/s².",
                    tags="NCERT,Conceptual",
                    created_by_id=admin_user.id
                )

                q3 = create_question(
                    class_id=c_id,
                    subject_id=s_id,
                    question_text="State Newton's Second Law of Motion and derive the formula F = ma.",
                    question_type="SHORT_ANSWER",
                    difficulty="MEDIUM",
                    marks=3.0,
                    chapter="Laws of Motion",
                    answer_text="Newton's 2nd Law states that the rate of change of momentum is proportional to applied force. F = dp/dt = m(dv/dt) = ma.",
                    explanation="Include statement, momentum definition p=mv, and derivative step.",
                    tags="NCERT,Important,HOTS",
                    created_by_id=admin_user.id
                )

                q4 = create_question(
                    class_id=c_id,
                    subject_id=s_id,
                    question_text="Explain the principle of conservation of momentum with a practical example.",
                    question_type="LONG_ANSWER",
                    difficulty="HARD",
                    marks=5.0,
                    chapter="Laws of Motion",
                    answer_text="Total momentum of an isolated system remains constant in absence of external force. Example: Recoil of gun, rocket propulsion.",
                    explanation="Define isolated system, state formula m1u1 + m2u2 = m1v1 + m2v2, and elaborate recoil example.",
                    tags="NCERT,Board-style",
                    created_by_id=admin_user.id
                )

                # 2. Create and finalize a Question Paper
                paper = create_question_paper(
                    title="Mid-Term Physics Assessment 2026",
                    class_id=c_id,
                    subject_id=s_id,
                    instructions="1. All questions are compulsory. 2. Write neat and clean steps.",
                    duration_minutes=90,
                    created_by_id=admin_user.id,
                    session_id=active_sess.id
                )

                # Add questions to Section A and B
                sec_a = paper.sections[0]
                sec_b = paper.sections[1]

                add_question_to_paper_section(sec_a.id, q1.id, 1.0)
                add_question_to_paper_section(sec_a.id, q2.id, 1.0)
                add_question_to_paper_section(sec_b.id, q3.id, 3.0)
                add_question_to_paper_section(sec_b.id, q4.id, 5.0)

                # Finalize paper to create immutable snapshots
                finalize_question_paper(paper.id)

                print("✓ Seeded Module 15 Question Bank items and finalized Question Paper with snapshots.")

            # ==========================================
            # MODULE 16: EXAMINATION MANAGEMENT SEEDING
            # ==========================================
            from app.models.examination import ExamType, Examination, ExaminationClass, ExaminationSubject, ExaminationResult, ExamOverallResult, GradeRule
            from app.services.examination_service import create_exam_type, get_grade_rules, create_examination, assign_classes_to_exam, add_exam_subject, save_bulk_exam_marks, calculate_and_publish_exam_results

            if Examination.query.count() == 0:
                # 1. Seed Exam Types
                et_mid = create_exam_type("Mid-Term Examination", "MID", "Official Mid-Year Academic Assessment")
                et_annual = create_exam_type("Annual Examination", "ANN", "Year-End Final Assessment")
                create_exam_type("Unit Test", "UT", "Periodic Chapter Assessment")

                # Ensure default grade rules exist
                get_grade_rules(active_only=True)

                first_cls = SchoolClass.query.first()
                first_subj = Subject.query.first()
                c_id = first_cls.id if first_cls else 1
                s_id = first_subj.id if first_subj else 1

                # 2. Create Master Examination
                mid_exam = create_examination(
                    name="Mid-Term Assessment 2026",
                    academic_session_id=active_sess.id,
                    exam_type_id=et_mid.id,
                    description="Mid-term assessment covering Chapters 1 to 4.",
                    start_date=date(2026, 9, 15),
                    end_date=date(2026, 9, 25),
                    created_by_id=admin_user.id
                )

                # Assign Class
                assign_classes_to_exam(mid_exam.id, [c_id])

                # Get finalized question paper from Module 15 if present
                from app.models.question_bank import QuestionPaper
                p_obj = QuestionPaper.query.filter_by(status='FINAL').first()
                p_id = p_obj.id if p_obj else None

                # Schedule Exam Subject
                es_sub = add_exam_subject(
                    exam_id=mid_exam.id,
                    class_id=c_id,
                    subject_id=s_id,
                    exam_date=date(2026, 9, 16),
                    start_time=time(9, 30),
                    end_time=time(12, 30),
                    max_marks=100.0,
                    pass_marks=33.0,
                    question_paper_id=p_id
                )

                # Enter marks for enrolled students
                students_cls = Student.query.filter_by(class_id=c_id).all()
                if students_cls:
                    marks_payload = []
                    for idx, st in enumerate(students_cls):
                        if idx == len(students_cls) - 1 and len(students_cls) > 1:
                            # Mark last student absent
                            marks_payload.append({'student_id': st.id, 'attendance_status': 'ABSENT', 'marks_obtained': None})
                        else:
                            # Assigned realistic marks
                            assigned_m = 75.0 + (idx * 5.0)
                            if assigned_m > 95.0:
                                assigned_m = 92.0
                            marks_payload.append({'student_id': st.id, 'attendance_status': 'PRESENT', 'marks_obtained': assigned_m})

                    save_bulk_exam_marks(es_sub.id, marks_payload, entered_by_id=admin_user.id)
                    calculate_and_publish_exam_results(mid_exam.id, approved_by_id=admin_user.id)

                print("✓ Seeded Module 16 Examination master, subjects, bulk marks, and published results.")

        db.session.commit()
        print("\n🎉 Database initialization and seeding completed successfully!")

if __name__ == '__main__':
    seed_database()
