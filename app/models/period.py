from datetime import datetime
from app.models import db

class Period(db.Model):
    __tablename__ = 'periods'
    __table_args__ = (
        db.UniqueConstraint('academic_session_id', 'period_order', name='uq_session_period_order'),
    )

    id = db.Column(db.Integer, primary_key=True)
    academic_session_id = db.Column(db.Integer, db.ForeignKey('academic_sessions.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False) # e.g. "Period 1", "Lunch Break", "Period 4"
    period_order = db.Column(db.Integer, default=1, nullable=False) # 1, 2, 3, 4...
    start_time = db.Column(db.Time, nullable=False) # e.g. 09:00:00
    end_time = db.Column(db.Time, nullable=False) # e.g. 09:45:00
    period_type = db.Column(db.String(30), default="CLASS", nullable=False) # CLASS, BREAK, LUNCH, ACTIVITY, FREE
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    academic_session = db.relationship('AcademicSession', lazy=True)
    timetables = db.relationship('Timetable', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Period #{self.period_order}: {self.name} ({self.start_time.strftime("%H:%M")}-{self.end_time.strftime("%H:%M")}) [{self.period_type}]>'
