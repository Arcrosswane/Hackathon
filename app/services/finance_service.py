import os
import uuid
from datetime import datetime, date, timedelta
from decimal import Decimal
from werkzeug.utils import secure_filename
from flask import current_app
from sqlalchemy import func, extract
from app.models import db, FinanceCategory, FinancialTransaction, Payment, Student, School
from app.services.academic_service import get_active_academic_session

ALLOWED_FINANCE_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'webp', 'doc', 'docx'}
VALID_PAYMENT_METHODS = {'CASH', 'UPI', 'CARD', 'BANK_TRANSFER', 'CHEQUE', 'ONLINE', 'OTHER'}
VALID_TRANSACTION_TYPES = {'INCOME', 'EXPENSE'}
VALID_TRANSACTION_STATUSES = {'COMPLETED', 'PENDING', 'CANCELLED'}

def is_allowed_finance_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_FINANCE_EXTENSIONS


def get_all_categories(school_id=None, category_type=None, active_only=False):
    """Retrieve financial categories with optional filtering by type and active status."""
    query = FinanceCategory.query
    if school_id:
        query = query.filter_by(school_id=school_id)
    if category_type:
        query = query.filter_by(type=category_type.upper())
    if active_only:
        query = query.filter_by(is_active=True)
    return query.order_by(FinanceCategory.name.asc()).all()


def create_category(name, category_type, description=None, school_id=None):
    """Create a new financial category (INCOME or EXPENSE)."""
    if not name or not name.strip():
        raise ValueError("Category name is required.")
    
    ctype = str(category_type).upper().strip()
    if ctype not in VALID_TRANSACTION_TYPES:
        raise ValueError(f"Invalid category type '{category_type}'. Must be 'INCOME' or 'EXPENSE'.")

    # Check for duplicate category name within same type
    existing = FinanceCategory.query.filter_by(name=name.strip(), type=ctype).first()
    if existing:
        if not existing.is_active:
            existing.is_active = True
            existing.description = description.strip() if description else existing.description
            db.session.commit()
            return existing
        raise ValueError(f"Financial category '{name}' ({ctype}) already exists.")

    cat = FinanceCategory(
        school_id=school_id,
        name=name.strip(),
        type=ctype,
        description=description.strip() if description else None,
        is_active=True
    )
    db.session.add(cat)
    db.session.commit()
    return cat


def update_category(category_id, name, description=None):
    """Update financial category details."""
    cat = FinanceCategory.query.get(category_id)
    if not cat:
        raise ValueError("Financial category not found.")
    
    if not name or not name.strip():
        raise ValueError("Category name is required.")

    cat.name = name.strip()
    cat.description = description.strip() if description else None
    db.session.commit()
    return cat


def toggle_category_status(category_id):
    """Toggle activation status of a category."""
    cat = FinanceCategory.query.get(category_id)
    if not cat:
        raise ValueError("Financial category not found.")
    cat.is_active = not cat.is_active
    db.session.commit()
    return cat


def generate_transaction_number():
    """Generate unique human-readable transaction identifier e.g., TXN-2026-A1B2C3."""
    year_str = datetime.now().year
    rand_hex = uuid.uuid4().hex[:6].upper()
    return f"TXN-{year_str}-{rand_hex}"


def save_finance_attachment(file):
    """
    Saves an uploaded supporting document safely.
    Returns dict: {'attachment_path': ..., 'original_filename': ...}
    """
    if not file or file.filename == '':
        return None

    if not is_allowed_finance_file(file.filename):
        raise ValueError(f"File type not allowed. Supported formats: {', '.join(sorted(ALLOWED_FINANCE_EXTENSIONS))}")

    filename = secure_filename(file.filename)
    unique_filename = f"fin_att_{uuid.uuid4().hex[:10]}_{filename}"

    upload_dir = os.path.join(current_app.static_folder, 'uploads', 'finance')
    os.makedirs(upload_dir, exist_ok=True)

    file_path = os.path.join(upload_dir, unique_filename)
    file.save(file_path)

    return {
        'attachment_path': f"uploads/finance/{unique_filename}",
        'original_filename': filename
    }


