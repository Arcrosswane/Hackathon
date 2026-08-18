from datetime import datetime
from app.models import db

class SchoolCircular(db.Model):
    __tablename__ = 'school_circulars'

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('institutes.id'), nullable=True, index=True)
    circular_number = db.Column(db.String(50), nullable=False, unique=True, index=True)
    
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    
    # Target Audience: "Entire School", "Teachers", "Students", "Parents", "Class", "Section"
    target_audience = db.Column(db.String(50), nullable=False, default="Entire School", index=True)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=True)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'), nullable=True)
    
    published_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    issue_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    attachment_path = db.Column(db.String(255), nullable=True)
    
    # Status: Draft, Published, Archived
    status = db.Column(db.String(20), nullable=False, default="Published", index=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    published_by = db.relationship('User', foreign_keys=[published_by_id], lazy=True)
    school_class = db.relationship('SchoolClass', foreign_keys=[class_id], lazy=True)
    section = db.relationship('Section', foreign_keys=[section_id], lazy=True)

    def __repr__(self):
        return f'<SchoolCircular #{self.circular_number} [{self.title}] Audience={self.target_audience}>'
