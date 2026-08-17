from datetime import datetime
from app.models import db

class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Category & Priority
    category = db.Column(db.String(40), default='System', nullable=False) # Academic, Attendance, Homework, Exams, Fees, Communication, School, Behaviour, System
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), default='Normal', nullable=False) # Normal, Important, Urgent
    
    # Entity reference & Deep link
    related_entity_type = db.Column(db.String(50), nullable=True) # Message, Homework, Examination, Attendance, FeeInvoice, SchoolNotice
    related_entity_id = db.Column(db.Integer, nullable=True)
    action_url = db.Column(db.String(255), nullable=True)
    
    # State
    read_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    recipient = db.relationship('User', lazy=True)
    school = db.relationship('School', lazy=True)

    def is_read(self):
        return self.read_at is not None

    def __repr__(self):
        return f'<Notification #{self.id} Recipient #{self.recipient_id} [{self.category}] Priority={self.priority}>'


class NotificationPreference(db.Model):
    __tablename__ = 'notification_preferences'
    __table_args__ = (
        db.UniqueConstraint('user_id', 'category', name='uq_user_category_preference'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category = db.Column(db.String(40), nullable=False)
    is_enabled = db.Column(db.Boolean, default=True, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = db.relationship('User', lazy=True)

    def __repr__(self):
        return f'<NotificationPreference User #{self.user_id} Category={self.category} Enabled={self.is_enabled}>'
