import uuid
from datetime import datetime, date
from flask import current_app
from app.models import (
    db, FeeType, FeeStructure, FeeComponent, StudentFeeAssignment,
    FeeInvoice, FeeInvoiceItem, Payment, Receipt,
    Student, StudentEnrollment, Employee, SchoolClass, Section, AcademicSession, GuardianStudent
)
from app.services.academic_service import get_active_academic_session

# ==========================================
# 1. FEE TYPE MANAGEMENT
# ==========================================

def get_all_fee_types(active_only=False):
    """Retrieve all fee types."""
    query = FeeType.query
    if active_only:
        query = query.filter_by(is_active=True)
    return query.order_by(FeeType.name.asc()).all()

def create_fee_type(name, description=None):
    """Create a new fee type."""
    if not name or not name.strip():
        raise ValueError("Fee type name is required.")

    clean_name = name.strip()
    existing = FeeType.query.filter(db.func.lower(FeeType.name) == clean_name.lower()).first()
    if existing:
        raise ValueError(f"Fee type '{clean_name}' already exists.")

    ft = FeeType(
        name=clean_name,
        description=description.strip() if description else None,
        is_active=True
    )
    db.session.add(ft)
    db.session.commit()
    return ft

def update_fee_type(type_id, name, description=None, is_active=True):
    """Update an existing fee type."""
    ft = FeeType.query.get(type_id)
    if not ft:
        raise ValueError("Fee type not found.")

    if not name or not name.strip():
        raise ValueError("Fee type name is required.")

    clean_name = name.strip()
    existing = FeeType.query.filter(
        db.func.lower(FeeType.name) == clean_name.lower(),
        FeeType.id != ft.id
    ).first()
    if existing:
        raise ValueError(f"Another fee type with name '{clean_name}' already exists.")

    ft.name = clean_name
    ft.description = description.strip() if description else None
    ft.is_active = is_active
    db.session.commit()
    return ft

def toggle_fee_type_status(type_id):
    """Toggle active/archive status of a fee type."""
    ft = FeeType.query.get(type_id)
    if not ft:
        raise ValueError("Fee type not found.")
    ft.is_active = not ft.is_active
    db.session.commit()
    return ft


# ==========================================
# 2. FEE STRUCTURE & COMPONENTS MANAGEMENT
# ==========================================

def get_fee_structures(session_id=None, class_id=None, active_only=False):
    """Query fee structures with filters."""
    if not session_id:
        act_sess = get_active_academic_session()
        session_id = act_sess.id if act_sess else None

    query = FeeStructure.query
    if session_id:
        query = query.filter_by(academic_session_id=session_id)
    if class_id:
        query = query.filter_by(class_id=class_id)
    if active_only:
        query = query.filter_by(is_active=True)

    return query.order_by(FeeStructure.created_at.desc()).all()

def create_fee_structure(class_id, name, components_data, description=None, session_id=None):
    """
    Creates a new fee structure with line components for a class and session.
    components_data format: [{'fee_type_id': 1, 'amount': 12000.0, 'frequency': 'YEARLY', 'due_date': '2026-09-01'}]
    """
    target_class = SchoolClass.query.get(class_id)
    if not target_class:
        raise ValueError("Selected class not found.")

    if not name or not name.strip():
        raise ValueError("Fee structure name is required.")

    if not session_id:
        act_sess = get_active_academic_session()
        if not act_sess:
            raise ValueError("No active academic session found.")
        session_id = act_sess.id

    fs = FeeStructure(
        academic_session_id=session_id,
        class_id=class_id,
        name=name.strip(),
        description=description.strip() if description else None,
        is_active=True
    )
    db.session.add(fs)
    db.session.flush()

    if components_data:
        for comp in components_data:
            ft_id = comp.get('fee_type_id')
            amt = float(comp.get('amount') or 0.0)
            freq = comp.get('frequency', 'YEARLY')
            d_date = comp.get('due_date')
            d_obj = datetime.strptime(str(d_date), '%Y-%m-%d').date() if d_date else None

            if ft_id and amt > 0:
                fc = FeeComponent(
                    fee_structure_id=fs.id,
                    fee_type_id=ft_id,
                    amount=amt,
                    frequency=freq,
                    due_date=d_obj,
                    description=comp.get('description')
                )
                db.session.add(fc)

    db.session.commit()
    return fs

