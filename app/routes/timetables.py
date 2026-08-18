from datetime import datetime, time
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, Response
from app.models import db, Period, Timetable, SchoolClass, Section, Subject, Employee
from app.utils.decorators import login_required, role_required
from app.services.academic_service import get_active_academic_session
from app.services.class_service import get_classes_for_session
from app.services.subject_service import get_subjects_for_class
from app.services.employee_service import get_teachers
from app.services.timetable_service import (
    DAYS_OF_WEEK, ENTRY_TYPES, TIMETABLE_STATUSES,
    get_all_periods_for_session, initialize_default_periods_for_session,
    get_class_timetable, check_conflicts, create_or_update_timetable_entry,
    delete_timetable_entry, publish_class_timetable,
    duplicate_timetable_entry, copy_day_schedule,
    import_timetable_from_file, export_timetable_csv, generate_sample_timetable_csv
)

timetables_bp = Blueprint('timetables', __name__, url_prefix='/admin/academics/timetables')

@timetables_bp.route('', methods=['GET'])
@login_required
@role_required('admin', 'teacher', 'employee', 'student', 'parent')
def index():
    try:
        db.create_all()
        alter_statements = [
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
            "ALTER TABLE timetables MODIFY COLUMN room_number VARCHAR(50) NULL;"
        ]
        with db.engine.connect() as conn:
            from sqlalchemy import text
            for stmt in alter_statements:
                try:
                    conn.execute(text(stmt))
                    conn.commit()
                except Exception:
                    pass
    except Exception:
        pass

    try:
        active_session = get_active_academic_session()
        if not active_session:
            active_session = AcademicSession.query.order_by(AcademicSession.id.desc()).first()
            if active_session:
                active_session.is_active = True
                db.session.commit()

        if not active_session:
            return render_template(
                'timetables/index.html',
                active_session=None,
                classes=[],
                selected_class=None,
                sections=[],
                selected_section=None,
                periods=[],
                days=DAYS_OF_WEEK,
                entry_types=ENTRY_TYPES,
                matrix={},
                class_subjects=[],
                teachers=[],
                is_published=False
            )

        classes = get_classes_for_session(active_session.id)
        selected_class_id = request.args.get('class_id', type=int)
        selected_section_id = request.args.get('section_id', type=int)

        if not selected_class_id and classes:
            selected_class_id = classes[0].id

        selected_class = SchoolClass.query.get(selected_class_id) if selected_class_id else None
        sections = selected_class.sections if selected_class else []

        selected_section = None
        if selected_section_id:
            selected_section = Section.query.get(selected_section_id)

        periods = initialize_default_periods_for_session(active_session.id)
        matrix = get_class_timetable(selected_class_id, selected_section_id, active_session.id) if selected_class_id else {}
        
        class_subjects = get_subjects_for_class(selected_class_id) if selected_class_id else []
        teachers = get_teachers()

        # Determine status of timetable (e.g. Published if any entry is published)
        is_published = any(en.status == 'PUBLISHED' for en in matrix.values())

        return render_template(
            'timetables/index.html',
            active_session=active_session,
            classes=classes,
            selected_class=selected_class,
            sections=sections,
            selected_section=selected_section,
            periods=periods,
            days=DAYS_OF_WEEK,
            entry_types=ENTRY_TYPES,
            matrix=matrix,
            class_subjects=class_subjects,
            teachers=teachers,
            is_published=is_published
        )
    except Exception as e:
        db.session.rollback()
        flash(f"Error loading Timetable system: {str(e)}", "danger")
        return render_template(
            'timetables/index.html',
            active_session=None,
            classes=[],
            selected_class=None,
            sections=[],
            selected_section=None,
            periods=[],
            days=DAYS_OF_WEEK,
            entry_types=ENTRY_TYPES,
            matrix={},
            class_subjects=[],
            teachers=[],
            is_published=False
        )

