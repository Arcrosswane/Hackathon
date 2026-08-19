from flask import Blueprint, render_template, request, session, flash, redirect, url_for, jsonify
from app.models import db, User, Student, Certificate, School
from app.utils.decorators import login_required
from app.services.certificate_service import (
    issue_certificate,
    get_certificate_history,
    verify_certificate,
    cancel_certificate
)

certificates_bp = Blueprint('certificates', __name__, url_prefix='/certificates')


@certificates_bp.route('/')
@login_required
def index():
    """Renders Issued Certificates History & Roster Page."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user:
        return redirect(url_for('auth.login'))

    user_role = (current_user.user_type or '').lower()
    sch_id = current_user.school_id or 1

    student_id = None
    if user_role == 'student':
        stu = Student.query.get(current_user.linked_entity_id) if current_user.linked_entity_id else Student.query.first()
        student_id = stu.id if stu else None

    certificates = get_certificate_history(
        school_id=sch_id if user_role in ('admin', 'teacher', 'employee') else None,
        student_id=student_id
    )

    return render_template(
        'certificates/index.html',
        current_user=current_user,
        certificates=certificates,
        user_role=user_role
    )


@certificates_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Renders Issue New Certificate Form & processes certificate creation."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user:
        return redirect(url_for('auth.login'))

    user_role = (current_user.user_type or '').lower()
    if user_role not in ('admin', 'teacher', 'employee'):
        flash('Permission denied to issue certificates.', 'danger')
        return redirect(url_for('certificates.index'))

    sch_id = current_user.school_id or 1

    if request.method == 'POST':
        student_id = request.form.get('student_id', type=int)
        cert_type = request.form.get('certificate_type', '').strip()
        remarks = request.form.get('remarks', '').strip()
        conduct = request.form.get('conduct', 'Good').strip()
        reason = request.form.get('reason', '').strip()

        if not student_id or not cert_type:
            flash('Please select a student and certificate type.', 'warning')
            return redirect(url_for('certificates.create'))

        try:
            extra_data = {'conduct': conduct, 'reason': reason}
            cert = issue_certificate(
                school_id=sch_id,
                student_id=student_id,
                cert_type=cert_type,
                issued_by_id=current_user.id,
                remarks=remarks,
                extra_data=extra_data
            )
            flash(f"Certificate #{cert.certificate_number} issued successfully!", 'success')
            return redirect(url_for('certificates.detail', cert_id=cert.id))
        except (ValueError, PermissionError) as e:
            flash(str(e), 'danger')
            return redirect(url_for('certificates.create'))

    students = Student.query.filter((Student.institute_id == sch_id) | (Student.institute_id.is_(None))).all() if sch_id else Student.query.all()
    cert_types = [
        "Transfer Certificate",
        "Character Certificate",
        "Bonafide Certificate",
        "Study Certificate",
        "Merit Certificate",
        "Conduct Certificate"
    ]

    return render_template(
        'certificates/create.html',
        current_user=current_user,
        students=students,
        cert_types=cert_types
    )


@certificates_bp.route('/<int:cert_id>')
@login_required
def detail(cert_id):
    """Renders Dedicated Printable Official Certificate View Page."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user:
        return redirect(url_for('auth.login'))

    user_role = (current_user.user_type or '').lower()
    cert = Certificate.query.get_or_404(cert_id)

    # Permission check
    if user_role == 'student':
        stu = Student.query.get(current_user.linked_entity_id) if current_user.linked_entity_id else Student.query.first()
        if not stu or cert.student_id != stu.id:
            flash('Permission denied to view this certificate.', 'danger')
            return redirect(url_for('certificates.index'))

    return render_template(
        'certificates/detail.html',
        current_user=current_user,
        cert=cert
    )


@certificates_bp.route('/<int:cert_id>/cancel', methods=['POST'])
@login_required
def cancel(cert_id):
    """Cancels an issued certificate."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user or (current_user.user_type or '').lower() != 'admin':
        flash('Permission denied to cancel certificates.', 'danger')
        return redirect(url_for('certificates.index'))

    reason = request.form.get('reason', 'Cancelled by administrator')
    try:
        cancel_certificate(cert_id=cert_id, school_id=current_user.school_id, user_id=current_user.id, reason=reason)
        flash('Certificate cancelled successfully.', 'info')
    except (ValueError, PermissionError) as e:
        flash(str(e), 'danger')

    return redirect(url_for('certificates.index'))


@certificates_bp.route('/verify', methods=['GET', 'POST'])
def verify():
    """Public Certificate Verification Checker Page (Minimum Info Exposed)."""
    verification_result = None
    query_num = ''

    if request.method == 'POST' or request.args.get('cert_number'):
        query_num = request.form.get('cert_number') or request.args.get('cert_number') or ''
        verification_result = verify_certificate(query_num)

    return render_template(
        'certificates/verify.html',
        query_num=query_num,
        result=verification_result
    )