def update_fee_structure(structure_id, name, components_data=None, description=None, is_active=True):
    """Update a fee structure and its components."""
    fs = FeeStructure.query.get(structure_id)
    if not fs:
        raise ValueError("Fee structure not found.")

    if not name or not name.strip():
        raise ValueError("Fee structure name is required.")

    fs.name = name.strip()
    fs.description = description.strip() if description else None
    fs.is_active = is_active

    if components_data is not None:
        FeeComponent.query.filter_by(fee_structure_id=fs.id).delete()
        for comp in components_data:
            ft_id = comp.get('fee_type_id')
            amt = float(comp.get('amount') or 0.0)
            freq = comp.get('frequency', 'YEARLY')
            d_date = comp.get('due_date')
            d_obj = datetime.strptime(str(d_date), '%Y-%m-%d').date() if d_date else None

            if ft_id and amt > 0:
                fc = FeeComponent(
                    fee_structure_id=fs.id,
                    fee_type_id=ft_id,
                    amount=amt,
                    frequency=freq,
                    due_date=d_obj,
                    description=comp.get('description')
                )
                db.session.add(fc)

    db.session.commit()
    return fs

def toggle_fee_structure_status(structure_id):
    """Toggle active status of a fee structure."""
    fs = FeeStructure.query.get(structure_id)
    if not fs:
        raise ValueError("Fee structure not found.")
    fs.is_active = not fs.is_active
    db.session.commit()
    return fs


# ==========================================
# 3. STUDENT FEE INVOICES & GENERATION
# ==========================================

def generate_invoice_number():
    """Generate unique human-readable invoice identifier e.g., INV-2026-000123."""
    year_str = datetime.now().year
    rand_hex = uuid.uuid4().hex[:6].upper()
    return f"INV-{year_str}-{rand_hex}"

def generate_receipt_number():
    """Generate unique human-readable receipt identifier e.g., REC-2026-000421."""
    year_str = datetime.now().year
    rand_hex = uuid.uuid4().hex[:6].upper()
    return f"REC-{year_str}-{rand_hex}"

def generate_student_invoice(student_id, fee_structure_id=None, due_date=None,
                             discount_amount=0.0, discount_reason=None,
                             discount_approved_by_id=None, session_id=None):
    """
    Generates a student fee invoice with preserved line items and server-side calculated totals.
    """
    student = Student.query.get(student_id)
    if not student:
        raise ValueError("Student record not found.")

    if not session_id:
        act_sess = get_active_academic_session()
        if not act_sess:
            raise ValueError("No active academic session found.")
        session_id = act_sess.id

    enrollment = StudentEnrollment.query.filter_by(student_id=student_id, academic_session_id=session_id, is_current=True).first()
    if not enrollment:
        enrollment = StudentEnrollment.query.filter_by(student_id=student_id).first()

    class_id = enrollment.class_id if enrollment else student.class_id
    if not class_id:
        raise ValueError("Student has no class placement.")

    # Resolve fee structure if not explicitly provided
    if not fee_structure_id:
        fs = FeeStructure.query.filter_by(academic_session_id=session_id, class_id=class_id, is_active=True).first()
        if not fs:
            fs = FeeStructure.query.filter_by(class_id=class_id, is_active=True).first()
        if not fs:
            raise ValueError(f"No active fee structure found for student's class.")
        fee_structure_id = fs.id
    else:
        fs = FeeStructure.query.get(fee_structure_id)
        if not fs:
            raise ValueError("Selected fee structure not found.")

    if not fs.components or len(fs.components) == 0:
        raise ValueError(f"Fee structure '{fs.name}' has no fee components configured.")

    subtotal = sum(float(c.amount) for c in fs.components)
    disc_val = max(float(discount_amount or 0.0), 0.0)
    disc_val = min(disc_val, subtotal)  # Prevent discount exceeding subtotal
    payable = max(round(subtotal - disc_val, 2), 0.0)

    issue_d = date.today()
    if not due_date:
        due_d = date(issue_d.year, issue_d.month + 1, 15) if issue_d.month < 12 else date(issue_d.year + 1, 1, 15)
    else:
        due_d = due_date if isinstance(due_date, date) else datetime.strptime(str(due_date), '%Y-%m-%d').date()

    inv = FeeInvoice(
        student_id=student_id,
        academic_session_id=session_id,
        class_id=class_id,
        invoice_number=generate_invoice_number(),
        issue_date=issue_d,
        due_date=due_d,
        subtotal=subtotal,
        discount=disc_val,
        total_payable=payable,
        paid_amount=0.00,
        status='ISSUED',
        notes=f"Fee Demand for {fs.name}. Discount: {discount_reason or 'None'}"
    )
    db.session.add(inv)
    db.session.flush()

    # Create immutable invoice line items
    for comp in fs.components:
        item = FeeInvoiceItem(
            invoice_id=inv.id,
            fee_type_id=comp.fee_type_id,
            description=f"{comp.fee_type.name} ({comp.frequency})",
            amount=comp.amount
        )
        db.session.add(item)

    # Record student fee assignment metadata
    assign = StudentFeeAssignment.query.filter_by(student_id=student_id, fee_structure_id=fs.id, academic_session_id=session_id).first()
    if not assign:
        assign = StudentFeeAssignment(
            student_id=student_id,
            fee_structure_id=fs.id,
            academic_session_id=session_id,
            discount_amount=disc_val,
            discount_reason=discount_reason.strip() if discount_reason else None,
            discount_approved_by_id=discount_approved_by_id,
            is_active=True
        )
        db.session.add(assign)

    db.session.commit()
    return inv

