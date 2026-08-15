from datetime import datetime
from app.models import db

class AcademicSession(db.Model):
    __tablename__ = 'academic_sessions'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False) # e.g. "2026-2027"
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    is_active = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    classes = db.relationship('SchoolClass', backref='academic_session', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<AcademicSession {self.name} [Active: {self.is_active}]>'