@timetables_bp.route('/save', methods=['POST'])
@login_required
@role_required('admin')
def save_entry():
    class_id = request.form.get('class_id', type=int)
    section_id = request.form.get('section_id', type=int)
    day_of_week = request.form.get('day_of_week', '').strip()
    period_id = request.form.get('period_id', type=int)
    subject_id = request.form.get('subject_id', type=int)
    employee_id = request.form.get('employee_id', type=int)
    room_number = request.form.get('room_number', '').strip()
    entry_type = request.form.get('entry_type', 'CLASS').strip()
    entry_id = request.form.get('entry_id', type=int)

    try:
        entry = create_or_update_timetable_entry(
            class_id=class_id,
            section_id=section_id,
            day_of_week=day_of_week,
            period_id=period_id,
            subject_id=subject_id,
            teacher_id=employee_id,
            room_number=room_number,
            entry_type=entry_type,
            entry_id=entry_id
        )
        flash(f"Timetable entry saved successfully for {entry.day_of_week} ({entry.period.name}).", "success")
    except ValueError as e:
        flash(str(e), "danger")
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to save timetable entry: {str(e)}", "danger")

    return redirect(url_for('timetables.index', class_id=class_id, section_id=section_id))

@timetables_bp.route('/<int:entry_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_entry(entry_id):
    class_id = request.form.get('class_id', type=int)
    section_id = request.form.get('section_id', type=int)
    
    try:
        delete_timetable_entry(entry_id)
        flash("Timetable entry deleted successfully.", "success")
    except Exception as e:
        flash(f"Failed to delete entry: {str(e)}", "danger")

    return redirect(url_for('timetables.index', class_id=class_id, section_id=section_id))

@timetables_bp.route('/<int:entry_id>/duplicate', methods=['POST'])
@login_required
@role_required('admin')
def duplicate_entry(entry_id):
    class_id = request.form.get('class_id', type=int)
    section_id = request.form.get('section_id', type=int)
    target_days = request.form.getlist('target_days')
    target_period_id = request.form.get('target_period_id', type=int)

    try:
        count, skipped = duplicate_timetable_entry(entry_id, target_days, target_period_id)
        if count > 0:
            flash(f"Successfully duplicated entry to {count} target slot(s)!", "success")
        if skipped:
            flash("Skipped some slots due to conflicts: " + " | ".join(skipped), "warning")
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to duplicate entry: {str(e)}", "danger")

    return redirect(url_for('timetables.index', class_id=class_id, section_id=section_id))

@timetables_bp.route('/copy-day', methods=['POST'])
@login_required
@role_required('admin')
def copy_day():
    class_id = request.form.get('class_id', type=int)
    section_id = request.form.get('section_id', type=int)
    source_day = request.form.get('source_day', '').strip()
    target_days = request.form.getlist('target_days')

    try:
        count, skipped = copy_day_schedule(class_id, section_id, source_day, target_days)
        flash(f"Copied {count} schedule entries from {source_day} to target day(s)!", "success")
        if skipped:
            flash("Skipped some conflicting slots: " + " | ".join(skipped), "warning")
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to copy day schedule: {str(e)}", "danger")

    return redirect(url_for('timetables.index', class_id=class_id, section_id=section_id))

@timetables_bp.route('/import-excel', methods=['POST'])
@login_required
@role_required('admin')
def import_excel():
    class_id = request.form.get('class_id', type=int)
    section_id = request.form.get('section_id', type=int)
    file = request.files.get('file')

    if not file or not file.filename:
        flash("Please select an Excel (.xlsx) or CSV (.csv) file to import.", "warning")
        return redirect(url_for('timetables.index', class_id=class_id, section_id=section_id))

    try:
        count, warnings = import_timetable_from_file(file.stream, file.filename, class_id, section_id)
        if count > 0:
            flash(f"Success! Imported {count} timetable entries successfully from '{file.filename}'.", "success")
        if warnings:
            flash("Import Warnings / Skipped Rows: " + " | ".join(warnings[:5]), "warning")
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to import timetable file: {str(e)}", "danger")

    return redirect(url_for('timetables.index', class_id=class_id, section_id=section_id))

@timetables_bp.route('/export-csv', methods=['GET'])
@login_required
@role_required('admin')
def export_csv():
    class_id = request.args.get('class_id', type=int)
    section_id = request.args.get('section_id', type=int)
    
    selected_class = SchoolClass.query.get(class_id) if class_id else None
    c_name = selected_class.name if selected_class else "Class"

    csv_data = export_timetable_csv(class_id, section_id)
    filename = f"Timetable_{c_name}.csv"

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename={filename}"}
    )