def generate_batch_class_invoices(class_id, due_date=None, session_id=None):
    """
    Generates fee invoices for all currently enrolled students in a class.
    """
    if not session_id:
        act_sess = get_active_academic_session()
        if not act_sess:
            raise ValueError("No active academic session found.")
        session_id = act_sess.id

    enrollments = StudentEnrollment.query.filter_by(
        academic_session_id=session_id,
        class_id=class_id,
        is_current=True
    ).all()

    if not enrollments:
        raise ValueError("No active students enrolled in selected class.")

    fs = FeeStructure.query.filter_by(academic_session_id=session_id, class_id=class_id, is_active=True).first()
    if not fs:
        raise ValueError("No active fee structure found for selected class.")

    gen_count = 0
    for en in enrollments:
        try:
            generate_student_invoice(
                student_id=en.student_id,
                fee_structure_id=fs.id,
                due_date=due_date,
                session_id=session_id
            )
            gen_count += 1
        except Exception:
            pass

    return gen_count

def get_invoices(session_id=None, class_id=None, student_id=None, status=None, search_query=None):
    """Query fee invoices with filters."""
    query = FeeInvoice.query

    if session_id:
        query = query.filter_by(academic_session_id=session_id)
    if class_id:
        query = query.filter_by(class_id=class_id)
    if student_id:
        query = query.filter_by(student_id=student_id)
    if status:
        query = query.filter_by(status=status.upper())

    if search_query:
        sq = f"%{search_query.strip()}%"
        query = query.filter((FeeInvoice.invoice_number.ilike(sq)) | (FeeInvoice.notes.ilike(sq)))

    return query.order_by(FeeInvoice.issue_date.desc(), FeeInvoice.created_at.desc()).all()


# ==========================================
# 4. PAYMENTS & RECEIPT ISSUANCE
# ==========================================

VALID_PAYMENT_METHODS = {'CASH', 'CARD', 'BANK_TRANSFER', 'UPI', 'ONLINE', 'OTHER'}

def record_payment(invoice_id, amount, payment_method='CASH', transaction_reference=None,
                   payment_date=None, received_by_id=None, notes=None):
    """
    Records a payment against a fee invoice with server-side overpayment validation and receipt generation.
    """
    inv = FeeInvoice.query.get(invoice_id)
    if not inv:
        raise ValueError("Fee invoice record not found.")

    if inv.status in ('PAID', 'CANCELLED'):
        raise ValueError(f"Cannot record payment for an invoice with status '{inv.status}'.")

    try:
        amt_val = float(amount)
    except (ValueError, TypeError):
        raise ValueError("Payment amount must be a valid positive number.")

    if amt_val <= 0:
        raise ValueError("Payment amount must be greater than zero.")

    # Overpayment check
    rem_balance = inv.outstanding_balance
    if amt_val > rem_balance + 0.01:
        raise ValueError(f"Payment amount (₹{amt_val:.2f}) exceeds outstanding invoice balance (₹{rem_balance:.2f}). Overpayment is not allowed.")

    pm = payment_method.upper() if payment_method else 'CASH'
    if pm not in VALID_PAYMENT_METHODS:
        raise ValueError(f"Invalid payment method. Supported methods: {', '.join(sorted(VALID_PAYMENT_METHODS))}")

    p_date = payment_date if isinstance(payment_date, date) else datetime.strptime(str(payment_date), '%Y-%m-%d').date() if payment_date else date.today()

    payment = Payment(
        student_id=inv.student_id,
        invoice_id=inv.id,
        amount=amt_val,
        payment_method=pm,
        transaction_reference=transaction_reference.strip() if transaction_reference else None,
        payment_date=p_date,
        received_by_id=received_by_id,
        status='SUCCESS',
        notes=notes.strip() if notes else None
    )
    db.session.add(payment)
    db.session.flush()

    # Update invoice paid total and status
    new_paid = float(inv.paid_amount or 0.0) + amt_val
    inv.paid_amount = round(new_paid, 2)

    if inv.paid_amount >= float(inv.total_payable):
        inv.status = 'PAID'
    else:
        inv.status = 'PARTIALLY_PAID'

    # Issue unique receipt
    rec = Receipt(
        payment_id=payment.id,
        receipt_number=generate_receipt_number(),
        issued_at=datetime.utcnow(),
        generated_by_id=received_by_id
    )
    db.session.add(rec)

    db.session.commit()
    return payment

