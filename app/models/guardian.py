from datetime import datetime
from app.models import db

class Guardian(db.Model):
    __tablename__ = 'guardians'

    id = db.Column(db.Integer, primary_key=True)
    institute_id = db.Column(db.Integer, db.ForeignKey('institutes.id'), nullable=True)
    registration_number = db.Column(db.String(50), unique=True, nullable=False) # Guardian Code (e.g. "PAR001", "GDN001")
    
    # Name fields
    first_name = db.Column(db.String(50), nullable=False, default="Parent")
    middle_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    full_name = db.Column(db.String(150), nullable=False, default="Parent / Guardian")

    # Professional & Personal Details
    occupation = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    status = db.Column(db.String(30), default="Active", nullable=False)

    # Contact Details
    email_address = db.Column(db.String(120), nullable=True)
    mobile_phone_number = db.Column(db.String(20), nullable=True)
    alternate_phone = db.Column(db.String(20), nullable=True)

    # Address
    home_address = db.Column(db.Text, nullable=True)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)
    country = db.Column(db.String(100), nullable=True, default="India")
    postal_code = db.Column(db.String(20), nullable=True)

    # Metadata & Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    student_links = db.relationship('GuardianStudent', backref='guardian', lazy=True, cascade='all, delete-orphan')

    # Property Aliases
    @property
    def guardian_code(self):
        return self.registration_number

    @guardian_code.setter
    def guardian_code(self, val):
        self.registration_number = val

    @property
    def email(self):
        return self.email_address

    @email.setter
    def email(self, val):
        self.email_address = val

    @property
    def phone(self):
        return self.mobile_phone_number

    @phone.setter
    def phone(self, val):
        self.mobile_phone_number = val

    @property
    def address(self):
        return self.home_address

    @address.setter
    def address(self, val):
        self.home_address = val

    def sync_full_name(self):
        """Construct full_name from first_name, middle_name, and last_name."""
        parts = [p for p in [self.first_name, self.middle_name, self.last_name] if p]
        self.full_name = " ".join(parts) if parts else self.first_name

    def __repr__(self):
        return f'<Guardian {self.registration_number} - {self.full_name} [{self.status}]>'
