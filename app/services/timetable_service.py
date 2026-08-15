import csv
import io
from datetime import datetime, time
from app.models import db, Timetable, Period, SchoolClass, Section, Subject, Employee, Student, StudentEnrollment, AcademicSession
from app.services.academic_service import get_active_academic_session

DAYS_OF_WEEK = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
ENTRY_TYPES = ['CLASS', 'BREAK', 'FREE']
TIMETABLE_STATUSES = ['DRAFT', 'PUBLISHED', 'ARCHIVED']

def get_all_periods_for_session(session_id):
    """Retrieve all active periods for an academic session ordered by period_order."""
    return Period.query.filter_by(academic_session_id=session_id, is_active=True).order_by(Period.period_order.asc()).all()

def initialize_default_periods_for_session(session_id):
    """
    Seed 8 standard period time slots for an academic session if none exist.
    """
    existing = Period.query.filter_by(academic_session_id=session_id).first()
    if existing:
        return get_all_periods_for_session(session_id)

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

    periods_created = []
    for name, order, st, et, ptype in default_slots:
        p = Period(
            academic_session_id=session_id,
            name=name,
            period_order=order,
            start_time=st,
            end_time=et,
            period_type=ptype,
            is_active=True
        )
        db.session.add(p)
        periods_created.append(p)

    db.session.commit()
    return periods_created

def check_conflicts(session_id, day_of_week, period_id, class_id, section_id=None, teacher_id=None, room_number=None, exclude_entry_id=None):
    """
    Authoritative Server-Side Conflict Detection Engine.
    Checks:
    1. Class Conflict: Same class/section cannot have two entries at same Day + Period.
    2. Teacher Conflict: Same teacher cannot teach two classes at same Day + Period.
    3. Room Conflict: Same room cannot be assigned twice at same Day + Period.
    Returns list of conflict warning messages.
    """
    conflicts = []

    # 1. Class Conflict Check
    class_q = Timetable.query.filter_by(
        academic_session_id=session_id,
        class_id=class_id,
        day_of_week=day_of_week,
        period_id=period_id
    )
    if section_id:
        class_q = class_q.filter(
            (Timetable.section_id == section_id) | (Timetable.section_id.is_(None))
        )
    if exclude_entry_id:
        class_q = class_q.filter(Timetable.id != exclude_entry_id)

    class_conflict_entry = class_q.first()
    if class_conflict_entry:
        sub_name = class_conflict_entry.subject.name if class_conflict_entry.subject else class_conflict_entry.entry_type
        conflicts.append(f"Class Conflict: {class_conflict_entry.school_class.display_name} already has '{sub_name}' scheduled on {day_of_week} during {class_conflict_entry.period.name}.")

    # 2. Teacher Conflict Check (only for teaching entries)
    if teacher_id:
        teacher_q = Timetable.query.filter_by(
            academic_session_id=session_id,
            employee_id=teacher_id,
            day_of_week=day_of_week,
            period_id=period_id
        )
        if exclude_entry_id:
            teacher_q = teacher_q.filter(Timetable.id != exclude_entry_id)

        teacher_conflict_entry = teacher_q.first()
        if teacher_conflict_entry:
            t_name = teacher_conflict_entry.teacher.full_name if teacher_conflict_entry.teacher else "Teacher"
            c_name = teacher_conflict_entry.school_class.display_name
            sec_name = f" - {teacher_conflict_entry.section.display_name}" if teacher_conflict_entry.section else ""
            conflicts.append(f"Teacher Conflict: {t_name} is already teaching {c_name}{sec_name} on {day_of_week} during {teacher_conflict_entry.period.name}.")

    # 3. Room Conflict Check (if room_number provided)
    if room_number and room_number.strip():
        room_clean = room_number.strip().upper()
        room_q = Timetable.query.filter_by(
            academic_session_id=session_id,
            day_of_week=day_of_week,
            period_id=period_id
        ).filter(db.func.upper(Timetable.room_number) == room_clean)
        
        if exclude_entry_id:
            room_q = room_q.filter(Timetable.id != exclude_entry_id)

        room_conflict_entry = room_q.first()
        if room_conflict_entry:
            c_name = room_conflict_entry.school_class.display_name
            conflicts.append(f"Room Conflict: '{room_clean}' is already assigned to {c_name} on {day_of_week} during {room_conflict_entry.period.name}.")

    return conflicts

