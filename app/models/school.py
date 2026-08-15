from datetime import datetime
from app.models import db

class School(db.Model):
    __tablename__ = 'schools'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, default="TPS School")
    school_code = db.Column(db.String(50), nullable=True, default="TPS-001")
    logo = db.Column(db.String(255), nullable=True)
    email = db.Column(db.String(120), nullable=True, default="contact@tps.edu")
    phone = db.Column(db.String(30), nullable=True, default="+91 98765 43210")
    website = db.Column(db.String(150), nullable=True, default="https://www.tps.edu")
    address = db.Column(db.Text, nullable=True, default="123 Education Boulevard")
    city = db.Column(db.String(100), nullable=True, default="Bengaluru")
    state = db.Column(db.String(100), nullable=True, default="Karnataka")
    country = db.Column(db.String(100), nullable=True, default="India")
    postal_code = db.Column(db.String(20), nullable=True, default="560001")
    principal_name = db.Column(db.String(100), nullable=True, default="Dr. Academic Director")
    academic_session = db.Column(db.String(50), nullable=True, default="2026-27")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Hybrid property alias for school_name
    @property
    def school_name(self):
        return self.name

    @school_name.setter
    def school_name(self, value):
        self.name = value

    def __repr__(self):
        return f'<School {self.name} ({self.school_code}) [Session: {self.academic_session}]>'
