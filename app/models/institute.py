from datetime import datetime
from app.models import db

class Institute(db.Model):
    __tablename__ = 'institutes'

    id = db.Column(db.Integer, primary_key=True)
    institute_name = db.Column(db.String(150), nullable=False)
    email_address = db.Column(db.String(120), nullable=False)
    email_verification_status = db.Column(db.Boolean, default=False)
    account_created_date = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    classes = db.relationship('SchoolClass', backref='institute', lazy=True, cascade='all, delete-orphan')
    employees = db.relationship('Employee', backref='institute', lazy=True, cascade='all, delete-orphan')
    students = db.relationship('Student', backref='institute', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Institute {self.institute_name}>'