def get_class_timetable(class_id, section_id=None, session_id=None):
    """
    Returns weekly timetable matrix dictionary for a class/section:
    matrix["Day_PeriodID"] = Timetable object
    """
    if not session_id:
        act_sess = get_active_academic_session()
        session_id = act_sess.id if act_sess else None

    query = Timetable.query.filter_by(academic_session_id=session_id, class_id=class_id)
    if section_id:
        query = query.filter((Timetable.section_id == section_id) | (Timetable.section_id.is_(None)))

    entries = query.all()
    matrix = {}
    for en in entries:
        matrix[f"{en.day_of_week}_{en.period_id}"] = en
    return matrix

def get_teacher_timetable(teacher_id, session_id=None):
    """Returns all timetable entries for a teacher/employee."""
    if not session_id:
        act_sess = get_active_academic_session()
        session_id = act_sess.id if act_sess else None

    return Timetable.query.filter_by(academic_session_id=session_id, employee_id=teacher_id)\
                          .order_by(Timetable.day_of_week.asc(), Timetable.period_id.asc()).all()

def get_student_timetable(student_id, session_id=None):
    """
    Resolves student's active StudentEnrollment and returns class timetable.
    """
    if not session_id:
        act_sess = get_active_academic_session()
        session_id = act_sess.id if act_sess else None

    enrollment = StudentEnrollment.query.filter_by(student_id=student_id, academic_session_id=session_id, is_current=True).first()
    if not enrollment:
        return {}

    return get_class_timetable(class_id=enrollment.class_id, section_id=enrollment.section_id, session_id=session_id)

def create_or_update_timetable_entry(class_id, day_of_week, period_id, section_id=None,
                                     subject_id=None, teacher_id=None, room_number=None,
                                     entry_type="CLASS", status="DRAFT", session_id=None, entry_id=None):
    """
    Create or update a timetable entry with conflict validation.
    """
    if not session_id:
        act_sess = get_active_academic_session()
        if not act_sess:
            raise ValueError("No active academic session found.")
        session_id = act_sess.id

    # Validate Class and Section
    target_class = SchoolClass.query.get(class_id)
    if not target_class:
        raise ValueError("Selected Class does not exist.")

    if section_id:
        sec = Section.query.get(section_id)
        if not sec:
            raise ValueError("Selected Section does not exist.")
        if sec.class_id != target_class.id:
            raise ValueError(f"Section '{sec.display_name}' does not belong to Class '{target_class.display_name}'.")

    # Validate Period
    period = Period.query.get(period_id)
    if not period:
        raise ValueError("Selected Period does not exist.")

    # Validate teaching entries require subject and teacher
    if entry_type == "CLASS":
        if not subject_id:
            raise ValueError("Teaching entries require a Subject to be selected.")
        if not teacher_id:
            raise ValueError("Teaching entries require a Teacher/Employee to be selected.")
    else:
        # Non-teaching entries (BREAK/FREE)
        subject_id = None
        teacher_id = None

    # Server Conflict Validation
    conflicts = check_conflicts(
        session_id=session_id,
        day_of_week=day_of_week,
        period_id=period_id,
        class_id=class_id,
        section_id=section_id,
        teacher_id=teacher_id,
        room_number=room_number,
        exclude_entry_id=entry_id
    )
    if conflicts:
        raise ValueError(" | ".join(conflicts))

    # Save / Update Entry
    entry = Timetable.query.get(entry_id) if entry_id else None
    if not entry:
        entry = Timetable(
            academic_session_id=session_id,
            class_id=class_id,
            section_id=section_id,
            period_id=period_id,
            day_of_week=day_of_week,
            subject_id=subject_id,
            employee_id=teacher_id,
            room_number=room_number.strip().upper() if room_number else None,
            entry_type=entry_type,
            status=status
        )
        db.session.add(entry)
    else:
        entry.academic_session_id = session_id
        entry.class_id = class_id
        entry.section_id = section_id
        entry.period_id = period_id
        entry.day_of_week = day_of_week
        entry.subject_id = subject_id
        entry.employee_id = teacher_id
        entry.room_number = room_number.strip().upper() if room_number else None
        entry.entry_type = entry_type
        entry.status = status

    db.session.commit()
    return entry