def get_payments(session_id=None, student_id=None, invoice_id=None, payment_method=None):
    """Query payments with filters."""
    query = Payment.query

    if student_id:
        query = query.filter_by(student_id=student_id)
    if invoice_id:
        query = query.filter_by(invoice_id=invoice_id)
    if payment_method:
        query = query.filter_by(payment_method=payment_method.upper())

    if session_id:
        query = query.join(FeeInvoice).filter(FeeInvoice.academic_session_id == session_id)

    return query.order_by(Payment.payment_date.desc(), Payment.created_at.desc()).all()

def get_receipt_by_id(receipt_id):
    """Retrieve receipt details by ID."""
    return Receipt.query.get(receipt_id)


# ==========================================
# 5. STUDENT LEDGER & COLLECTION ANALYTICS
# ==========================================

def get_student_fee_summary(student_id, session_id=None):
    """
    Calculates complete student fee account ledger (assigned, subtotal, discount, payable, paid, outstanding, overdue).
    """
    student = Student.query.get(student_id)
    if not student:
        raise ValueError("Student record not found.")

    if not session_id:
        act_sess = get_active_academic_session()
        session_id = act_sess.id if act_sess else None

    invoices = get_invoices(session_id=session_id, student_id=student.id)
    payments = get_payments(session_id=session_id, student_id=student.id)

    tot_subtotal = sum(float(i.subtotal) for i in invoices)
    tot_discount = sum(float(i.discount) for i in invoices)
    tot_payable = sum(float(i.total_payable) for i in invoices)
    tot_paid = sum(float(i.paid_amount) for i in invoices)
    tot_outstanding = max(round(tot_payable - tot_paid, 2), 0.0)

    today_curr = date.today()
    overdue_invoices = [i for i in invoices if i.due_date and i.due_date < today_curr and i.status != 'PAID']
    tot_overdue = sum(i.outstanding_balance for i in overdue_invoices)

    return {
        'student': student,
        'summary': {
            'total_subtotal': tot_subtotal,
            'total_discount': tot_discount,
            'total_payable': tot_payable,
            'total_paid': tot_paid,
            'total_outstanding': tot_outstanding,
            'total_overdue': tot_overdue,
            'overdue_count': len(overdue_invoices)
        },
        'invoices': invoices,
        'payments': payments
    }

def get_collection_summary(session_id=None):
    """
    Generates school-wide fee collection summary metrics for admin/finance staff.
    """
    if not session_id:
        act_sess = get_active_academic_session()
        session_id = act_sess.id if act_sess else None

    invoices = get_invoices(session_id=session_id)
    payments = get_payments(session_id=session_id)

    tot_billed = sum(float(i.total_payable) for i in invoices)
    tot_collected = sum(float(p.amount) for p in payments if p.status == 'SUCCESS')
    tot_outstanding = max(round(tot_billed - tot_collected, 2), 0.0)

    today_curr = date.today()
    overdue_invoices = [i for i in invoices if i.due_date and i.due_date < today_curr and i.status != 'PAID']
    tot_overdue = sum(i.outstanding_balance for i in overdue_invoices)

    paid_count = sum(1 for i in invoices if i.status == 'PAID')
    partial_count = sum(1 for i in invoices if i.status == 'PARTIALLY_PAID')
    unpaid_count = sum(1 for i in invoices if i.status in ('ISSUED', 'DRAFT'))

    # Daily collection summary for recent 7 days
    today_p = sum(float(p.amount) for p in payments if p.payment_date == today_curr and p.status == 'SUCCESS')

    return {
        'total_billed': tot_billed,
        'total_collected': tot_collected,
        'total_outstanding': tot_outstanding,
        'total_overdue': tot_overdue,
        'total_invoices_count': len(invoices),
        'paid_count': paid_count,
        'partially_paid_count': partial_count,
        'unpaid_count': unpaid_count,
        'today_collection': today_p,
        'recent_payments': payments[:10]
    }


# ==========================================
# 6. AUTHORIZATION HELPERS
# ==========================================

def verify_parent_invoice_access(guardian_id, invoice_id):
    """Verifies server-side if parent is linked to student owning the invoice."""
    if not guardian_id or not invoice_id:
        return False
    inv = FeeInvoice.query.get(invoice_id)
    if not inv:
        return False
    link = GuardianStudent.query.filter_by(guardian_id=guardian_id, student_id=inv.student_id).first()
    return bool(link)

def verify_parent_receipt_access(guardian_id, receipt_id):
    """Verifies server-side if parent is linked to student owning the receipt."""
    if not guardian_id or not receipt_id:
        return False
    rec = Receipt.query.get(receipt_id)
    if not rec or not rec.payment:
        return False
    link = GuardianStudent.query.filter_by(guardian_id=guardian_id, student_id=rec.payment.student_id).first()
    return bool(link)
