import io
import csv
from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_from_directory, Response, current_app
from app.utils.decorators import login_required, role_required
from app.services.academic_service import get_active_academic_session
from app.services.finance_service import (
    get_all_categories, create_category, update_category, toggle_category_status,
    create_manual_transaction, get_financial_transactions, get_finance_dashboard_summary,
    cancel_transaction, VALID_PAYMENT_METHODS, VALID_TRANSACTION_TYPES
)
from app.models import FinancialTransaction, FinanceCategory

accounts_bp = Blueprint('accounts', __name__, url_prefix='/accounts')

@accounts_bp.route('/dashboard')
@login_required
@role_required('Admin')
def dashboard():
    """Accounts & Finance overview dashboard."""
    act_sess = get_active_academic_session()
    sess_id = act_sess.id if act_sess else None

    summary = get_finance_dashboard_summary(session_id=sess_id)
    return render_template('accounts/dashboard.html', summary=summary, active_session=act_sess)


@accounts_bp.route('/transactions')
@login_required
@role_required('Admin')
def transactions_list():
    """Filterable transaction ledger."""
    act_sess = get_active_academic_session()
    sess_id = act_sess.id if act_sess else None

    t_type = request.args.get('type')
    cat_id = request.args.get('category_id', type=int)
    method = request.args.get('payment_method')
    status = request.args.get('status')
    date_preset = request.args.get('date_preset')
    start_d = request.args.get('start_date')
    end_d = request.args.get('end_date')
    search_q = request.args.get('q')

    transactions = get_financial_transactions(
        session_id=sess_id,
        category_id=cat_id,
        transaction_type=t_type,
        payment_method=method,
        status=status,
        date_preset=date_preset,
        start_date=start_d,
        end_date=end_d,
        search_query=search_q
    )

    categories = get_all_categories(active_only=False)

    return render_template(
        'accounts/transactions_list.html',
        transactions=transactions,
        categories=categories,
        valid_methods=sorted(list(VALID_PAYMENT_METHODS)),
        selected_type=t_type,
        selected_cat_id=cat_id,
        selected_method=method,
        selected_status=status,
        selected_preset=date_preset,
        start_date=start_d,
        end_date=end_d,
        search_query=search_q,
        active_session=act_sess
    )