def duplicate_timetable_entry(entry_id, target_days, target_period_id=None):
    """
    Duplicates a single timetable entry across multiple target days (and optionally a target period).
    """
    src_entry = Timetable.query.get(entry_id)
    if not src_entry:
        raise ValueError("Source schedule entry not found.")

    if not target_days:
        raise ValueError("Please select at least one target day to duplicate to.")

    period_id = target_period_id or src_entry.period_id

    created_count = 0
    skipped_conflicts = []

    for day in target_days:
        if day not in DAYS_OF_WEEK:
            continue

        conflicts = check_conflicts(
            session_id=src_entry.academic_session_id,
            day_of_week=day,
            period_id=period_id,
            class_id=src_entry.class_id,
            section_id=src_entry.section_id,
            teacher_id=src_entry.employee_id,
            room_number=src_entry.room_number
        )

        if conflicts:
            skipped_conflicts.append(f"{day}: " + ", ".join(conflicts))
            continue

        # Check existing entry at slot and update or create
        existing = Timetable.query.filter_by(
            academic_session_id=src_entry.academic_session_id,
            class_id=src_entry.class_id,
            section_id=src_entry.section_id,
            day_of_week=day,
            period_id=period_id
        ).first()

        if not existing:
            new_entry = Timetable(
                academic_session_id=src_entry.academic_session_id,
                class_id=src_entry.class_id,
                section_id=src_entry.section_id,
                period_id=period_id,
                day_of_week=day,
                subject_id=src_entry.subject_id,
                employee_id=src_entry.employee_id,
                room_number=src_entry.room_number,
                entry_type=src_entry.entry_type,
                status=src_entry.status
            )
            db.session.add(new_entry)
            created_count += 1
        else:
            existing.subject_id = src_entry.subject_id
            existing.employee_id = src_entry.employee_id
            existing.room_number = src_entry.room_number
            existing.entry_type = src_entry.entry_type
            created_count += 1

    db.session.commit()
    return created_count, skipped_conflicts

def copy_day_schedule(class_id, section_id, source_day, target_days, session_id=None):
    """
    Copies all scheduled periods from a source day (e.g. Monday) to target days (e.g. Tuesday, Wednesday).
    """
    if not session_id:
        act_sess = get_active_academic_session()
        session_id = act_sess.id if act_sess else None

    if source_day not in DAYS_OF_WEEK:
        raise ValueError("Invalid source day specified.")

    src_entries = Timetable.query.filter_by(
        academic_session_id=session_id,
        class_id=class_id,
        day_of_week=source_day
    )
    if section_id:
        src_entries = src_entries.filter((Timetable.section_id == section_id) | (Timetable.section_id.is_(None)))

    entries_to_copy = src_entries.all()
    if not entries_to_copy:
        raise ValueError(f"No schedule entries found on {source_day} to copy.")

    total_created = 0
    all_skipped = []

    for entry in entries_to_copy:
        valid_targets = [d for d in target_days if d != source_day]
        cnt, skipped = duplicate_timetable_entry(entry.id, valid_targets, target_period_id=entry.period_id)
        total_created += cnt
        all_skipped.extend(skipped)

    return total_created, all_skipped

def delete_timetable_entry(entry_id):
    """Delete a single timetable schedule entry."""
    entry = Timetable.query.get(entry_id)
    if not entry:
        raise ValueError("Timetable entry not found.")
    
    db.session.delete(entry)
    db.session.commit()
    return True

