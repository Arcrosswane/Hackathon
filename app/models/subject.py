from datetime import datetime
from app.models import db

class Subject(db.Model):
    __tablename__ = 'subjects'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), nullable=True) # e.g. "MAT", "SCI", "ENG", "SST"
    name = db.Column(db.String(100), unique=True, nullable=False) # e.g. "Mathematics"
    short_name = db.Column(db.String(50), nullable=True) # e.g. "Maths"
    subject_type = db.Column(db.String(30), nullable=False, default="core") # core, elective, optional, co_curricular
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    subject_classes = db.relationship('SubjectClass', backref='subject', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Subject {self.name} ({self.code or "No Code"}) [{self.subject_type}]>'
