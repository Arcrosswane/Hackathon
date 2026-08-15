from datetime import datetime
from app.models import db

class GuardianStudent(db.Model):
    __tablename__ = 'guardian_students'
    __table_args__ = (
        db.UniqueConstraint('guardian_id', 'student_id', name='uq_guardian_student_link'),
    )

    id = db.Column(db.Integer, primary_key=True)
    guardian_id = db.Column(db.Integer, db.ForeignKey('guardians.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    
    # Relationship Metadata
    relationship = db.Column(db.String(50), default="Father", nullable=False) # Father, Mother, Guardian, Grandfather, Grandmother, Uncle, Aunt, Other
    is_primary = db.Column(db.Boolean, default=False, nullable=False)
    is_emergency_contact = db.Column(db.Boolean, default=False, nullable=False)
    can_receive_notifications = db.Column(db.Boolean, default=True, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    student = db.relationship('Student', backref=db.backref('guardian_links', lazy=True, cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<GuardianStudent Guardian #{self.guardian_id} ↔ Student #{self.student_id} ({self.relationship}) [Primary: {self.is_primary}]>'