@accounts_bp.route('/income/create', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def create_income():
    """Record a manual financial income entry."""
    act_sess = get_active_academic_session()
    sess_id = act_sess.id if act_sess else None

    if request.method == 'POST':
        cat_id = request.form.get('category_id', type=int)
        amt = request.form.get('amount')
        t_date = request.form.get('transaction_date')
        p_method = request.form.get('payment_method')
        ref_num = request.form.get('reference_number')
        payer = request.form.get('vendor_or_payer')
        desc = request.form.get('description')
        uploaded_file = request.files.get('attachment')

        emp_id = session.get('employee_id')

        try:
            txn = create_manual_transaction(
                category_id=cat_id,
                transaction_type='INCOME',
                amount=amt,
                transaction_date=t_date,
                description=desc,
                payment_method=p_method,
                reference_number=ref_num,
                vendor_or_payer=payer,
                created_by_id=emp_id,
                session_id=sess_id,
                file=uploaded_file
            )
            flash(f"🎉 Financial Income #{txn.transaction_number} of ₹{txn.amount:.2f} recorded successfully!", "success")
            return redirect(url_for('accounts.transactions_list'))
        except ValueError as e:
            flash(str(e), "danger")

    categories = get_all_categories(category_type='INCOME', active_only=True)
    return render_template(
        'accounts/income_form.html',
        categories=categories,
        valid_methods=sorted(list(VALID_PAYMENT_METHODS)),
        today_date=date.today().strftime('%Y-%m-%d'),
        active_session=act_sess
    )


@accounts_bp.route('/expenses/create', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def create_expense():
    """Record an operational school expense entry."""
    act_sess = get_active_academic_session()
    sess_id = act_sess.id if act_sess else None

    if request.method == 'POST':
        cat_id = request.form.get('category_id', type=int)
        amt = request.form.get('amount')
        t_date = request.form.get('transaction_date')
        p_method = request.form.get('payment_method')
        ref_num = request.form.get('reference_number')
        vendor = request.form.get('vendor_or_payer')
        desc = request.form.get('description')
        uploaded_file = request.files.get('attachment')

        emp_id = session.get('employee_id')

        try:
            txn = create_manual_transaction(
                category_id=cat_id,
                transaction_type='EXPENSE',
                amount=amt,
                transaction_date=t_date,
                description=desc,
                payment_method=p_method,
                reference_number=ref_num,
                vendor_or_payer=vendor,
                created_by_id=emp_id,
                session_id=sess_id,
                file=uploaded_file
            )
            flash(f"School Expense #{txn.transaction_number} of ₹{txn.amount:.2f} recorded successfully!", "success")
            return redirect(url_for('accounts.transactions_list'))
        except ValueError as e:
            flash(str(e), "danger")

    categories = get_all_categories(category_type='EXPENSE', active_only=True)
    return render_template(
        'accounts/expense_form.html',
        categories=categories,
        valid_methods=sorted(list(VALID_PAYMENT_METHODS)),
        today_date=date.today().strftime('%Y-%m-%d'),
        active_session=act_sess
    )


@accounts_bp.route('/transactions/<int:transaction_id>')
@login_required
@role_required('Admin')
def transaction_detail(transaction_id):
    """View details of a specific financial transaction."""
    txn = FinancialTransaction.query.get_or_404(transaction_id)
    return render_template('accounts/transaction_detail.html', transaction=txn)


@accounts_bp.route('/transactions/<int:transaction_id>/cancel', methods=['POST'])
@login_required
@role_required('Admin')
def cancel_transaction_route(transaction_id):
    """Void/cancel a financial transaction."""
    try:
        txn = cancel_transaction(transaction_id)
        flash(f"Transaction #{txn.transaction_number} has been cancelled and excluded from net balances.", "warning")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for('accounts.transactions_list'))


@accounts_bp.route('/categories', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def manage_categories():
    """Manage income and expense categories."""
    if request.method == 'POST':
        name = request.form.get('name')
        c_type = request.form.get('type')
        desc = request.form.get('description')
        cat_id = request.form.get('category_id', type=int)

        try:
            if cat_id:
                update_category(cat_id, name, desc)
                flash(f"Category '{name}' updated successfully!", "success")
            else:
                create_category(name, c_type, desc)
                flash(f"New {c_type} category '{name}' created successfully!", "success")
            return redirect(url_for('accounts.manage_categories'))
        except ValueError as e:
            flash(str(e), "danger")

    categories = get_all_categories(active_only=False)
    income_cats = [c for c in categories if c.type == 'INCOME']
    expense_cats = [c for c in categories if c.type == 'EXPENSE']

    return render_template(
        'accounts/categories.html',
        income_categories=income_cats,
        expense_categories=expense_cats
    )


@accounts_bp.route('/categories/<int:category_id>/toggle', methods=['POST'])
@login_required
@role_required('Admin')
def toggle_category(category_id):
    """Activate or deactivate a financial category."""
    try:
        cat = toggle_category_status(category_id)
        status_str = "activated" if cat.is_active else "deactivated"
        flash(f"Financial category '{cat.name}' has been {status_str}.", "info")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for('accounts.manage_categories'))


@accounts_bp.route('/attachments/<int:transaction_id>')
@login_required
@role_required('Admin')
def download_attachment(transaction_id):
    """Authorization-protected download route for transaction supporting documents."""
    txn = FinancialTransaction.query.get_or_404(transaction_id)
    if not txn.attachment_path:
        flash("No document attached to this transaction.", "warning")
        return redirect(url_for('accounts.transaction_detail', transaction_id=txn.id))

    filename = txn.attachment_path.replace('uploads/finance/', '')
    upload_dir = os.path.join(current_app.static_folder, 'uploads', 'finance')
    return send_from_directory(upload_dir, filename, as_attachment=True, download_name=txn.original_filename or filename)


@accounts_bp.route('/export/csv')
@login_required
@role_required('Admin')
def export_csv():
    """Generate downloadable CSV export of filtered financial transactions."""
    act_sess = get_active_academic_session()
    sess_id = act_sess.id if act_sess else None

    t_type = request.args.get('type')
    cat_id = request.args.get('category_id', type=int)
    method = request.args.get('payment_method')
    status = request.args.get('status')
    date_preset = request.args.get('date_preset')
    start_d = request.args.get('start_date')
    end_d = request.args.get('end_date')
    search_q = request.args.get('q')

    transactions = get_financial_transactions(
        session_id=sess_id,
        category_id=cat_id,
        transaction_type=t_type,
        payment_method=method,
        status=status,
        date_preset=date_preset,
        start_date=start_d,
        end_date=end_d,
        search_query=search_q
    )

    output = io.StringIO()
    writer = csv.writer(output)

    # Write CSV Header
    writer.writerow([
        'Transaction #', 'Type', 'Category', 'Amount (INR)',
        'Date', 'Payment Method', 'Reference #', 'Payer/Vendor',
        'Status', 'Source', 'Description'
    ])

    for t in transactions:
        writer.writerow([
            t.transaction_number,
            t.transaction_type,
            t.category.name if t.category else 'N/A',
            f"{t.amount:.2f}",
            t.transaction_date.strftime('%Y-%m-%d'),
            t.payment_method,
            t.reference_number or '',
            t.vendor_or_payer or '',
            t.status,
            t.source_type,
            t.description or ''
        ])

    output.seek(0)
    filename = f"stratlearn_finance_export_{date.today().strftime('%Y%m%d')}.csv"
    
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )
