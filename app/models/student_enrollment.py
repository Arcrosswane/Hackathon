from datetime import datetime, date
from app.models import db

class StudentEnrollment(db.Model):
    __tablename__ = 'student_enrollments'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    academic_session_id = db.Column(db.Integer, db.ForeignKey('academic_sessions.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'), nullable=True)
    roll_number = db.Column(db.Integer, nullable=True)
    enrollment_date = db.Column(db.Date, default=date.today, nullable=True)
    is_current = db.Column(db.Boolean, default=True, nullable=False)
    status = db.Column(db.String(30), default="Active", nullable=False) # Active, Transferred, Promoted, Completed

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    academic_session = db.relationship('AcademicSession', lazy=True)
    school_class = db.relationship('SchoolClass', lazy=True)
    section = db.relationship('Section', lazy=True)

    def __repr__(self):
        return f'<StudentEnrollment Student #{self.student_id} -> Class #{self.class_id} (Session #{self.academic_session_id}) [Current: {self.is_current}]>'