def publish_class_timetable(class_id, section_id=None, session_id=None):
    """
    Publish all draft timetable entries for a class/section after validating conflicts.
    """
    if not session_id:
        act_sess = get_active_academic_session()
        session_id = act_sess.id if act_sess else None

    query = Timetable.query.filter_by(academic_session_id=session_id, class_id=class_id)
    if section_id:
        query = query.filter((Timetable.section_id == section_id) | (Timetable.section_id.is_(None)))

    entries = query.all()
    if not entries:
        raise ValueError("No timetable entries found to publish.")

    # Re-validate all entries for conflict integrity before publishing
    all_conflicts = []
    for en in entries:
        c_list = check_conflicts(
            session_id=session_id,
            day_of_week=en.day_of_week,
            period_id=en.period_id,
            class_id=en.class_id,
            section_id=en.section_id,
            teacher_id=en.employee_id,
            room_number=en.room_number,
            exclude_entry_id=en.id
        )
        all_conflicts.extend(c_list)

    if all_conflicts:
        raise ValueError("Cannot publish timetable due to conflicts: " + " | ".join(all_conflicts))

    for en in entries:
        en.status = "PUBLISHED"

    db.session.commit()
    return len(entries)

def parse_timetable_csv_or_excel(file_stream, filename):
    """
    Parses an uploaded CSV or Excel (.xlsx) file stream into a list of row dictionaries.
    Supports CSV and Excel files seamlessly.
    """
    rows = []
    filename_lower = filename.lower()

    if filename_lower.endswith('.xlsx') or filename_lower.endswith('.xls'):
        try:
            import openpyxl
            wb = openpyxl.load_workbook(file_stream, data_only=True)
            sheet = wb.active
            header = [str(cell.value or '').strip() for cell in sheet[1]]
            
            for row in sheet.iter_rows(min_row=2, values_only=True):
                if not any(row):
                    continue
                row_dict = {}
                for idx, col_name in enumerate(header):
                    row_dict[col_name] = str(row[idx] or '').strip() if idx < len(row) else ''
                rows.append(row_dict)
        except ImportError:
            raise ValueError("openpyxl library not installed. Please upload CSV files or install openpyxl.")
    else:
        # Parse CSV
        content = file_stream.read().decode('utf-8-sig', errors='ignore')
        reader = csv.DictReader(io.StringIO(content))
        for row in reader:
            cleaned_row = {str(k or '').strip(): str(v or '').strip() for k, v in row.items()}
            if any(cleaned_row.values()):
                rows.append(cleaned_row)

    return rows

def import_timetable_from_file(file_stream, filename, class_id, section_id=None, session_id=None):
    """
    Bulk imports timetable schedule entries from an Excel or CSV file.
    Expected headers (flexible case-insensitive):
    Day, Period, Subject, Teacher, Room, Type
    """
    if not session_id:
        act_sess = get_active_academic_session()
        session_id = act_sess.id if act_sess else None

    raw_rows = parse_timetable_csv_or_excel(file_stream, filename)
    if not raw_rows:
        raise ValueError("The uploaded Excel/CSV file contains no readable data rows.")

    periods = get_all_periods_for_session(session_id)
    periods_by_name = {p.name.lower(): p for p in periods}
    periods_by_order = {p.period_order: p for p in periods}

    subjects = Subject.query.all()
    subjects_by_code = {s.code.lower(): s for s in subjects if s.code}
    subjects_by_name = {s.name.lower(): s for s in subjects}

    teachers = Employee.query.filter_by(is_teacher=True).all()
    teachers_by_code = {t.registration_number.lower(): t for t in teachers}
    teachers_by_name = {t.full_name.lower(): t for t in teachers}

    success_count = 0
    warnings = []

    for row_idx, row in enumerate(raw_rows, start=2):
        # Flexible Header Normalization
        row_norm = {k.lower(): v for k, v in row.items()}
        
        day_raw = row_norm.get('day') or row_norm.get('day_of_week') or ''
        period_raw = row_norm.get('period') or row_norm.get('period_order') or row_norm.get('time_slot') or ''
        subject_raw = row_norm.get('subject') or row_norm.get('subject_code') or row_norm.get('subject_name') or ''
        teacher_raw = row_norm.get('teacher') or row_norm.get('employee') or row_norm.get('teacher_code') or row_norm.get('teacher_name') or ''
        room_raw = row_norm.get('room') or row_norm.get('room_number') or row_norm.get('location') or ''
        type_raw = (row_norm.get('type') or row_norm.get('entry_type') or 'CLASS').upper()

        # Match Day
        matched_day = None
        for d in DAYS_OF_WEEK:
            if d.lower() == day_raw.strip().lower():
                matched_day = d
                break
        if not matched_day:
            warnings.append(f"Row {row_idx}: Invalid day '{day_raw}' skipped.")
            continue

        # Match Period
        matched_period = None
        period_str = period_raw.strip().lower()
        if period_str in periods_by_name:
            matched_period = periods_by_name[period_str]
        elif period_str.isdigit() and int(period_str) in periods_by_order:
            matched_period = periods_by_order[int(period_str)]
        else:
            # Try fuzzy match "period 1" -> 1
            for p in periods:
                if p.name.lower() in period_str or period_str in p.name.lower():
                    matched_period = p
                    break

        if not matched_period:
            warnings.append(f"Row {row_idx}: Could not match period '{period_raw}' on {matched_day}.")
            continue

        # Match Subject & Teacher if CLASS
        subject_id = None
        teacher_id = None
        if type_raw == 'CLASS':
            sub_clean = subject_raw.strip().lower()
            if sub_clean in subjects_by_code:
                subject_id = subjects_by_code[sub_clean].id
            elif sub_clean in subjects_by_name:
                subject_id = subjects_by_name[sub_clean].id

            teach_clean = teacher_raw.strip().lower()
            if teach_clean in teachers_by_code:
                teacher_id = teachers_by_code[teach_clean].id
            elif teach_clean in teachers_by_name:
                teacher_id = teachers_by_name[teach_clean].id

        try:
            create_or_update_timetable_entry(
                class_id=class_id,
                section_id=section_id,
                day_of_week=matched_day,
                period_id=matched_period.id,
                subject_id=subject_id,
                teacher_id=teacher_id,
                room_number=room_raw,
                entry_type=type_raw,
                session_id=session_id
            )
            success_count += 1
        except Exception as e:
            warnings.append(f"Row {row_idx} ({matched_day} {matched_period.name}): {str(e)}")

    return success_count, warnings

