from datetime import datetime
import json
from app.models import db

class Question(db.Model):
    __tablename__ = 'questions'

    id = db.Column(db.Integer, primary_key=True)
    institute_id = db.Column(db.Integer, db.ForeignKey('institutes.id'), nullable=True) # School ID
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=True)
    
    chapter = db.Column(db.String(100), nullable=True) # e.g. "Number Systems", "Photosynthesis"
    topic = db.Column(db.String(100), nullable=True) # Optional sub-topic
    
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(30), nullable=False, default="MCQ") 
    # MCQ, SHORT_ANSWER, LONG_ANSWER, VERY_SHORT_ANSWER, TRUE_FALSE, FILL_IN_THE_BLANK, CASE_BASED, NUMERICAL
    
    difficulty = db.Column(db.String(20), nullable=False, default="MEDIUM") # EASY, MEDIUM, HARD
    marks = db.Column(db.Float, nullable=False, default=1.0)
    
    # Options for MCQ
    option_a = db.Column(db.String(255), nullable=True)
    option_b = db.Column(db.String(255), nullable=True)
    option_c = db.Column(db.String(255), nullable=True)
    option_d = db.Column(db.String(255), nullable=True)
    correct_option = db.Column(db.String(10), nullable=True) # "A", "B", "C", "D"
    
    answer_text = db.Column(db.Text, nullable=True) # Model answer / key points
    explanation = db.Column(db.Text, nullable=True) # Detailed solution explanation
    tags = db.Column(db.String(255), nullable=True) # Comma separated e.g. "NCERT,Important,HOTS"
    
    status = db.Column(db.String(20), nullable=False, default="ACTIVE") # ACTIVE, ARCHIVED, AI_GENERATED
    visibility = db.Column(db.String(20), nullable=False, default="SCHOOL_SHARED") # PRIVATE, SCHOOL_SHARED
    
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    school_class = db.relationship('SchoolClass', foreign_keys=[class_id], lazy=True)
    subject = db.relationship('Subject', foreign_keys=[subject_id], lazy=True)
    created_by = db.relationship('User', foreign_keys=[created_by_id], lazy=True)

    __table_args__ = (
        db.Index('idx_q_class_subj', 'class_id', 'subject_id'),
        db.Index('idx_q_diff_type', 'difficulty', 'question_type'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'question_text': self.question_text,
            'question_type': self.question_type,
            'difficulty': self.difficulty,
            'marks': self.marks,
            'chapter': self.chapter or '',
            'topic': self.topic or '',
            'option_a': self.option_a or '',
            'option_b': self.option_b or '',
            'option_c': self.option_c or '',
            'option_d': self.option_d or '',
            'correct_option': self.correct_option or '',
            'answer_text': self.answer_text or '',
            'explanation': self.explanation or '',
            'tags': self.tags or ''
        }

    def __repr__(self):
        return f'<Question #{self.id} [{self.question_type} - {self.marks}m]: {self.question_text[:30]}...>'


class QuestionPaper(db.Model):
    __tablename__ = 'question_papers'

    id = db.Column(db.Integer, primary_key=True)
    institute_id = db.Column(db.Integer, db.ForeignKey('institutes.id'), nullable=True)
    academic_session_id = db.Column(db.Integer, db.ForeignKey('academic_sessions.id'), nullable=True)
    
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    
    title = db.Column(db.String(150), nullable=False) # e.g. "Mid-Term Examination 2026"
    instructions = db.Column(db.Text, nullable=True)
    duration_minutes = db.Column(db.Integer, nullable=False, default=90)
    total_marks = db.Column(db.Float, nullable=False, default=0.0) # Calculated server-side
    
    status = db.Column(db.String(20), nullable=False, default="DRAFT") # DRAFT, FINAL, ARCHIVED
    
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    school_class = db.relationship('SchoolClass', foreign_keys=[class_id], lazy=True)
    subject = db.relationship('Subject', foreign_keys=[subject_id], lazy=True)
    created_by = db.relationship('User', foreign_keys=[created_by_id], lazy=True)
    sections = db.relationship('QuestionPaperSection', backref='paper', lazy=True, cascade='all, delete-orphan', order_by='QuestionPaperSection.section_order')

    def __repr__(self):
        return f'<QuestionPaper #{self.id} "{self.title}" [{self.status} - {self.total_marks}m]>'


class QuestionPaperSection(db.Model):
    __tablename__ = 'question_paper_sections'

    id = db.Column(db.Integer, primary_key=True)
    paper_id = db.Column(db.Integer, db.ForeignKey('question_papers.id'), nullable=False)
    
    section_name = db.Column(db.String(50), nullable=False, default="Section A") # Section A, Section B
    section_instructions = db.Column(db.Text, nullable=True)
    section_order = db.Column(db.Integer, nullable=False, default=1)
    total_section_marks = db.Column(db.Float, nullable=False, default=0.0)

    # Relationships
    paper_questions = db.relationship('QuestionPaperQuestion', backref='section', lazy=True, cascade='all, delete-orphan', order_by='QuestionPaperQuestion.question_order')

    def __repr__(self):
        return f'<QuestionPaperSection #{self.id} "{self.section_name}" Paper #{self.paper_id}>'


class QuestionPaperQuestion(db.Model):
    __tablename__ = 'question_paper_questions'

    id = db.Column(db.Integer, primary_key=True)
    section_id = db.Column(db.Integer, db.ForeignKey('question_paper_sections.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=True)
    
    question_order = db.Column(db.Integer, nullable=False, default=1)
    marks = db.Column(db.Float, nullable=False, default=1.0)
    
    # Immutable snapshot serialized at paper finalization time
    question_snapshot_json = db.Column(db.Text, nullable=True)

    # Relationships
    question = db.relationship('Question', foreign_keys=[question_id], lazy=True)

    @property
    def snapshot_data(self):
        if self.question_snapshot_json:
            try:
                return json.loads(self.question_snapshot_json)
            except Exception:
                pass
        if self.question:
            return self.question.to_dict()
        return {}

    def __repr__(self):
        return f'<QuestionPaperQuestion #{self.id} Sec #{self.section_id} Q #{self.question_id}>'


class AIQuestionGenerationLog(db.Model):
    __tablename__ = 'ai_question_generation_logs'

    id = db.Column(db.Integer, primary_key=True)
    institute_id = db.Column(db.Integer, db.ForeignKey('institutes.id'), nullable=True)
    requested_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=True)
    
    chapters = db.Column(db.String(255), nullable=True)
    difficulty = db.Column(db.String(20), nullable=True)
    question_types = db.Column(db.String(255), nullable=True)
    prompt_summary = db.Column(db.Text, nullable=True)
    
    response_status = db.Column(db.String(20), nullable=False, default="SUCCESS") # SUCCESS, FAILED
    questions_generated = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<AIQuestionGenerationLog #{self.id}: {self.questions_generated} Qs [{self.response_status}]>'
