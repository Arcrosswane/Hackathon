from datetime import datetime
from app.models import db

class Timetable(db.Model):
    __tablename__ = 'timetables'
    __table_args__ = (
        db.UniqueConstraint('academic_session_id', 'class_id', 'section_id', 'day_of_week', 'period_id', name='uq_session_class_section_day_period'),
    )

    id = db.Column(db.Integer, primary_key=True)
    academic_session_id = db.Column(db.Integer, db.ForeignKey('academic_sessions.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'), nullable=True)
    period_id = db.Column(db.Integer, db.ForeignKey('periods.id'), nullable=False)
    
    day_of_week = db.Column(db.String(20), nullable=False) # Monday, Tuesday, Wednesday, Thursday, Friday, Saturday
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=True) # Optional for BREAK/FREE
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=True) # Teacher ID (Optional for BREAK/FREE)
    
    room_number = db.Column(db.String(50), nullable=True) # e.g. "Room 204", "Lab 1"
    entry_type = db.Column(db.String(30), default="CLASS", nullable=False) # CLASS, BREAK, FREE
    status = db.Column(db.String(30), default="DRAFT", nullable=False) # DRAFT, PUBLISHED, ARCHIVED
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    academic_session = db.relationship('AcademicSession', lazy=True)
    school_class = db.relationship('SchoolClass', lazy=True)
    section = db.relationship('Section', lazy=True)
    period = db.relationship('Period', lazy=True)
    subject = db.relationship('Subject', lazy=True)
    teacher = db.relationship('Employee', lazy=True)

    def __repr__(self):
        return f'<Timetable Class #{self.class_id} Sec #{self.section_id} on {self.day_of_week} Period #{self.period_id} [{self.status}]>'
