from datetime import datetime
from app.models import db

class FeeType(db.Model):
    __tablename__ = 'fee_types'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<FeeType {self.name}>'


class FeeStructure(db.Model):
    __tablename__ = 'fee_structures'

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=True)
    academic_session_id = db.Column(db.Integer, db.ForeignKey('academic_sessions.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    academic_session = db.relationship('AcademicSession', lazy=True)
    school_class = db.relationship('SchoolClass', lazy=True)
    components = db.relationship('FeeComponent', backref='structure', cascade='all, delete-orphan', lazy=True)

    def __repr__(self):
        return f'<FeeStructure {self.name} - Class #{self.class_id}>'


class FeeComponent(db.Model):
    __tablename__ = 'fee_components'

    id = db.Column(db.Integer, primary_key=True)
    fee_structure_id = db.Column(db.Integer, db.ForeignKey('fee_structures.id'), nullable=False)
    fee_type_id = db.Column(db.Integer, db.ForeignKey('fee_types.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    frequency = db.Column(db.String(30), default='YEARLY', nullable=False)  # 'ONE_TIME', 'MONTHLY', 'QUARTERLY', 'HALF_YEARLY', 'YEARLY'
    due_date = db.Column(db.Date, nullable=True)
    description = db.Column(db.String(255), nullable=True)

    # Relationships
    fee_type = db.relationship('FeeType', lazy=True)

    def __repr__(self):
        return f'<FeeComponent Type #{self.fee_type_id}: ₹{self.amount} ({self.frequency})>'


class StudentFeeAssignment(db.Model):
    __tablename__ = 'student_fee_assignments'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    fee_structure_id = db.Column(db.Integer, db.ForeignKey('fee_structures.id'), nullable=False)
    academic_session_id = db.Column(db.Integer, db.ForeignKey('academic_sessions.id'), nullable=False)
    discount_amount = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)
    discount_reason = db.Column(db.String(255), nullable=True)
    discount_approved_by_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    student = db.relationship('Student', lazy=True)
    fee_structure = db.relationship('FeeStructure', lazy=True)
    academic_session = db.relationship('AcademicSession', lazy=True)
    discount_approver = db.relationship('Employee', lazy=True)

    def __repr__(self):
        return f'<StudentFeeAssignment Student #{self.student_id} Structure #{self.fee_structure_id}>'


class FeeInvoice(db.Model):
    __tablename__ = 'fee_invoices'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    academic_session_id = db.Column(db.Integer, db.ForeignKey('academic_sessions.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)  # e.g., 'INV-2026-000123'
    issue_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    
    subtotal = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    discount = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    total_payable = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    paid_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    
    status = db.Column(db.String(30), default='ISSUED', nullable=False)  # 'DRAFT', 'ISSUED', 'PARTIALLY_PAID', 'PAID', 'CANCELLED'
    notes = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    student = db.relationship('Student', lazy=True)
    academic_session = db.relationship('AcademicSession', lazy=True)
    school_class = db.relationship('SchoolClass', lazy=True)
    items = db.relationship('FeeInvoiceItem', backref='invoice', cascade='all, delete-orphan', lazy=True)
    payments = db.relationship('Payment', backref='invoice', lazy=True)

    @property
    def outstanding_balance(self):
        """Calculate server-side remaining balance."""
        tot = float(self.total_payable or 0.0)
        pd = float(self.paid_amount or 0.0)
        return max(round(tot - pd, 2), 0.0)

    def __repr__(self):
        return f'<FeeInvoice #{self.invoice_number} Student #{self.student_id}: ₹{self.total_payable} [{self.status}]>'


class FeeInvoiceItem(db.Model):
    __tablename__ = 'fee_invoice_items'

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('fee_invoices.id'), nullable=False)
    fee_type_id = db.Column(db.Integer, db.ForeignKey('fee_types.id'), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)

    # Relationships
    fee_type = db.relationship('FeeType', lazy=True)

    def __repr__(self):
        return f'<FeeInvoiceItem {self.description}: ₹{self.amount}>'


class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    invoice_id = db.Column(db.Integer, db.ForeignKey('fee_invoices.id'), nullable=False)
    
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(db.String(30), default='CASH', nullable=False)  # 'CASH', 'CARD', 'BANK_TRANSFER', 'UPI', 'ONLINE', 'OTHER'
    transaction_reference = db.Column(db.String(100), nullable=True)  # UPI Ref / Cheque No / Bank Ref
    payment_date = db.Column(db.Date, nullable=False)
    received_by_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=True)
    
    status = db.Column(db.String(30), default='SUCCESS', nullable=False)  # 'SUCCESS', 'PENDING', 'FAILED', 'CANCELLED'
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    student = db.relationship('Student', lazy=True)
    received_by = db.relationship('Employee', lazy=True)
    receipt = db.relationship('Receipt', backref='payment', uselist=False, lazy=True)

    def __repr__(self):
        return f'<Payment #{self.id} Invoice #{self.invoice_id}: ₹{self.amount} ({self.payment_method})>'


class Receipt(db.Model):
    __tablename__ = 'receipts'

    id = db.Column(db.Integer, primary_key=True)
    payment_id = db.Column(db.Integer, db.ForeignKey('payments.id'), nullable=False, unique=True)
    receipt_number = db.Column(db.String(50), unique=True, nullable=False)  # e.g., 'REC-2026-000421'
    issued_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    generated_by_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=True)

    # Relationships
    generated_by = db.relationship('Employee', lazy=True)

    def __repr__(self):
        return f'<Receipt #{self.receipt_number} Payment #{self.payment_id}>'
