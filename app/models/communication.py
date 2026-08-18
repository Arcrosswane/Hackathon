from datetime import datetime
from app.models import db

class CommunicationProviderConfig(db.Model):
    __tablename__ = 'communication_provider_configs'

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('institutes.id'), nullable=True, index=True)
    
    # Provider Type: "SMS", "WhatsApp"
    provider_type = db.Column(db.String(20), nullable=False, index=True)
    provider_name = db.Column(db.String(50), nullable=False, default="Twilio Gateway")  # e.g. Twilio, Msg91, Meta WhatsApp API
    
    is_enabled = db.Column(db.Boolean, default=False, nullable=False)
    is_configured = db.Column(db.Boolean, default=False, nullable=False)
    
    api_key_masked = db.Column(db.String(100), nullable=True)  # Masked display key e.g. "SK_live_****89a2"
    sender_id_or_number = db.Column(db.String(50), nullable=True)  # e.g. "STRATL", "+14155552671"
    
    config_json = db.Column(db.Text, nullable=True)  # Encrypted/JSON config storage
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<CommunicationProviderConfig [{self.provider_type} - {self.provider_name}] Enabled={self.is_enabled}>'


class CommunicationTemplate(db.Model):
    __tablename__ = 'communication_templates'

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('institutes.id'), nullable=True, index=True)
    
    name = db.Column(db.String(100), nullable=False) # e.g. "Fee Payment Reminder", "Exam Result Notification", "Holiday Announcement"
    channel = db.Column(db.String(20), nullable=False, default="SMS") # SMS, WhatsApp, Email, System
    template_code = db.Column(db.String(50), nullable=False, index=True)
    
    content_template = db.Column(db.Text, nullable=False) # e.g. "Dear {{parent_name}}, fee invoice {{invoice_number}} for {{student_name}} of amount {{amount}} is due on {{due_date}}."
    variables_json = db.Column(db.Text, nullable=True) # e.g. "['parent_name', 'invoice_number', 'student_name', 'amount', 'due_date']"
    
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<CommunicationTemplate #{self.id} [{self.name}] Channel={self.channel}>'
