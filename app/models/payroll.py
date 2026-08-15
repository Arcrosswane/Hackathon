from datetime import datetime
from app.models import db

class SalaryComponent(db.Model):
    __tablename__ = 'salary_components'

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=True)
    name = db.Column(db.String(100), nullable=False) # e.g. "Basic Salary", "HRA", "Transport Allowance", "Professional Tax"
    type = db.Column(db.String(20), nullable=False) # 'EARNING' or 'DEDUCTION'
    calculation_type = db.Column(db.String(20), nullable=False, default='FIXED_AMOUNT') # 'FIXED_AMOUNT' or 'PERCENTAGE'
    default_value = db.Column(db.Numeric(12, 2), nullable=False, default=0.00) # Amount or Percentage rate
    percentage_of_component_id = db.Column(db.Integer, db.ForeignKey('salary_components.id'), nullable=True) # For percentage of Basic
    description = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<SalaryComponent {self.name} [{self.type} - {self.calculation_type}]>'


class SalaryStructure(db.Model):
    __tablename__ = 'salary_structures'

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=True)
    name = db.Column(db.String(150), nullable=False) # e.g. "Senior Academic Staff", "Support Staff"
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    items = db.relationship('SalaryStructureItem', backref='structure', cascade='all, delete-orphan', lazy=True)
    assignments = db.relationship('EmployeeSalaryAssignment', backref='structure', lazy=True)

    def __repr__(self):
        return f'<SalaryStructure {self.name}>'


class SalaryStructureItem(db.Model):
    __tablename__ = 'salary_structure_items'

    id = db.Column(db.Integer, primary_key=True)
    salary_structure_id = db.Column(db.Integer, db.ForeignKey('salary_structures.id'), nullable=False)
    component_id = db.Column(db.Integer, db.ForeignKey('salary_components.id'), nullable=False)
    calculation_type = db.Column(db.String(20), nullable=False, default='FIXED_AMOUNT') # 'FIXED_AMOUNT' or 'PERCENTAGE'
    amount_or_percentage = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)

    # Relationships
    component = db.relationship('SalaryComponent', lazy=True)

    def __repr__(self):
        return f'<SalaryStructureItem Structure #{self.salary_structure_id} Component #{self.component_id}: {self.amount_or_percentage}>'


class EmployeeSalaryAssignment(db.Model):
    __tablename__ = 'employee_salary_assignments'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    salary_structure_id = db.Column(db.Integer, db.ForeignKey('salary_structures.id'), nullable=False)
    effective_from = db.Column(db.Date, nullable=False)
    effective_until = db.Column(db.Date, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    employee = db.relationship('Employee', lazy=True)

    def __repr__(self):
        return f'<EmployeeSalaryAssignment Employee #{self.employee_id} Structure #{self.salary_structure_id}>'


class PayrollRecord(db.Model):
    __tablename__ = 'payroll_records'
    __table_args__ = (
        db.UniqueConstraint('employee_id', 'payroll_period', name='uq_employee_payroll_period'),
    )

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=True)
    academic_session_id = db.Column(db.Integer, db.ForeignKey('academic_sessions.id'), nullable=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    
    payroll_period = db.Column(db.String(20), nullable=False) # e.g. "2026-08"
    period_label = db.Column(db.String(50), nullable=False) # e.g. "August 2026"
    salary_structure_id = db.Column(db.Integer, db.ForeignKey('salary_structures.id'), nullable=True)
    
    gross_salary = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    total_deductions = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    net_salary = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    
    salary_slip_number = db.Column(db.String(50), unique=True, nullable=False) # e.g., 'PAY-2026-08-000123'
    status = db.Column(db.String(20), default='GENERATED', nullable=False) # 'DRAFT', 'GENERATED', 'APPROVED', 'PAID', 'CANCELLED'
    
    payment_method = db.Column(db.String(30), default='BANK_TRANSFER', nullable=False) # 'BANK_TRANSFER', 'CASH', 'UPI', 'CHEQUE', 'OTHER'
    payment_reference = db.Column(db.String(100), nullable=True) # Bank UTR / Cheque #
    notes = db.Column(db.Text, nullable=True)
    
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime, nullable=True)
    paid_at = db.Column(db.DateTime, nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=True)

    # Relationships
    employee = db.relationship('Employee', foreign_keys=[employee_id], lazy=True)
    created_by = db.relationship('Employee', foreign_keys=[created_by_id], lazy=True)
    salary_structure = db.relationship('SalaryStructure', lazy=True)
    items = db.relationship('PayrollItem', backref='payroll', cascade='all, delete-orphan', lazy=True)

    def __repr__(self):
        return f'<PayrollRecord #{self.salary_slip_number} Employee #{self.employee_id} [{self.payroll_period}]: ₹{self.net_salary} ({self.status})>'


class PayrollItem(db.Model):
    __tablename__ = 'payroll_items'

    id = db.Column(db.Integer, primary_key=True)
    payroll_id = db.Column(db.Integer, db.ForeignKey('payroll_records.id'), nullable=False)
    component_name = db.Column(db.String(100), nullable=False)
    component_type = db.Column(db.String(20), nullable=False) # 'EARNING' or 'DEDUCTION'
    calculation_type = db.Column(db.String(20), nullable=False, default='FIXED_AMOUNT')
    amount = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)

    def __repr__(self):
        return f'<PayrollItem {self.component_name} [{self.component_type}]: ₹{self.amount}>'
