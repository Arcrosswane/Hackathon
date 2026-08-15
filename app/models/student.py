from datetime import datetime
from app.models import db

class Student(db.Model):
    __tablename__ = 'students'

    id = db.Column(db.Integer, primary_key=True)
    institute_id = db.Column(db.Integer, db.ForeignKey('institutes.id'), nullable=True)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=True) # Legacy direct reference
    registration_number = db.Column(db.String(50), unique=True, nullable=False) # Admission Number (e.g. "ADM001", "STU-2026-001")
    
    # Name fields
    first_name = db.Column(db.String(50), nullable=False, default="Student")
    middle_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    full_name = db.Column(db.String(150), nullable=False, default="Student Name")

    # Personal Details
    gender = db.Column(db.String(20), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    admission_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(30), nullable=False, default="Active") # Active, Inactive, Graduated, Transferred, Withdrawn
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Contact Info
    email_address = db.Column(db.String(120), nullable=True)
    mobile_phone_number = db.Column(db.String(20), nullable=True)
    
    # Address
    home_address = db.Column(db.Text, nullable=True)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)
    country = db.Column(db.String(100), nullable=True, default="India")
    postal_code = db.Column(db.String(20), nullable=True)

    # Guardian / Parent Information
    guardian_name = db.Column(db.String(100), nullable=True)
    guardian_relation = db.Column(db.String(50), nullable=True) # Father, Mother, Guardian, Other
    guardian_phone = db.Column(db.String(20), nullable=True)
    guardian_email = db.Column(db.String(120), nullable=True)
    guardian_occupation = db.Column(db.String(100), nullable=True)

    # Media & Metadata
    profile_photo = db.Column(db.String(255), nullable=True) # Relative path to static avatar
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    fees = db.relationship('Fee', backref='student', lazy=True)
    enrollments = db.relationship('StudentEnrollment', backref='student', lazy=True, cascade='all, delete-orphan')

    # Property Aliases
    @property
    def admission_number(self):
        return self.registration_number

    @admission_number.setter
    def admission_number(self, val):
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

    def get_current_enrollment(self):
        """Returns the student's currently active enrollment record."""
        for en in self.enrollments:
            if en.is_current:
                return en
        return self.enrollments[0] if self.enrollments else None

    def __repr__(self):
        return f'<Student {self.registration_number} - {self.full_name} [{self.status}]>'