def create_manual_transaction(category_id, transaction_type, amount, transaction_date,
                              description=None, payment_method='CASH', reference_number=None,
                              vendor_or_payer=None, created_by_id=None, school_id=None,
                              session_id=None, file=None):
    """
    Records a manual income or expense financial transaction.
    """
    cat = FinanceCategory.query.get(category_id)
    if not cat:
        raise ValueError("Selected financial category not found.")

    ttype = str(transaction_type).upper().strip()
    if ttype not in VALID_TRANSACTION_TYPES:
        raise ValueError("Transaction type must be 'INCOME' or 'EXPENSE'.")

    if cat.type != ttype:
        raise ValueError(f"Category '{cat.name}' is an {cat.type} category and cannot be used for {ttype} transactions.")

    try:
        amt_val = round(Decimal(str(amount)), 2)
        if amt_val <= 0:
            raise ValueError("Amount must be a positive number greater than 0.")
    except Exception:
        raise ValueError("Invalid amount specified.")

    if not transaction_date:
        t_date = date.today()
    elif isinstance(transaction_date, date):
        t_date = transaction_date
    else:
        t_date = datetime.strptime(str(transaction_date), '%Y-%m-%d').date()

    pmeth = str(payment_method).upper().strip() if payment_method else 'CASH'
    if pmeth not in VALID_PAYMENT_METHODS:
        pmeth = 'OTHER'

    att_info = save_finance_attachment(file) if file else None

    txn = FinancialTransaction(
        school_id=school_id,
        academic_session_id=session_id,
        category_id=cat.id,
        transaction_type=ttype,
        transaction_number=generate_transaction_number(),
        amount=amt_val,
        transaction_date=t_date,
        description=description.strip() if description else None,
        payment_method=pmeth,
        reference_number=reference_number.strip() if reference_number else None,
        vendor_or_payer=vendor_or_payer.strip() if vendor_or_payer else None,
        source_type='MANUAL',
        status='COMPLETED',
        created_by_id=created_by_id,
        attachment_path=att_info['attachment_path'] if att_info else None,
        original_filename=att_info['original_filename'] if att_info else None
    )
    db.session.add(txn)
    db.session.commit()
    return txn


def sync_single_payment_to_finance(payment):
    """
    Syncs a single Module 11 student fee payment as a Financial Transaction income record.
    Guarantees duplicate income protection via (source_type='FEE_PAYMENT', source_id=payment.id).
    """
    if not payment:
        return None

    # Duplicate protection check
    existing = FinancialTransaction.query.filter_by(source_type='FEE_PAYMENT', source_id=payment.id).first()
    if existing:
        # Update status if fee payment was cancelled/refunded
        if payment.status in ('CANCELLED', 'FAILED') and existing.status != 'CANCELLED':
            existing.status = 'CANCELLED'
            db.session.commit()
        return existing

    # Find or provision "Student Fees" category
    cat = FinanceCategory.query.filter_by(name="Student Fees", type="INCOME").first()
    if not cat:
        cat = FinanceCategory(name="Student Fees", type="INCOME", description="Student tuition and academic fee collections", is_active=True)
        db.session.add(cat)
        db.session.flush()

    student_name = payment.student.full_name if payment.student else "Student"
    tx_num = f"TXN-FEE-{payment.id:06d}"

    sch = School.query.first()
    sch_id = sch.id if sch else None

    txn = FinancialTransaction(
        school_id=sch_id,
        academic_session_id=payment.invoice.academic_session_id if payment.invoice else None,
        category_id=cat.id,
        transaction_type='INCOME',
        transaction_number=tx_num,
        amount=round(Decimal(str(payment.amount)), 2),
        transaction_date=payment.payment_date,
        description=f"Fee Payment for Invoice #{payment.invoice.invoice_number if payment.invoice else 'N/A'}",
        payment_method=payment.payment_method if payment.payment_method in VALID_PAYMENT_METHODS else 'OTHER',
        reference_number=payment.transaction_reference or (f"Receipt #{payment.receipt.receipt_number}" if payment.receipt else None),
        vendor_or_payer=student_name,
        source_type='FEE_PAYMENT',
        source_id=payment.id,
        status='COMPLETED' if payment.status == 'SUCCESS' else 'CANCELLED',
        created_by_id=payment.received_by_id
    )
    db.session.add(txn)
    db.session.commit()
    return txn


