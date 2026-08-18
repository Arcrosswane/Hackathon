import json
import uuid
from datetime import datetime
from app.models import db, Certificate, Student, School

def generate_certificate_number(school_id=None):
    """
    Generates a unique human-readable certificate number formatted as CERT-YYYY-XXXXXX.
    """
    year = datetime.utcnow().year
    short_uuid = uuid.uuid4().hex[:6].upper()
    cert_num = f"CERT-{year}-{short_uuid}"
    return cert_num


def issue_certificate(school_id, student_id, cert_type, issued_by_id, remarks=None, extra_data=None):
    """
    Issues an official school certificate for a student.
    """
    student = Student.query.get(student_id)
    if not student:
        raise ValueError("Student not found.")

    if school_id and student.school_id and student.school_id != school_id:
        raise PermissionError("Access denied to student record.")

    cert_num = generate_certificate_number(school_id)

    extra_str = json.dumps(extra_data) if isinstance(extra_data, dict) else (extra_data or '')

    certificate = Certificate(
        school_id=school_id or student.school_id or 1,
        certificate_number=cert_num,
        certificate_type=cert_type,
        student_id=student.id,
        issued_by_id=issued_by_id,
        issue_date=datetime.utcnow().date(),
        status="Issued",
        remarks=remarks,
        extra_data=extra_str,
        created_at=datetime.utcnow()
    )

    db.session.add(certificate)
    db.session.commit()
    return certificate


def get_certificate_history(school_id=None, student_id=None, cert_type=None, status=None):
    """
    Returns filtered roster of issued certificates respecting school isolation.
    """
    query = Certificate.query
    if school_id:
        query = query.filter_by(school_id=school_id)
    if student_id:
        query = query.filter_by(student_id=student_id)
    if cert_type:
        query = query.filter_by(certificate_type=cert_type)
    if status:
        query = query.filter_by(status=status)

    return query.order_by(Certificate.issue_date.desc(), Certificate.id.desc()).all()


def verify_certificate(cert_number):
    """
    Public verification endpoint returning minimum necessary details.
    """
    cert_num = (cert_number or '').strip()
    if not cert_num:
        return {'is_valid': False, 'message': 'Invalid certificate number.'}

    cert = Certificate.query.filter_by(certificate_number=cert_num).first()
    if not cert:
        return {'is_valid': False, 'message': 'Certificate number not found in official school records.'}

    student_initials = f"{cert.student.first_name[0]}. {cert.student.last_name}" if cert.student else "Student"
    sch = School.query.get(cert.school_id) if cert.school_id else School.query.first()
    school_name = sch.name if sch else "StratLearn Academy"

    return {
        'is_valid': cert.status == 'Issued',
        'certificate_number': cert.certificate_number,
        'certificate_type': cert.certificate_type,
        'student_name': student_initials,
        'school_name': school_name,
        'issue_date': cert.issue_date.strftime('%B %d, %Y') if cert.issue_date else 'N/A',
        'status': cert.status
    }


def cancel_certificate(cert_id, school_id=None, user_id=None, reason=None):
    """
    Marks an issued certificate as Cancelled.
    """
    cert = Certificate.query.get(cert_id)
    if not cert:
        raise ValueError("Certificate not found.")

    if school_id and cert.school_id and cert.school_id != school_id:
        raise PermissionError("Access denied to certificate record.")

    cert.status = 'Cancelled'
    if reason:
        cert.remarks = (cert.remarks or '') + f" | Cancelled: {reason}"

    db.session.commit()
    return cert