@timetables_bp.route('/sample-template', methods=['GET'])
@login_required
@role_required('admin')
def sample_template():
    class_id = request.args.get('class_id', type=int)
    csv_data = generate_sample_timetable_csv(class_id)
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=Timetable_Import_Sample_Template.csv"}
    )

@timetables_bp.route('/publish', methods=['POST'])
@login_required
@role_required('admin')
def publish():
    class_id = request.form.get('class_id', type=int)
    section_id = request.form.get('section_id', type=int)

    try:
        count = publish_class_timetable(class_id, section_id)
        flash(f"Success! Timetable published successfully ({count} periods activated).", "success")
    except ValueError as e:
        flash(str(e), "danger")
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to publish timetable: {str(e)}", "danger")

    return redirect(url_for('timetables.index', class_id=class_id, section_id=section_id))

@timetables_bp.route('/periods', methods=['GET'])
@login_required
@role_required('admin')
def period_settings():
    try:
        db.create_all()
    except Exception:
        pass

    try:
        active_session = get_active_academic_session()
        if not active_session:
            flash("No active academic session found.", "warning")
            return redirect(url_for('admin.dashboard'))

        periods = get_all_periods_for_session(active_session.id)
        return render_template('timetables/periods.html', active_session=active_session, periods=periods, entry_types=ENTRY_TYPES)
    except Exception as e:
        db.session.rollback()
        flash(f"Error loading period settings: {str(e)}", "danger")
        return redirect(url_for('timetables.index'))

@timetables_bp.route('/periods/save', methods=['POST'])
@login_required
@role_required('admin')
def save_period():
    active_session = get_active_academic_session()
    period_id = request.form.get('period_id', type=int)
    name = request.form.get('name', '').strip()
    order = request.form.get('period_order', type=int)
    st_str = request.form.get('start_time', '').strip()
    et_str = request.form.get('end_time', '').strip()
    ptype = request.form.get('period_type', 'CLASS').strip()

    if not name or not order or not st_str or not et_str:
        flash("Period Name, Order, Start Time, and End Time are required.", "danger")
        return redirect(url_for('timetables.period_settings'))

    try:
        st_parts = [int(x) for x in st_str.split(':')]
        et_parts = [int(x) for x in et_str.split(':')]
        start_time_val = time(st_parts[0], st_parts[1])
        end_time_val = time(et_parts[0], et_parts[1])

        p = Period.query.get(period_id) if period_id else None
        if not p:
            p = Period(
                academic_session_id=active_session.id,
                name=name,
                period_order=order,
                start_time=start_time_val,
                end_time=end_time_val,
                period_type=ptype,
                is_active=True
            )
            db.session.add(p)
        else:
            p.name = name
            p.period_order = order
            p.start_time = start_time_val
            p.end_time = end_time_val
            p.period_type = ptype

        db.session.commit()
        flash(f"Period '{p.name}' saved successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to save period: {str(e)}", "danger")

    return redirect(url_for('timetables.period_settings'))

@timetables_bp.route('/api/validate-conflict', methods=['POST'])
@login_required
@role_required('admin')
def validate_conflict_api():
    """AJAX JSON conflict check endpoint."""
    data = request.get_json() or {}
    session_id = data.get('session_id')
    day_of_week = data.get('day_of_week')
    period_id = data.get('period_id')
    class_id = data.get('class_id')
    section_id = data.get('section_id')
    teacher_id = data.get('teacher_id')
    room_number = data.get('room_number')
    exclude_entry_id = data.get('entry_id')

    if not session_id or not day_of_week or not period_id or not class_id:
        return jsonify({'conflicts': []})

    conflicts = check_conflicts(
        session_id=session_id,
        day_of_week=day_of_week,
        period_id=period_id,
        class_id=class_id,
        section_id=section_id,
        teacher_id=teacher_id,
        room_number=room_number,
        exclude_entry_id=exclude_entry_id
    )

    return jsonify({'conflicts': conflicts, 'has_conflict': len(conflicts) > 0})


@timetables_bp.route('/live-class')
@login_required
def live_class():
    """Placeholder route for future Live Class feature."""
    flash("Live Class Integration is a future feature.", "info")
    return redirect(url_for('timetables.index'))