def sync_all_fee_payments_to_finance(school_id=None, session_id=None):
    """
    Scans for any un-synced fee payment records in Module 11 and converts them into financial transactions.
    """
    payments = Payment.query.filter_by(status='SUCCESS').all()
    synced_count = 0
    for p in payments:
        existing = FinancialTransaction.query.filter_by(source_type='FEE_PAYMENT', source_id=p.id).first()
        if not existing:
            sync_single_payment_to_finance(p)
            synced_count += 1
    return synced_count


def get_financial_transactions(session_id=None, category_id=None, transaction_type=None,
                                payment_method=None, status=None, date_preset=None,
                                start_date=None, end_date=None, search_query=None):
    """
    Filterable transaction query builder.
    """
    # Ensure fee payments are synced
    sync_all_fee_payments_to_finance(session_id=session_id)

    query = FinancialTransaction.query

    if session_id:
        query = query.filter((FinancialTransaction.academic_session_id == session_id) | (FinancialTransaction.academic_session_id.is_(None)))

    if transaction_type and transaction_type.upper() in VALID_TRANSACTION_TYPES:
        query = query.filter_by(transaction_type=transaction_type.upper())

    if category_id:
        query = query.filter_by(category_id=category_id)

    if payment_method:
        query = query.filter_by(payment_method=payment_method.upper())

    if status:
        query = query.filter_by(status=status.upper())

    # Date Presets Filtering
    today = date.today()
    if date_preset == 'today':
        query = query.filter(FinancialTransaction.transaction_date == today)
    elif date_preset == 'this_week':
        start_w = today - timedelta(days=today.weekday())
        query = query.filter(FinancialTransaction.transaction_date >= start_w)
    elif date_preset == 'this_month':
        start_m = date(today.year, today.month, 1)
        query = query.filter(FinancialTransaction.transaction_date >= start_m)
    elif date_preset == 'this_year':
        start_y = date(today.year, 1, 1)
        query = query.filter(FinancialTransaction.transaction_date >= start_y)
    elif start_date or end_date:
        if start_date:
            d_start = start_date if isinstance(start_date, date) else datetime.strptime(str(start_date), '%Y-%m-%d').date()
            query = query.filter(FinancialTransaction.transaction_date >= d_start)
        if end_date:
            d_end = end_date if isinstance(end_date, date) else datetime.strptime(str(end_date), '%Y-%m-%d').date()
            query = query.filter(FinancialTransaction.transaction_date <= d_end)

    if search_query and search_query.strip():
        sq = f"%{search_query.strip()}%"
        query = query.filter(
            (FinancialTransaction.transaction_number.ilike(sq)) |
            (FinancialTransaction.description.ilike(sq)) |
            (FinancialTransaction.vendor_or_payer.ilike(sq)) |
            (FinancialTransaction.reference_number.ilike(sq))
        )

    return query.order_by(FinancialTransaction.transaction_date.desc(), FinancialTransaction.id.desc()).all()


