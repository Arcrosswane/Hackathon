from datetime import datetime
from app.models import db

class SubjectClass(db.Model):
    __tablename__ = 'subject_classes'
    __table_args__ = (
        db.UniqueConstraint('subject_id', 'class_id', name='uq_subject_class_assignment'),
    )

    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    teacher = db.relationship('Employee', backref='assigned_subject_classes', lazy=True)

    def __repr__(self):
        return f'<SubjectClass Subject #{self.subject_id} -> Class #{self.class_id} (Teacher #{self.teacher_id})>'
