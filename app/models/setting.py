from datetime import datetime
from app.models import db

class Setting(db.Model):
    __tablename__ = 'settings'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Setting {self.key}={self.value}>'


class RolePermission(db.Model):
    __tablename__ = 'role_permissions'
    __table_args__ = (
        db.UniqueConstraint('role_name', 'permission_key', name='uq_role_permission'),
    )

    id = db.Column(db.Integer, primary_key=True)
    role_name = db.Column(db.String(50), nullable=False, index=True)  # ADMIN, TEACHER, STUDENT, PARENT
    permission_key = db.Column(db.String(100), nullable=False, index=True)  # e.g., 'students.view'
    is_granted = db.Column(db.Boolean, default=True, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<RolePermission {self.role_name}:{self.permission_key}={self.is_granted}>'


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('institutes.id'), nullable=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)

    action = db.Column(db.String(150), nullable=False)
    module = db.Column(db.String(50), nullable=False, index=True)
    details = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], lazy=True)

    def __repr__(self):
        return f'<AuditLog #{self.id} {self.module}:{self.action}>'
