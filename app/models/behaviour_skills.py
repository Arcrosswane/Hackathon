from datetime import datetime
from app.models import db

class BehaviourCategory(db.Model):
    __tablename__ = 'behaviour_categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    records = db.relationship('BehaviourRecord', backref='category', lazy=True)

    def __repr__(self):
        return f'<BehaviourCategory {self.name}>'


class BehaviourRecord(db.Model):
    __tablename__ = 'behaviour_records'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    assessor_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    academic_session_id = db.Column(db.Integer, db.ForeignKey('academic_sessions.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('behaviour_categories.id'), nullable=False)

    type = db.Column(db.String(20), nullable=False, default='POSITIVE')  # 'POSITIVE', 'OBSERVATION', 'IMPROVEMENT'
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    date = db.Column(db.Date, nullable=False)
    severity = db.Column(db.String(20), default='LOW', nullable=False)  # 'LOW', 'MEDIUM', 'HIGH'
    visibility = db.Column(db.String(30), default='BOTH', nullable=False)  # 'INTERNAL', 'STUDENT_VISIBLE', 'PARENT_VISIBLE', 'BOTH'

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    student = db.relationship('Student', lazy=True)
    assessor = db.relationship('Employee', lazy=True)
    academic_session = db.relationship('AcademicSession', lazy=True)
    school_class = db.relationship('SchoolClass', lazy=True)
    section = db.relationship('Section', lazy=True)

    def __repr__(self):
        return f'<BehaviourRecord #{self.id} {self.type} - Student #{self.student_id}>'


class SkillDefinition(db.Model):
    __tablename__ = 'skill_definitions'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    group_name = db.Column(db.String(50), nullable=True, default='General')  # e.g. 'Communication', 'Social', 'Thinking', 'Self-Management'
    description = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    assessments = db.relationship('SkillAssessment', backref='skill', lazy=True)

    def __repr__(self):
        return f'<SkillDefinition {self.name} [{self.group_name}]>'


class SkillAssessment(db.Model):
    __tablename__ = 'skill_assessments'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skill_definitions.id'), nullable=False)
    assessor_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    academic_session_id = db.Column(db.Integer, db.ForeignKey('academic_sessions.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'), nullable=True)

    rating = db.Column(db.Integer, nullable=False, default=3)  # 1 to 5 scale
    observation = db.Column(db.Text, nullable=True)
    assessment_date = db.Column(db.Date, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    student = db.relationship('Student', lazy=True)
    assessor = db.relationship('Employee', lazy=True)
    academic_session = db.relationship('AcademicSession', lazy=True)
    school_class = db.relationship('SchoolClass', lazy=True)
    section = db.relationship('Section', lazy=True)

    def __repr__(self):
        return f'<SkillAssessment Skill #{self.skill_id} Rating {self.rating} - Student #{self.student_id}>'
