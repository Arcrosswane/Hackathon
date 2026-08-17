from datetime import datetime
from app.models import db

class Certificate(db.Model):
    __tablename__ = 'certificates'

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('institutes.id'), nullable=True, index=True)
    certificate_number = db.Column(db.String(50), nullable=False, unique=True, index=True)
    
    # Types: "Transfer Certificate", "Character Certificate", "Bonafide Certificate", "Study Certificate", "Merit Certificate", "Conduct Certificate"
    certificate_type = db.Column(db.String(100), nullable=False, index=True)
    
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, index=True)
    issued_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    issue_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    # Status: Draft, Issued, Cancelled
    status = db.Column(db.String(20), nullable=False, default="Issued", index=True)
    
    remarks = db.Column(db.Text, nullable=True)
    extra_data = db.Column(db.Text, nullable=True)  # JSON string storing conduct, academic session, reason for issue, etc.
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    student = db.relationship('Student', foreign_keys=[student_id], lazy=True)
    issued_by = db.relationship('User', foreign_keys=[issued_by_id], lazy=True)

    def __repr__(self):
        return f'<Certificate #{self.certificate_number} [{self.certificate_type}] - Student #{self.student_id}>'
