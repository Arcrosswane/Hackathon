from datetime import datetime
from app.models import db

class SyllabusChapter(db.Model):
    __tablename__ = 'syllabus_chapters'

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('institutes.id'), nullable=True, index=True)
    academic_session_id = db.Column(db.Integer, db.ForeignKey('academic_sessions.id'), nullable=True, index=True)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False, index=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False, index=True)

    chapter_name = db.Column(db.String(150), nullable=False)
    chapter_number = db.Column(db.Integer, nullable=True, default=1)
    description = db.Column(db.Text, nullable=True)
    display_order = db.Column(db.Integer, default=1, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    school_class = db.relationship('SchoolClass', foreign_keys=[class_id], lazy=True)
    subject = db.relationship('Subject', foreign_keys=[subject_id], lazy=True)
    academic_session = db.relationship('AcademicSession', foreign_keys=[academic_session_id], lazy=True)
    topics = db.relationship('SyllabusTopic', backref='chapter', lazy=True, cascade='all, delete-orphan', order_by='SyllabusTopic.display_order')

    def __repr__(self):
        return f'<SyllabusChapter #{self.id} Ch {self.chapter_number}: {self.chapter_name}>'


class SyllabusTopic(db.Model):
    __tablename__ = 'syllabus_topics'

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('institutes.id'), nullable=True, index=True)
    chapter_id = db.Column(db.Integer, db.ForeignKey('syllabus_chapters.id'), nullable=False, index=True)

    topic_name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    display_order = db.Column(db.Integer, default=1, nullable=False)

    # Teaching Status: NOT_STARTED, IN_PROGRESS, COMPLETED
    teaching_status = db.Column(db.String(20), nullable=False, default="NOT_STARTED", index=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    completed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    updated_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    completed_by = db.relationship('User', foreign_keys=[completed_by_id], lazy=True)
    updated_by = db.relationship('User', foreign_keys=[updated_by_id], lazy=True)

    def is_completed(self):
        return self.teaching_status == 'COMPLETED'

    def __repr__(self):
        return f'<SyllabusTopic #{self.id} {self.topic_name} [{self.teaching_status}]>'


class NotebookCorrection(db.Model):
    __tablename__ = 'notebook_corrections'
    __table_args__ = (
        db.UniqueConstraint('student_id', 'topic_id', 'academic_session_id', name='uq_student_topic_correction'),
    )

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('institutes.id'), nullable=True, index=True)
    academic_session_id = db.Column(db.Integer, db.ForeignKey('academic_sessions.id'), nullable=True, index=True)
    
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False, index=True)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'), nullable=True, index=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False, index=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('syllabus_topics.id'), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, index=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Status: PENDING, SUBMITTED, CORRECTED
    status = db.Column(db.String(20), nullable=False, default="PENDING", index=True)
    remarks = db.Column(db.String(255), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    student = db.relationship('Student', foreign_keys=[student_id], lazy=True)
    topic = db.relationship('SyllabusTopic', foreign_keys=[topic_id], lazy=True)
    teacher = db.relationship('User', foreign_keys=[teacher_id], lazy=True)

    def __repr__(self):
        return f'<NotebookCorrection Student #{self.student_id} Topic #{self.topic_id} [{self.status}]>'


class SyllabusTarget(db.Model):
    __tablename__ = 'syllabus_targets'
    __table_args__ = (
        db.UniqueConstraint('school_id', 'academic_session_id', 'month', 'year', 'class_id', 'subject_id', 'teacher_id', name='uq_school_session_month_target'),
    )

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('institutes.id'), nullable=True, index=True)
    academic_session_id = db.Column(db.Integer, db.ForeignKey('academic_sessions.id'), nullable=True, index=True)

    month = db.Column(db.Integer, nullable=False)  # 1 to 12
    year = db.Column(db.Integer, nullable=False, default=2026)
    month_name = db.Column(db.String(50), nullable=True)  # e.g. "August 2026"

    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False, index=True)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'), nullable=True, index=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False, index=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False, index=True)

    target_topic_count = db.Column(db.Integer, nullable=False, default=10)
    tolerance_margin = db.Column(db.Integer, nullable=False, default=1)

    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    school_class = db.relationship('SchoolClass', foreign_keys=[class_id], lazy=True)
    section = db.relationship('Section', foreign_keys=[section_id], lazy=True)
    subject = db.relationship('Subject', foreign_keys=[subject_id], lazy=True)
    teacher = db.relationship('Employee', foreign_keys=[teacher_id], lazy=True)
    created_by = db.relationship('User', foreign_keys=[created_by_id], lazy=True)

    def __repr__(self):
        return f'<SyllabusTarget Class #{self.class_id} Subject #{self.subject_id} Teacher #{self.teacher_id} Month {self.month}/{self.year} Target: {self.target_topic_count}>'
