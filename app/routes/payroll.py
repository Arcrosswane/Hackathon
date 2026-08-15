from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
from app.utils.decorators import login_required, role_required
from app.services.academic_service import get_active_academic_session
from app.services.employee_service import get_all_employees, get_employee_by_id
from app.services.payroll_service import (
    get_all_salary_components, create_salary_component, toggle_salary_component_status,
    get_all_salary_structures, create_salary_structure, update_salary_structure, delete_salary_structure,
    assign_salary_structure, assign_structure_to_all_employees, get_employee_active_assignment, calculate_employee_salary_snapshot,
    generate_batch_payroll, approve_payroll, record_salary_payment, delete_payroll_record,
    get_payroll_records, get_payroll_summary_metrics,
    VALID_PAYMENT_METHODS
)
from app.models import PayrollRecord, SalaryComponent, SalaryStructure, EmployeeSalaryAssignment, Employee

payroll_bp = Blueprint('payroll', __name__, url_prefix='/payroll')


@payroll_bp.route('/dashboard')
@login_required
@role_required('Admin')
def dashboard():
    """Admin Payroll Overview Dashboard."""
    act_sess = get_active_academic_session()
    curr_period = date.today().strftime('%Y-%m')

    selected_period = request.args.get('period', curr_period)
    metrics = get_payroll_summary_metrics(payroll_period=selected_period)
    recent_payrolls = get_payroll_records(payroll_period=selected_period)

    return render_template(
        'payroll/dashboard.html',
        metrics=metrics,
        recent_payrolls=recent_payrolls,
        selected_period=selected_period,
        active_session=act_sess
    )


@payroll_bp.route('/roster')
@login_required
@role_required('Admin')
def roster():
    """Monthly Payroll Roster and Payment Processing."""
    act_sess = get_active_academic_session()
    curr_period = date.today().strftime('%Y-%m')

    period = request.args.get('period', curr_period)
    dept = request.args.get('department')
    status = request.args.get('status')
    search_q = request.args.get('q')

    payrolls = get_payroll_records(
        payroll_period=period,
        department=dept,
        status=status,
        search_query=search_q
    )

    metrics = get_payroll_summary_metrics(payroll_period=period)
    employees = get_all_employees(active_only=True)
    departments = sorted(list(set(e.department for e in employees if e.department)))

    return render_template(
        'payroll/roster.html',
        payrolls=payrolls,
        metrics=metrics,
        departments=departments,
        selected_period=period,
        selected_dept=dept,
        selected_status=status,
        search_query=search_q,
        valid_methods=sorted(list(VALID_PAYMENT_METHODS)),
        active_session=act_sess
    )


