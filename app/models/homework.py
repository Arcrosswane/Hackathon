from datetime import datetime
from app.models import db

class Homework(db.Model):
    __tablename__ = 'homework'

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=True)
    academic_session_id = db.Column(db.Integer, db.ForeignKey('academic_sessions.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False) # Teacher who created the assignment
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'), nullable=True) # Target Section (NULL = All Sections of Class)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True) # Instructions
    assigned_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    max_marks = db.Column(db.Numeric(5, 2), nullable=True, default=100.00)
    status = db.Column(db.String(30), default='DRAFT', nullable=False) # 'DRAFT', 'PUBLISHED', 'ARCHIVED'
    
    # AI vs Manual Evaluation Settings
    evaluation_type = db.Column(db.String(20), default='MANUAL', nullable=False) # 'MANUAL', 'AI'
    grading_rubric = db.Column(db.Text, nullable=True) # Solution key / grading criteria for AI

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Explicit Relationships
    academic_session = db.relationship('AcademicSession', lazy=True)
    teacher = db.relationship('Employee', foreign_keys=[teacher_id], lazy=True)
    school_class = db.relationship('SchoolClass', lazy=True)
    section = db.relationship('Section', lazy=True)
    subject = db.relationship('Subject', lazy=True)
    attachments = db.relationship('HomeworkAttachment', backref='homework', lazy=True, cascade='all, delete-orphan')
    submissions = db.relationship('HomeworkSubmission', backref='homework', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Homework #{self.id} {self.title} [{self.evaluation_type}] [{self.status}]>'


class HomeworkAttachment(db.Model):
    __tablename__ = 'homework_attachments'

    id = db.Column(db.Integer, primary_key=True)
    homework_id = db.Column(db.Integer, db.ForeignKey('homework.id'), nullable=False)
    file_path = db.Column(db.String(255), nullable=False) # Relative storage path
    original_filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer, nullable=True) # Bytes
    file_type = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<HomeworkAttachment {self.original_filename} for HW #{self.homework_id}>'


class HomeworkSubmission(db.Model):
    __tablename__ = 'homework_submissions'
    __table_args__ = (
        db.UniqueConstraint('homework_id', 'student_id', name='uq_homework_student_submission'),
    )

    id = db.Column(db.Integer, primary_key=True)
    homework_id = db.Column(db.Integer, db.ForeignKey('homework.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.String(30), default='SUBMITTED', nullable=False) # 'SUBMITTED', 'LATE', 'REVIEWED'
    
    submission_text = db.Column(db.Text, nullable=True)
    attachment_path = db.Column(db.String(255), nullable=True)
    original_filename = db.Column(db.String(255), nullable=True)
    
    marks = db.Column(db.Numeric(5, 2), nullable=True)
    feedback = db.Column(db.Text, nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=True)

    # AI Evaluation Metadata
    ai_evaluated = db.Column(db.Boolean, default=False, nullable=False)
    ai_reasoning = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    student = db.relationship('Student', lazy=True)
    reviewed_by = db.relationship('Employee', foreign_keys=[reviewed_by_id], lazy=True)

    def __repr__(self):
        return f'<HomeworkSubmission HW #{self.homework_id} Student #{self.student_id} [{self.status}]>'
