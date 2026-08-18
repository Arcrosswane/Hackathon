from datetime import datetime, date
from app.models import db

class Attendance(db.Model):
    __tablename__ = 'attendance'

    id = db.Column(db.Integer, primary_key=True)
    institute_id = db.Column(db.Integer, db.ForeignKey('institutes.id'), nullable=True) # School ID
    academic_session_id = db.Column(db.Integer, db.ForeignKey('academic_sessions.id'), nullable=True)
    
    entity_type = db.Column(db.String(20), nullable=False, default="Student") # "Student" or "Employee"
    entity_id = db.Column(db.Integer, nullable=False, default=0) # Legacy entity ID
    
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=True)
    
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=True)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'), nullable=True)
    
    attendance_date = db.Column(db.Date, nullable=False)
    date = db.Column(db.Date, nullable=True) # Legacy date column alias
    
    status = db.Column(db.String(20), nullable=False, default="PRESENT") # "PRESENT", "ABSENT", "LATE", "HALF_DAY"
    remarks = db.Column(db.String(255), nullable=True)
    
    recorded_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    student = db.relationship('Student', foreign_keys=[student_id], backref=db.backref('attendance_records', lazy=True, cascade='all, delete-orphan'))
    employee = db.relationship('Employee', foreign_keys=[employee_id], backref=db.backref('attendance_records', lazy=True, cascade='all, delete-orphan'))
    school_class = db.relationship('SchoolClass', foreign_keys=[class_id], backref='attendance_records', lazy=True)
    section = db.relationship('Section', foreign_keys=[section_id], backref='attendance_records', lazy=True)
    recorded_by = db.relationship('User', foreign_keys=[recorded_by_id], lazy=True)
    academic_session = db.relationship('AcademicSession', foreign_keys=[academic_session_id], lazy=True)

    __table_args__ = (
        db.UniqueConstraint('student_id', 'attendance_date', 'academic_session_id', name='uq_student_daily_attendance'),
        db.UniqueConstraint('employee_id', 'attendance_date', name='uq_employee_daily_attendance'),
        db.Index('idx_attn_date_class_sec', 'attendance_date', 'class_id', 'section_id'),
        db.Index('idx_attn_student_date', 'student_id', 'attendance_date'),
        db.Index('idx_attn_employee_date', 'employee_id', 'attendance_date'),
    )

    def __repr__(self):
        target = f"Student #{self.student_id}" if self.student_id else f"Employee #{self.employee_id}"
        return f'<Attendance {target} on {self.attendance_date}: {self.status}>'

AttendanceRecord = Attendance
