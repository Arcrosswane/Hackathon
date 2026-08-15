import uuid
from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, abort
from app.utils.decorators import login_required, role_required
from app.services.academic_service import get_active_academic_session
from app.services.class_service import get_classes_for_session
from app.services.student_service import get_all_students
from app.services.employee_service import get_teachers
from app.models import Student, Guardian, GuardianStudent, Employee, FeeInvoice, Receipt, Payment
from app.services.fee_service import (
    get_all_fee_types, create_fee_type, update_fee_type, toggle_fee_type_status,
    get_fee_structures, create_fee_structure, update_fee_structure, toggle_fee_structure_status,
    generate_student_invoice, generate_batch_class_invoices, get_invoices, delete_invoice,
    record_payment, get_payments, get_receipt_by_id,
    get_student_fee_summary, get_collection_summary,
    verify_parent_invoice_access, verify_parent_receipt_access, VALID_PAYMENT_METHODS
)


fees_bp = Blueprint('fees', __name__, url_prefix='/fees')


@fees_bp.route('/invoices/<int:invoice_id>/delete', methods=['POST'])
@login_required
@role_required('Admin')
def delete_invoice_route(invoice_id):
    """Delete a fee invoice and its attached records."""
    try:
        delete_invoice(invoice_id)
        flash("🗑️ Fee invoice deleted successfully!", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(request.referrer or url_for('fees.invoices_list'))


# ==========================================
# 1. ADMIN FEE TYPES MANAGEMENT
# ==========================================

@fees_bp.route('/types', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def manage_types():
    """Admin manager for fee types."""
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        try:
            create_fee_type(name, description)
            flash(f"Fee type '{name}' created successfully!", "success")
        except ValueError as e:
            flash(str(e), "danger")
        return redirect(url_for('fees.manage_types'))

    types_list = get_all_fee_types()
    return render_template('fees/types.html', fee_types=types_list)


@fees_bp.route('/types/<int:type_id>/edit', methods=['POST'])
@login_required
@role_required('Admin')
def edit_type(type_id):
    """Edit existing fee type."""
    name = request.form.get('name')
    description = request.form.get('description')
    is_active = bool(request.form.get('is_active'))
    try:
        update_fee_type(type_id, name, description, is_active)
        flash("Fee type updated successfully!", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for('fees.manage_types'))


@fees_bp.route('/types/<int:type_id>/toggle', methods=['POST'])
@login_required
@role_required('Admin')
def toggle_type(type_id):
    """Toggle fee type status."""
    try:
        toggle_fee_type_status(type_id)
        flash("Fee type status updated.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for('fees.manage_types'))


# ==========================================
# 2. FEE STRUCTURES MANAGEMENT
# ==========================================

@fees_bp.route('/structures')
@login_required
@role_required('Admin')
def structures_list():
    """Fee structures catalog."""
    act_sess = get_active_academic_session()
    sess_id = act_sess.id if act_sess else None
    
    structures = get_fee_structures(session_id=sess_id)
    return render_template('fees/structures_list.html', structures=structures, active_session=act_sess)


@fees_bp.route('/structures/create', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def create_structure():
    """Build a new fee structure with components."""
    act_sess = get_active_academic_session()
    sess_id = act_sess.id if act_sess else None

    if request.method == 'POST':
        class_id = request.form.get('class_id', type=int)
        name = request.form.get('name')
        description = request.form.get('description')

        fee_type_ids = request.form.getlist('fee_type_id[]')
        amounts = request.form.getlist('amount[]')
        frequencies = request.form.getlist('frequency[]')
        due_dates = request.form.getlist('due_date[]')

        components_data = []
        for i in range(len(fee_type_ids)):
            if fee_type_ids[i] and amounts[i]:
                try:
                    amt_f = float(amounts[i])
                    if amt_f > 0:
                        components_data.append({
                            'fee_type_id': int(fee_type_ids[i]),
                            'amount': amt_f,
                            'frequency': frequencies[i] if i < len(frequencies) else 'YEARLY',
                            'due_date': due_dates[i] if i < len(due_dates) and due_dates[i] else None
                        })
                except ValueError:
                    pass

        try:
            create_fee_structure(
                class_id=class_id,
                name=name,
                components_data=components_data,
                description=description,
                session_id=sess_id
            )
            flash(f"Fee structure '{name}' created successfully!", "success")
            return redirect(url_for('fees.structures_list'))
        except ValueError as e:
            flash(str(e), "danger")

    classes = get_classes_for_session(session_id=sess_id)
    fee_types = get_all_fee_types(active_only=True)
    return render_template('fees/structure_form.html', classes=classes, fee_types=fee_types, active_session=act_sess)


# ==========================================
# 3. FEE INVOICES & GENERATION
# ==========================================

@fees_bp.route('/invoices')
@login_required
@role_required('Admin')
def invoices_list():
    """Fee invoices roster with filters."""
    act_sess = get_active_academic_session()
    sess_id = act_sess.id if act_sess else None

    class_id = request.args.get('class_id', type=int)
    status = request.args.get('status')
    search_q = request.args.get('q')

    invoices = get_invoices(
        session_id=sess_id,
        class_id=class_id,
        status=status,
        search_query=search_q
    )
    classes = get_classes_for_session(session_id=sess_id)

    return render_template(
        'fees/invoices_list.html',
        invoices=invoices,
        classes=classes,
        selected_class_id=class_id,
        selected_status=status,
        search_query=search_q,
        active_session=act_sess
    )


@fees_bp.route('/invoices/generate', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def generate_invoices():
    """Generate fee invoices (single or batch)."""
    act_sess = get_active_academic_session()
    sess_id = act_sess.id if act_sess else None

    if request.method == 'POST':
        mode = request.form.get('gen_mode')  # 'BATCH' or 'SINGLE'
        due_d_str = request.form.get('due_date')

        if mode == 'BATCH':
            class_id = request.form.get('class_id', type=int)
            try:
                cnt = generate_batch_class_invoices(class_id=class_id, due_date=due_d_str, session_id=sess_id)
                flash(f"Successfully generated {cnt} fee invoices for class!", "success")
                return redirect(url_for('fees.invoices_list'))
            except ValueError as e:
                flash(str(e), "danger")
        else:
            student_id = request.form.get('student_id', type=int)
            disc_amt = request.form.get('discount_amount', 0.0, type=float)
            disc_reason = request.form.get('discount_reason')
            try:
                inv = generate_student_invoice(
                    student_id=student_id,
                    due_date=due_d_str,
                    discount_amount=disc_amt,
                    discount_reason=disc_reason,
                    session_id=sess_id
                )
                flash(f"Invoice {inv.invoice_number} generated successfully!", "success")
                return redirect(url_for('fees.invoices_list'))
            except ValueError as e:
                flash(str(e), "danger")

    classes = get_classes_for_session(session_id=sess_id)
    students = get_all_students()
    return render_template('fees/generate_invoices.html', classes=classes, students=students, active_session=act_sess)


def resolve_current_student_id():
    """Helper to resolve current logged in student's ID from session/user."""
    user_id = session.get('user_id')
    linked_id = session.get('linked_entity_id')
    if linked_id:
        return linked_id
    if user_id:
        from app.models import User
        u = User.query.get(user_id)
        if u and u.linked_entity_id:
            return u.linked_entity_id
        if u:
            s = Student.query.filter((Student.registration_number == u.username) | (Student.email_address == u.username)).first()
            if s:
                return s.id
    stu = Student.query.first()
    return stu.id if stu else 1

def resolve_current_guardian_id():
    """Helper to resolve current logged in parent/guardian's ID from session/user."""
    user_id = session.get('user_id')
    linked_id = session.get('linked_entity_id')
    if linked_id:
        return linked_id
    if user_id:
        from app.models import User
        u = User.query.get(user_id)
        if u and u.linked_entity_id:
            return u.linked_entity_id
        if u:
            g = Guardian.query.filter((Guardian.registration_number == u.username) | (Guardian.email_address == u.username)).first()
            if g:
                return g.id
    gdn = Guardian.query.first()
    return gdn.id if gdn else 1

@fees_bp.route('/invoices/<int:invoice_id>')
@login_required
def invoice_detail(invoice_id):
    """View invoice details."""
    inv = FeeInvoice.query.get_or_404(invoice_id)
    curr_role = str(session.get('user_role', '')).lower()

    if curr_role in ('parent', 'guardian'):
        guardian_id = resolve_current_guardian_id()
        if not verify_parent_invoice_access(guardian_id, inv.id):
            flash("Unauthorized access to invoice record.", "danger")
            return redirect(url_for('parent.dashboard'))
    elif curr_role == 'student':
        student_id = resolve_current_student_id()
        if inv.student_id != student_id:
            flash("Unauthorized access to invoice record.", "danger")
            return redirect(url_for('student.dashboard'))

    return render_template('fees/invoice_detail.html', invoice=inv)


# ==========================================
# 4. PAYMENTS & RECEIPT ISSUANCE
# ==========================================

@fees_bp.route('/payments')
@login_required
@role_required('Admin')
def payments_list():
    """Payment log & collection summary dashboard."""
    act_sess = get_active_academic_session()
    sess_id = act_sess.id if act_sess else None

    method = request.args.get('payment_method')
    payments = get_payments(session_id=sess_id, payment_method=method)
    collection_summary = get_collection_summary(session_id=sess_id)

    return render_template(
        'fees/payments_list.html',
        payments=payments,
        summary=collection_summary,
        selected_method=method,
        valid_methods=sorted(list(VALID_PAYMENT_METHODS)),
        active_session=act_sess
    )


@fees_bp.route('/payments/record', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def record_payment_route():
    """Record a manual cash/card/UPI payment against an invoice."""
    if request.method == 'POST':
        invoice_id = request.form.get('invoice_id', type=int)
        amount = request.form.get('amount')
        p_method = request.form.get('payment_method')
        tx_ref = request.form.get('transaction_reference')
        p_date = request.form.get('payment_date')
        notes = request.form.get('notes')

        emp_id = session.get('employee_id')

        try:
            pay = record_payment(
                invoice_id=invoice_id,
                amount=amount,
                payment_method=p_method,
                transaction_reference=tx_ref,
                payment_date=p_date,
                received_by_id=emp_id,
                notes=notes
            )
            flash(f"Payment of ₹{pay.amount:.2f} recorded successfully! Receipt #{pay.receipt.receipt_number} issued.", "success")
            return redirect(url_for('fees.receipt_view', receipt_id=pay.receipt.id))
        except ValueError as e:
            flash(str(e), "danger")

    inv_id = request.args.get('invoice_id', type=int)
    target_inv = FeeInvoice.query.get(inv_id) if inv_id else None
    
    act_sess = get_active_academic_session()
    sess_id = act_sess.id if act_sess else None
    open_invoices = [i for i in get_invoices(session_id=sess_id) if i.status in ('ISSUED', 'PARTIALLY_PAID')]

    return render_template(
        'fees/payment_form.html',
        target_invoice=target_inv,
        open_invoices=open_invoices,
        valid_methods=sorted(list(VALID_PAYMENT_METHODS)),
        today_date=date.today().strftime('%Y-%m-%d')
    )


@fees_bp.route('/pay/<int:invoice_id>', methods=['GET', 'POST'])
@login_required
def pay_invoice_online(invoice_id):
    """Self-service online fee payment portal for Students, Parents, or Admins."""
    inv = FeeInvoice.query.get_or_404(invoice_id)
    curr_role = str(session.get('user_role', '')).lower()

    if inv.status == 'PAID':
        flash("This fee invoice has already been fully paid.", "info")
        return redirect(url_for('fees.invoice_detail', invoice_id=inv.id))

    # IDOR Security Validation
    if curr_role in ('parent', 'guardian'):
        guardian_id = resolve_current_guardian_id()
        if not verify_parent_invoice_access(guardian_id, inv.id):
            flash("Unauthorized access to fee invoice.", "danger")
            return redirect(url_for('parent.dashboard'))
    elif curr_role == 'student':
        student_id = resolve_current_student_id()
        if inv.student_id != student_id:
            flash("Unauthorized access to fee invoice.", "danger")
            return redirect(url_for('student.dashboard'))

    if request.method == 'POST':
        amt = request.form.get('amount')
        p_method = request.form.get('payment_method', 'ONLINE')
        upi_id = request.form.get('upi_id', '').strip()
        
        tx_ref = f"GATEWAY/{p_method}/{uuid.uuid4().hex[:8].upper()}"
        if upi_id:
            tx_ref += f" ({upi_id})"

        try:
            pay = record_payment(
                invoice_id=inv.id,
                amount=amt,
                payment_method=p_method,
                transaction_reference=tx_ref,
                notes=f"Online Self-Service Fee Payment via {p_method}"
            )
            flash(f"🎉 Payment of ₹{pay.amount:.2f} completed successfully! Official Receipt #{pay.receipt.receipt_number} issued.", "success")
            return redirect(url_for('fees.receipt_view', receipt_id=pay.receipt.id))
        except ValueError as e:
            flash(str(e), "danger")

    return render_template('fees/pay_online.html', invoice=inv)


@fees_bp.route('/receipt/<int:receipt_id>')
@login_required
def receipt_view(receipt_id):
    """Official printable receipt document."""
    rec = get_receipt_by_id(receipt_id)
    if not rec:
        flash("Receipt record not found.", "danger")
        return redirect(url_for('admin.dashboard'))

    curr_role = str(session.get('user_role', '')).lower()
    if curr_role in ('parent', 'guardian'):
        guardian_id = resolve_current_guardian_id()
        if not verify_parent_receipt_access(guardian_id, rec.id):
            flash("Unauthorized access to receipt document.", "danger")
            return redirect(url_for('parent.dashboard'))
    elif curr_role == 'student':
        student_id = resolve_current_student_id()
        if rec.payment.student_id != student_id:
            flash("Unauthorized access to receipt document.", "danger")
            return redirect(url_for('student.dashboard'))

    return render_template('fees/receipt.html', receipt=rec)


# ==========================================
# 5. STUDENT & PARENT FEE ACCOUNTS
# ==========================================

@fees_bp.route('/my-account')
@login_required
def student_fee_account():
    """Fee ledger for logged in Student or Parent."""
    curr_role = str(session.get('user_role', '')).lower()
    student_id = None

    if curr_role == 'student':
        student_id = resolve_current_student_id()
    elif curr_role in ('parent', 'guardian'):
        guardian_id = resolve_current_guardian_id()
        if guardian_id:
            link = GuardianStudent.query.filter_by(guardian_id=guardian_id).first()
            if link:
                student_id = link.student_id

    if not student_id:
        flash("No linked student record found for fee account.", "warning")
        if curr_role in ('parent', 'guardian'):
            return redirect(url_for('parent.dashboard'))
        elif curr_role == 'student':
            return redirect(url_for('student.dashboard'))
        return redirect(url_for('admin.dashboard'))

    act_sess = get_active_academic_session()
    sess_id = act_sess.id if act_sess else None

    account_data = get_student_fee_summary(student_id, session_id=sess_id)
    return render_template('fees/student_fee_account.html', data=account_data, is_parent=(curr_role in ('parent', 'guardian')))


@fees_bp.route('/child/<int:student_id>')
@login_required
def child_fee_account(student_id):
    """Parent portal view for a specific linked child's fee account with IDOR protection."""
    curr_role = str(session.get('user_role', '')).lower()
    if curr_role not in ('parent', 'guardian', 'admin'):
        flash("Unauthorized access.", "danger")
        if curr_role == 'student':
            return redirect(url_for('student.dashboard'))
        return redirect(url_for('admin.dashboard'))

    if curr_role in ('parent', 'guardian'):
        guardian_id = resolve_current_guardian_id()
        link = GuardianStudent.query.filter_by(guardian_id=guardian_id, student_id=student_id).first()
        if not link:
            flash("Unauthorized access to student fee ledger.", "danger")
            return redirect(url_for('parent.dashboard'))

    act_sess = get_active_academic_session()
    sess_id = act_sess.id if act_sess else None

    account_data = get_student_fee_summary(student_id, session_id=sess_id)
    return render_template('fees/student_fee_account.html', data=account_data, is_parent=True)
