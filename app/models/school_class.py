from datetime import datetime
from app.models import db

class SchoolClass(db.Model):
    __tablename__ = 'classes'
    __table_args__ = (
        db.UniqueConstraint('academic_session_id', 'name', name='uq_session_class_name'),
    )

    id = db.Column(db.Integer, primary_key=True)
    academic_session_id = db.Column(db.Integer, db.ForeignKey('academic_sessions.id'), nullable=False)
    institute_id = db.Column(db.Integer, db.ForeignKey('institutes.id'), nullable=True)
    name = db.Column(db.String(50), nullable=False) # e.g. "9", "Nursery", "10"
    display_name = db.Column(db.String(100), nullable=False) # e.g. "Grade 9", "Class 9"
    numeric_order = db.Column(db.Integer, default=0, nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    sections = db.relationship('Section', backref='school_class', lazy=True, cascade='all, delete-orphan')
    subject_classes = db.relationship('SubjectClass', backref='school_class', lazy=True, cascade='all, delete-orphan')
    students = db.relationship('Student', backref='school_class', lazy=True)
    homeworks = db.relationship('Homework', lazy=True, cascade='all, delete-orphan')
    timetables = db.relationship('Timetable', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<SchoolClass {self.display_name} (Session #{self.academic_session_id})>'
