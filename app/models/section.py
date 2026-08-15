from datetime import datetime
from app.models import db

class Section(db.Model):
    __tablename__ = 'sections'
    __table_args__ = (
        db.UniqueConstraint('class_id', 'name', name='uq_class_section_name'),
    )

    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False) # e.g. "A", "B", "E"
    display_name = db.Column(db.String(100), nullable=False) # e.g. "Section A"
    capacity = db.Column(db.Integer, nullable=True, default=40)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Section {self.display_name} (Class #{self.class_id})>'