@payroll_bp.route('/generate', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def generate_view():
    """Batch Payroll Generation Wizard."""
    act_sess = get_active_academic_session()
    sess_id = act_sess.id if act_sess else None

    if request.method == 'POST':
        period = request.form.get('payroll_period')
        emp_ids = request.form.getlist('employee_ids', type=int)

        admin_emp_id = session.get('employee_id')

        try:
            records = generate_batch_payroll(
                payroll_period=period,
                employee_ids=emp_ids if emp_ids else None,
                created_by_id=admin_emp_id,
                session_id=sess_id
            )
            flash(f"🎉 Generated {len(records)} payroll record(s) for period '{period}' successfully!", "success")
            return redirect(url_for('payroll.roster', period=period))
        except ValueError as e:
            flash(str(e), "danger")

    employees = get_all_employees(active_only=True)
    default_period = date.today().strftime('%Y-%m')

    return render_template(
        'payroll/generate.html',
        employees=employees,
        default_period=default_period,
        active_session=act_sess
    )


@payroll_bp.route('/<int:payroll_id>/approve', methods=['POST'])
@login_required
@role_required('Admin')
def approve_payroll_route(payroll_id):
    """Approve generated payroll record."""
    try:
        admin_emp_id = session.get('employee_id')
        p = approve_payroll(payroll_id, approved_by_id=admin_emp_id)
        flash(f"Payroll record #{p.salary_slip_number} approved successfully!", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(request.referrer or url_for('payroll.roster'))


@payroll_bp.route('/<int:payroll_id>/pay', methods=['POST'])
@login_required
@role_required('Admin')
def record_payment_route(payroll_id):
    """Record salary payment and auto-sync as expense transaction to Module 12 Accounts."""
    p_method = request.form.get('payment_method')
    p_ref = request.form.get('payment_reference')

    admin_emp_id = session.get('employee_id')

    try:
        p = record_salary_payment(
            payroll_id=payroll_id,
            payment_method=p_method,
            payment_reference=p_ref,
            paid_by_id=admin_emp_id
        )
        flash(f"💳 Salary payment of ₹{p.net_salary:.2f} for '{p.employee.full_name}' recorded and synced to Accounts & Finance!", "success")
    except ValueError as e:
        flash(str(e), "danger")

    return redirect(request.referrer or url_for('payroll.roster'))


@payroll_bp.route('/<int:payroll_id>/slip')
@login_required
def salary_slip(payroll_id):
    """Printable Salary Slip View with IDOR security."""
    payroll = PayrollRecord.query.get_or_404(payroll_id)

    user_role = session.get('user_role')
    user_emp_id = session.get('linked_entity_id') or session.get('employee_id')

    # Security check: Admins can view all salary slips. Employees can ONLY view their own.
    if user_role not in ('Admin', 'admin'):
        if not user_emp_id or payroll.employee_id != user_emp_id:
            flash("Unauthorized access to salary slip record.", "danger")
            return abort(403)

    return render_template('payroll/salary_slip.html', payroll=payroll)


@payroll_bp.route('/structures', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def structures_list():
    """Salary Structures catalog and builder."""
    if request.method == 'POST':
        name = request.form.get('name')
        desc = request.form.get('description')
        comp_ids = request.form.getlist('component_ids', type=int)
        amounts = request.form.getlist('amounts')
        auto_assign = (request.form.get('auto_assign_all') == '1')

        items = []
        for cid in comp_ids:
            val = request.form.get(f'amount_{cid}', 0.0)
            comp = SalaryComponent.query.get(cid)
            if comp:
                items.append({
                    'component_id': cid,
                    'calculation_type': comp.calculation_type,
                    'amount_or_percentage': val
                })

        try:
            struct = create_salary_structure(name, desc, items, auto_assign_all=auto_assign)
            msg = f"Salary Structure '{struct.name}' created with {len(items)} components!"
            if auto_assign:
                msg += " Auto-assigned to all active staff members."
            flash(msg, "success")
            return redirect(url_for('payroll.structures_list'))
        except ValueError as e:
            flash(str(e), "danger")

    structures = get_all_salary_structures(active_only=False)
    components = get_all_salary_components(active_only=False)

    return render_template(
        'payroll/structures.html',
        structures=structures,
        components=components
    )


@payroll_bp.route('/structures/<int:structure_id>/edit', methods=['POST'])
@login_required
@role_required('Admin')
def edit_structure(structure_id):
    """Edit an existing salary structure."""
    name = request.form.get('name')
    desc = request.form.get('description')
    comp_ids = request.form.getlist('component_ids', type=int)
    auto_assign = (request.form.get('auto_assign_all') == '1')

    items = []
    for cid in comp_ids:
        val = request.form.get(f'amount_{cid}', 0.0)
        comp = SalaryComponent.query.get(cid)
        if comp:
            items.append({
                'component_id': cid,
                'calculation_type': comp.calculation_type,
                'amount_or_percentage': val
            })

    try:
        struct = update_salary_structure(structure_id, name, desc, items, auto_assign_all=auto_assign)
        msg = f"Salary Structure '{struct.name}' updated successfully!"
        if auto_assign:
            msg += " Auto-assigned to all active staff members."
        flash(msg, "success")
    except ValueError as e:
        flash(str(e), "danger")

    return redirect(url_for('payroll.structures_list'))


@payroll_bp.route('/structures/<int:structure_id>/assign-all', methods=['POST'])
@login_required
@role_required('Admin')
def assign_all_structure_route(structure_id):
    """Bulk assign structure to all active employees."""
    try:
        count = assign_structure_to_all_employees(structure_id)
        flash(f"⚡ Structure assigned to {count} active staff members successfully!", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for('payroll.structures_list'))


@payroll_bp.route('/structures/<int:structure_id>/delete', methods=['POST'])
@login_required
@role_required('Admin')
def delete_structure_route(structure_id):
    """Delete a salary structure."""
    try:
        delete_salary_structure(structure_id)
        flash("Salary structure deleted successfully.", "info")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for('payroll.structures_list'))


@payroll_bp.route('/<int:payroll_id>/delete', methods=['POST'])
@login_required
@role_required('Admin')
def delete_payroll_route(payroll_id):
    """Delete a payroll record and clean up synced accounts expenses."""
    try:
        delete_payroll_record(payroll_id)
        flash("🗑️ Payroll record deleted successfully. You can now re-generate payroll for this period if needed.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(request.referrer or url_for('payroll.roster'))


@payroll_bp.route('/components', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def components_list():
    """Salary Components Manager (Earnings & Deductions)."""
    if request.method == 'POST':
        name = request.form.get('name')
        c_type = request.form.get('type')
        calc_t = request.form.get('calculation_type')
        def_val = request.form.get('default_value')
        desc = request.form.get('description')

        try:
            create_salary_component(name, c_type, calc_t, def_val, description=desc)
            flash(f"New {c_type} component '{name}' created successfully!", "success")
            return redirect(url_for('payroll.components_list'))
        except ValueError as e:
            flash(str(e), "danger")

    components = get_all_salary_components(active_only=False)
    earnings = [c for c in components if c.type == 'EARNING']
    deductions = [c for c in components if c.type == 'DEDUCTION']

    return render_template(
        'payroll/components.html',
        earnings=earnings,
        deductions=deductions
    )


@payroll_bp.route('/components/<int:component_id>/toggle', methods=['POST'])
@login_required
@role_required('Admin')
def toggle_component(component_id):
    """Toggle activation of a salary component."""
    try:
        c = toggle_salary_component_status(component_id)
        status_str = "activated" if c.is_active else "deactivated"
        flash(f"Salary component '{c.name}' {status_str}.", "info")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for('payroll.components_list'))


@payroll_bp.route('/assignments', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def assignments():
    """Employee Salary Structure Assignment Manager."""
    if request.method == 'POST':
        emp_id = request.form.get('employee_id', type=int)
        struct_id = request.form.get('salary_structure_id', type=int)
        eff_date = request.form.get('effective_from')
        notes = request.form.get('notes')

        try:
            assign_salary_structure(emp_id, struct_id, eff_date, notes)
            flash("Salary structure assigned to employee successfully!", "success")
            return redirect(url_for('payroll.assignments'))
        except ValueError as e:
            flash(str(e), "danger")

    employees = get_all_employees(active_only=True)
    structures = get_all_salary_structures(active_only=True)
    assignments_list = EmployeeSalaryAssignment.query.filter_by(is_active=True).all()

    return render_template(
        'payroll/assignments.html',
        employees=employees,
        structures=structures,
        assignments=assignments_list,
        today_date=date.today().strftime('%Y-%m-%d')
    )


@payroll_bp.route('/my-salary')
@login_required
def my_salary():
    """Employee Self-Service Salary Portal."""
    user_role = session.get('user_role')
    user_emp_id = session.get('linked_entity_id') or session.get('employee_id')

    if not user_emp_id:
        flash("No linked employee record found for your account.", "warning")
        return redirect(url_for('teacher.dashboard' if user_role in ('Teacher', 'teacher') else 'auth.login'))

    emp = get_employee_by_id(user_emp_id)
    if not emp:
        flash("Employee profile not found.", "danger")
        return redirect(url_for('teacher.dashboard'))

    payrolls = get_payroll_records(employee_id=emp.id)
    active_assignment = get_employee_active_assignment(emp.id)

    return render_template(
        'payroll/my_salary.html',
        employee=emp,
        payrolls=payrolls,
        active_assignment=active_assignment
    )
