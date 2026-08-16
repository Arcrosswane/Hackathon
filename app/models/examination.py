from datetime import datetime
from app.models import db

class ExamType(db.Model):
    __tablename__ = 'exam_types'

    id = db.Column(db.Integer, primary_key=True)
    institute_id = db.Column(db.Integer, db.ForeignKey('institutes.id'), nullable=True) # School ID
    name = db.Column(db.String(100), nullable=False) # e.g. "Unit Test", "Half Yearly", "Annual", "Pre-Board"
    code = db.Column(db.String(30), nullable=True) # e.g. "UT", "HY", "ANN"
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code or '',
            'description': self.description or '',
            'is_active': self.is_active
        }


class Examination(db.Model):
    __tablename__ = 'examinations'

    id = db.Column(db.Integer, primary_key=True)
    institute_id = db.Column(db.Integer, db.ForeignKey('institutes.id'), nullable=True)
    academic_session_id = db.Column(db.Integer, db.ForeignKey('academic_sessions.id'), nullable=False)
    exam_type_id = db.Column(db.Integer, db.ForeignKey('exam_types.id'), nullable=True)
    
    name = db.Column(db.String(150), nullable=False) # e.g. "Mid-Term Examination 2026"
    description = db.Column(db.Text, nullable=True)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    
    # Statuses: DRAFT, SCHEDULED, ONGOING, COMPLETED, RESULT_PUBLISHED, ARCHIVED
    status = db.Column(db.String(30), nullable=False, default="DRAFT")
    
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    academic_session = db.relationship('AcademicSession', foreign_keys=[academic_session_id], lazy=True)
    exam_type = db.relationship('ExamType', foreign_keys=[exam_type_id], lazy=True)
    created_by = db.relationship('User', foreign_keys=[created_by_id], lazy=True)
    
    exam_classes = db.relationship('ExaminationClass', backref='examination', lazy=True, cascade='all, delete-orphan')
    exam_subjects = db.relationship('ExaminationSubject', backref='examination', lazy=True, cascade='all, delete-orphan')
    results = db.relationship('ExaminationResult', backref='examination', lazy=True, cascade='all, delete-orphan')
    overall_results = db.relationship('ExamOverallResult', backref='examination', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Examination #{self.id}: {self.name} [{self.status}]>'


class ExaminationClass(db.Model):
    __tablename__ = 'examination_classes'

    id = db.Column(db.Integer, primary_key=True)
    examination_id = db.Column(db.Integer, db.ForeignKey('examinations.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'), nullable=True) # If null, applies to all sections

    # Relationships
    school_class = db.relationship('SchoolClass', foreign_keys=[class_id], lazy=True)
    section = db.relationship('Section', foreign_keys=[section_id], lazy=True)


class ExaminationSubject(db.Model):
    __tablename__ = 'examination_subjects'

    id = db.Column(db.Integer, primary_key=True)
    examination_id = db.Column(db.Integer, db.ForeignKey('examinations.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'), nullable=True) # Optional section specific
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    
    exam_date = db.Column(db.Date, nullable=True)
    start_time = db.Column(db.Time, nullable=True)
    end_time = db.Column(db.Time, nullable=True)
    
    max_marks = db.Column(db.Float, nullable=False, default=100.0)
    pass_marks = db.Column(db.Float, nullable=False, default=33.0)
    
    # Module 15 Question Paper Attachment
    question_paper_id = db.Column(db.Integer, db.ForeignKey('question_papers.id'), nullable=True)
    
    status = db.Column(db.String(20), nullable=False, default="SCHEDULED") # SCHEDULED, COMPLETED, EVALUATED
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    school_class = db.relationship('SchoolClass', foreign_keys=[class_id], lazy=True)
    section = db.relationship('Section', foreign_keys=[section_id], lazy=True)
    subject = db.relationship('Subject', foreign_keys=[subject_id], lazy=True)
    question_paper = db.relationship('QuestionPaper', foreign_keys=[question_paper_id], lazy=True)


class ExaminationResult(db.Model):
    __tablename__ = 'examination_results'

    id = db.Column(db.Integer, primary_key=True)
    institute_id = db.Column(db.Integer, db.ForeignKey('institutes.id'), nullable=True)
    academic_session_id = db.Column(db.Integer, db.ForeignKey('academic_sessions.id'), nullable=True)
    
    examination_id = db.Column(db.Integer, db.ForeignKey('examinations.id'), nullable=False)
    exam_subject_id = db.Column(db.Integer, db.ForeignKey('examination_subjects.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=True)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'), nullable=True)
    
    attendance_status = db.Column(db.String(10), nullable=False, default="PRESENT") # PRESENT, ABSENT
    marks_obtained = db.Column(db.Float, nullable=True) # Null if ABSENT or not entered
    max_marks = db.Column(db.Float, nullable=False, default=100.0)
    percentage = db.Column(db.Float, nullable=True)
    grade = db.Column(db.String(10), nullable=True)
    is_pass = db.Column(db.Boolean, nullable=True)
    
    # Statuses: DRAFT, SUBMITTED, APPROVED, PUBLISHED
    status = db.Column(db.String(20), nullable=False, default="DRAFT")
    
    entered_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    exam_subject = db.relationship('ExaminationSubject', foreign_keys=[exam_subject_id], lazy=True)
    student = db.relationship('Student', foreign_keys=[student_id], lazy=True)
    school_class = db.relationship('SchoolClass', foreign_keys=[class_id], lazy=True)
    section = db.relationship('Section', foreign_keys=[section_id], lazy=True)
    entered_by = db.relationship('User', foreign_keys=[entered_by_id], lazy=True)

    __table_args__ = (
        db.UniqueConstraint('examination_id', 'exam_subject_id', 'student_id', name='uq_student_exam_subject'),
        db.Index('idx_res_student', 'student_id', 'status'),
        db.Index('idx_res_exam_class', 'examination_id', 'class_id'),
    )


class ExamOverallResult(db.Model):
    __tablename__ = 'exam_overall_results'

    id = db.Column(db.Integer, primary_key=True)
    institute_id = db.Column(db.Integer, db.ForeignKey('institutes.id'), nullable=True)
    academic_session_id = db.Column(db.Integer, db.ForeignKey('academic_sessions.id'), nullable=True)
    
    examination_id = db.Column(db.Integer, db.ForeignKey('examinations.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=True)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'), nullable=True)
    
    total_obtained = db.Column(db.Float, nullable=False, default=0.0)
    total_max = db.Column(db.Float, nullable=False, default=0.0)
    overall_percentage = db.Column(db.Float, nullable=False, default=0.0)
    overall_grade = db.Column(db.String(10), nullable=True)
    
    overall_result = db.Column(db.String(10), nullable=False, default="PASS") # PASS, FAIL
    status = db.Column(db.String(20), nullable=False, default="DRAFT") # DRAFT, PUBLISHED
    
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    student = db.relationship('Student', foreign_keys=[student_id], lazy=True)
    school_class = db.relationship('SchoolClass', foreign_keys=[class_id], lazy=True)
    section = db.relationship('Section', foreign_keys=[section_id], lazy=True)

    __table_args__ = (
        db.UniqueConstraint('examination_id', 'student_id', name='uq_student_overall_exam'),
    )


class GradeRule(db.Model):
    __tablename__ = 'grade_rules'

    id = db.Column(db.Integer, primary_key=True)
    institute_id = db.Column(db.Integer, db.ForeignKey('institutes.id'), nullable=True)
    
    name = db.Column(db.String(50), nullable=False, default="CBSE Standard")
    min_percentage = db.Column(db.Float, nullable=False)
    max_percentage = db.Column(db.Float, nullable=False)
    grade = db.Column(db.String(10), nullable=False) # e.g. "A1", "A2", "B1", "B2", "C1", "C2", "D", "E"
    description = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'grade': self.grade,
            'min_percentage': self.min_percentage,
            'max_percentage': self.max_percentage,
            'description': self.description or ''
        }