def get_finance_dashboard_summary(school_id=None, session_id=None):
    """
    Calculates authoritative financial metrics server-side using SQL aggregations.
    """
    sync_all_fee_payments_to_finance(session_id=session_id)

    today = date.today()
    month_start = date(today.year, today.month, 1)

    # Base completed transactions query
    base_query = db.session.query(
        FinancialTransaction.transaction_type,
        func.coalesce(func.sum(FinancialTransaction.amount), 0).label('total_amount')
    ).filter(FinancialTransaction.status == 'COMPLETED')

    if session_id:
        base_query = base_query.filter((FinancialTransaction.academic_session_id == session_id) | (FinancialTransaction.academic_session_id.is_(None)))

    # Overall Totals
    overall_rows = base_query.group_by(FinancialTransaction.transaction_type).all()
    totals_map = {row.transaction_type: float(row.total_amount) for row in overall_rows}
    
    total_income = totals_map.get('INCOME', 0.0)
    total_expenses = totals_map.get('EXPENSE', 0.0)
    net_balance = round(total_income - total_expenses, 2)

    # Today's Totals
    today_rows = base_query.filter(FinancialTransaction.transaction_date == today).group_by(FinancialTransaction.transaction_type).all()
    today_map = {row.transaction_type: float(row.total_amount) for row in today_rows}
    today_income = today_map.get('INCOME', 0.0)
    today_expenses = today_map.get('EXPENSE', 0.0)

    # Current Month Totals
    month_rows = base_query.filter(FinancialTransaction.transaction_date >= month_start).group_by(FinancialTransaction.transaction_type).all()
    month_map = {row.transaction_type: float(row.total_amount) for row in month_rows}
    month_income = month_map.get('INCOME', 0.0)
    month_expenses = month_map.get('EXPENSE', 0.0)

    # Income by Category
    inc_cat_query = db.session.query(
        FinanceCategory.name,
        func.coalesce(func.sum(FinancialTransaction.amount), 0).label('amount')
    ).join(FinancialTransaction, FinancialTransaction.category_id == FinanceCategory.id)\
     .filter(FinancialTransaction.transaction_type == 'INCOME', FinancialTransaction.status == 'COMPLETED')
    
    if session_id:
        inc_cat_query = inc_cat_query.filter((FinancialTransaction.academic_session_id == session_id) | (FinancialTransaction.academic_session_id.is_(None)))
    income_by_category = [{'category': r[0], 'amount': float(r[1])} for r in inc_cat_query.group_by(FinanceCategory.name).all()]

    # Expenses by Category
    exp_cat_query = db.session.query(
        FinanceCategory.name,
        func.coalesce(func.sum(FinancialTransaction.amount), 0).label('amount')
    ).join(FinancialTransaction, FinancialTransaction.category_id == FinanceCategory.id)\
     .filter(FinancialTransaction.transaction_type == 'EXPENSE', FinancialTransaction.status == 'COMPLETED')
    
    if session_id:
        exp_cat_query = exp_cat_query.filter((FinancialTransaction.academic_session_id == session_id) | (FinancialTransaction.academic_session_id.is_(None)))
    expenses_by_category = [{'category': r[0], 'amount': float(r[1])} for r in exp_cat_query.group_by(FinanceCategory.name).all()]

    # Recent Transactions (Last 10)
    recent_txns = FinancialTransaction.query.order_by(FinancialTransaction.transaction_date.desc(), FinancialTransaction.id.desc()).limit(10).all()

    return {
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_balance': net_balance,
        'today_income': today_income,
        'today_expenses': today_expenses,
        'month_income': month_income,
        'month_expenses': month_expenses,
        'income_by_category': income_by_category,
        'expenses_by_category': expenses_by_category,
        'recent_transactions': recent_txns
    }


def cancel_transaction(transaction_id):
    """Voids/cancels a transaction, excluding it from balance calculations."""
    txn = FinancialTransaction.query.get(transaction_id)
    if not txn:
        raise ValueError("Financial transaction not found.")
    txn.status = 'CANCELLED'
    db.session.commit()
    return txn
