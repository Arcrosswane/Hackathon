from datetime import datetime
from app.models import db

class FinanceCategory(db.Model):
    __tablename__ = 'finance_categories'

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'INCOME' or 'EXPENSE'
    description = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    transactions = db.relationship('FinancialTransaction', backref='category', lazy=True)

    def __repr__(self):
        return f'<FinanceCategory {self.name} [{self.type}]>'


class FinancialTransaction(db.Model):
    __tablename__ = 'financial_transactions'

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=True)
    academic_session_id = db.Column(db.Integer, db.ForeignKey('academic_sessions.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('finance_categories.id'), nullable=False)
    
    transaction_type = db.Column(db.String(20), nullable=False)  # 'INCOME' or 'EXPENSE'
    transaction_number = db.Column(db.String(50), unique=True, nullable=False)  # e.g., 'TXN-2026-000123'
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    transaction_date = db.Column(db.Date, nullable=False)
    
    description = db.Column(db.Text, nullable=True)
    payment_method = db.Column(db.String(30), default='CASH', nullable=False)  # 'CASH', 'UPI', 'CARD', 'BANK_TRANSFER', 'CHEQUE', 'ONLINE', 'OTHER'
    reference_number = db.Column(db.String(100), nullable=True)  # Cheque #, UPI Ref, Invoice #
    vendor_or_payer = db.Column(db.String(150), nullable=True)  # Vendor name or Payer name
    
    source_type = db.Column(db.String(30), default='MANUAL', nullable=False)  # 'MANUAL', 'FEE_PAYMENT', 'FUTURE_STORE', 'FUTURE_PAYROLL', 'OTHER'
    source_id = db.Column(db.Integer, nullable=True)  # e.g., Payment.id
    
    status = db.Column(db.String(20), default='COMPLETED', nullable=False)  # 'COMPLETED', 'PENDING', 'CANCELLED'
    created_by_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=True)
    
    attachment_path = db.Column(db.String(255), nullable=True)
    original_filename = db.Column(db.String(255), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    school = db.relationship('School', lazy=True)
    academic_session = db.relationship('AcademicSession', lazy=True)
    created_by = db.relationship('Employee', lazy=True)

    def __repr__(self):
        return f'<FinancialTransaction #{self.transaction_number} [{self.transaction_type}]: ₹{self.amount} ({self.status})>'