def export_timetable_csv(class_id, section_id=None, session_id=None):
    """
    Exports current class timetable to CSV string.
    """
    if not session_id:
        act_sess = get_active_academic_session()
        session_id = act_sess.id if act_sess else None

    matrix = get_class_timetable(class_id, section_id, session_id)
    periods = get_all_periods_for_session(session_id)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Day', 'Period Order', 'Period Name', 'Start Time', 'End Time', 'Entry Type', 'Subject Code', 'Subject Name', 'Teacher Code', 'Teacher Name', 'Room Number', 'Status'])

    for d in DAYS_OF_WEEK:
        for p in periods:
            key = f"{d}_{p.id}"
            en = matrix.get(key)
            if en:
                writer.writerow([
                    d,
                    p.period_order,
                    p.name,
                    p.start_time.strftime('%H:%M'),
                    p.end_time.strftime('%H:%M'),
                    en.entry_type,
                    en.subject.code if en.subject else '',
                    en.subject.name if en.subject else '',
                    en.teacher.registration_number if en.teacher else '',
                    en.teacher.full_name if en.teacher else '',
                    en.room_number or '',
                    en.status
                ])
            else:
                writer.writerow([d, p.period_order, p.name, p.start_time.strftime('%H:%M'), p.end_time.strftime('%H:%M'), 'FREE', '', '', '', '', '', 'DRAFT'])

    return output.getvalue()

def generate_sample_timetable_csv(class_id, session_id=None):
    """
    Generates a pre-filled sample CSV template for users to edit and upload.
    """
    if not session_id:
        act_sess = get_active_academic_session()
        session_id = act_sess.id if act_sess else None

    periods = get_all_periods_for_session(session_id)
    subjects = Subject.query.all()
    teachers = Employee.query.filter_by(is_teacher=True).all()

    sub_code = subjects[0].code if subjects and subjects[0].code else (subjects[0].name if subjects else 'MATH')
    tch_code = teachers[0].registration_number if teachers else 'EMP001'

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Day', 'Period', 'Type', 'Subject', 'Teacher', 'Room'])

    for d in DAYS_OF_WEEK[:5]: # Mon - Fri sample
        for p in periods:
            if p.period_type == 'BREAK':
                writer.writerow([d, p.name, 'BREAK', '', '', ''])
            else:
                writer.writerow([d, p.name, 'CLASS', sub_code, tch_code, 'Room 101'])

    return output.getvalue()
