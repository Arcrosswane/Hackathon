from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import db

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=True) # Linked to School profile
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    user_type = db.Column(db.String(20), nullable=False) # "Admin", "Employee", "Student"
    linked_entity_id = db.Column(db.Integer, nullable=True) # Linked to Employee ID or Student ID
    profile_photo_url = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to School
    school = db.relationship('School', backref='users', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username} [{self.user_type}] (School #{self.school_id})>'
