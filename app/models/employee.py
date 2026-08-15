from datetime import datetime
from app.models import db

class Employee(db.Model):
    __tablename__ = 'employees'

    id = db.Column(db.Integer, primary_key=True)
    institute_id = db.Column(db.Integer, db.ForeignKey('institutes.id'), nullable=True)
    registration_number = db.Column(db.String(50), unique=True, nullable=False) # e.g. "EMP001", "TCH001"
    
    # Name fields
    first_name = db.Column(db.String(50), nullable=False, default="Staff")
    middle_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    full_name = db.Column(db.String(150), nullable=False, default="Staff Member")

    # Role & Professional Details
    role = db.Column(db.String(50), nullable=False, default="Teacher") # e.g. Teacher, Staff, Admin
    department = db.Column(db.String(50), nullable=False, default="Academic") # Academic, Administration, Accounts, Library, IT, Transport, Support, Other
    designation = db.Column(db.String(100), nullable=False, default="Teacher") # e.g. "Senior Mathematics Teacher", "Principal", "Librarian"
    employment_type = db.Column(db.String(30), nullable=False, default="Full-time") # Full-time, Part-time, Contract, Temporary, Other
    is_teacher = db.Column(db.Boolean, default=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    date_of_joining = db.Column(db.Date, nullable=True)
    monthly_salary = db.Column(db.Numeric(10, 2), nullable=True)

    # Contact & Personal Information
    email_address = db.Column(db.String(120), nullable=True)
    mobile_phone_number = db.Column(db.String(20), nullable=True)
    alternate_phone = db.Column(db.String(20), nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    father_husband_name = db.Column(db.String(100), nullable=True)
    national_id = db.Column(db.String(50), nullable=True)
    educational_qualification = db.Column(db.String(100), nullable=True)
    religion = db.Column(db.String(50), nullable=True)
    blood_group = db.Column(db.String(10), nullable=True)

    # Location Address
    home_address = db.Column(db.Text, nullable=True)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)
    country = db.Column(db.String(100), nullable=True, default="India")
    postal_code = db.Column(db.String(20), nullable=True)

    # Media & Metadata
    profile_photo = db.Column(db.String(255), nullable=True) # Relative path to static uploaded avatar
    prior_experience_summary = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    salaries = db.relationship('Salary', backref='employee', lazy=True)
    homeworks = db.relationship('Homework', foreign_keys='Homework.teacher_id', lazy=True)
    timetables = db.relationship('Timetable', lazy=True)

    # Aliases for clean code access
    @property
    def employee_code(self):
        return self.registration_number

    @employee_code.setter
    def employee_code(self, val):
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

    @property
    def joining_date(self):
        return self.date_of_joining

    @joining_date.setter
    def joining_date(self, val):
        self.date_of_joining = val

    def sync_full_name(self):
        """Construct full_name from first_name, middle_name, and last_name."""
        parts = [p for p in [self.first_name, self.middle_name, self.last_name] if p]
        self.full_name = " ".join(parts) if parts else self.first_name

    def __repr__(self):
        return f'<Employee {self.registration_number} - {self.full_name} [{self.designation}]>'
