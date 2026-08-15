import os
import uuid
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import func
from app.models import (
    db, Employee, School, AcademicSession,
    SalaryComponent, SalaryStructure, SalaryStructureItem,
    EmployeeSalaryAssignment, PayrollRecord, PayrollItem,
    FinanceCategory, FinancialTransaction
)
from app.services.academic_service import get_active_academic_session

VALID_COMPONENT_TYPES = {'EARNING', 'DEDUCTION'}
VALID_CALCULATION_TYPES = {'FIXED_AMOUNT', 'PERCENTAGE'}
VALID_PAYROLL_STATUSES = {'DRAFT', 'GENERATED', 'APPROVED', 'PAID', 'CANCELLED'}
VALID_PAYMENT_METHODS = {'BANK_TRANSFER', 'CASH', 'UPI', 'CHEQUE', 'OTHER'}

def get_all_salary_components(component_type=None, active_only=False):
    """Retrieve salary components with optional filtering."""
    query = SalaryComponent.query
    if component_type:
        query = query.filter_by(type=component_type.upper())
    if active_only:
        query = query.filter_by(is_active=True)
    return query.order_by(SalaryComponent.name.asc()).all()


def create_salary_component(name, component_type, calculation_type='FIXED_AMOUNT',
                            default_value=0.0, percentage_of_component_id=None,
                            description=None, school_id=None):
    """Create a new salary component (EARNING or DEDUCTION)."""
    if not name or not name.strip():
        raise ValueError("Component name is required.")

    ctype = str(component_type).upper().strip()
    if ctype not in VALID_COMPONENT_TYPES:
        raise ValueError(f"Invalid component type '{component_type}'. Must be 'EARNING' or 'DEDUCTION'.")

    calctype = str(calculation_type).upper().strip()
    if calctype not in VALID_CALCULATION_TYPES:
        raise ValueError("Calculation type must be 'FIXED_AMOUNT' or 'PERCENTAGE'.")

    try:
        val = round(Decimal(str(default_value)), 2)
        if val < 0:
            raise ValueError("Default value cannot be negative.")
    except Exception:
        raise ValueError("Invalid default value specified.")

    comp = SalaryComponent(
        school_id=school_id,
        name=name.strip(),
        type=ctype,
        calculation_type=calctype,
        default_value=val,
        percentage_of_component_id=percentage_of_component_id,
        description=description.strip() if description else None,
        is_active=True
    )
    db.session.add(comp)
    db.session.commit()
    return comp


def toggle_salary_component_status(component_id):
    """Toggle activation status of a salary component."""
    comp = SalaryComponent.query.get(component_id)
    if not comp:
        raise ValueError("Salary component not found.")
    comp.is_active = not comp.is_active
    db.session.commit()
    return comp


def get_all_salary_structures(active_only=False):
    """Retrieve salary structures."""
    query = SalaryStructure.query
    if active_only:
        query = query.filter_by(is_active=True)
    return query.order_by(SalaryStructure.name.asc()).all()


def create_salary_structure(name, description=None, component_items=None, school_id=None):
    """Create a new salary structure with component items."""
    if not name or not name.strip():
        raise ValueError("Salary structure name is required.")

    structure = SalaryStructure(
        school_id=school_id,
        name=name.strip(),
        description=description.strip() if description else None,
        is_active=True
    )
    db.session.add(structure)
    db.session.flush()

    if component_items:
        for item in component_items:
            comp_id = item.get('component_id')
            calc_t = item.get('calculation_type', 'FIXED_AMOUNT')
            val = item.get('amount_or_percentage', 0.0)

            if comp_id:
                s_item = SalaryStructureItem(
                    salary_structure_id=structure.id,
                    component_id=comp_id,
                    calculation_type=calc_t,
                    amount_or_percentage=round(Decimal(str(val)), 2)
                )
                db.session.add(s_item)

    db.session.commit()
    return structure


def assign_salary_structure(employee_id, salary_structure_id, effective_from=None, notes=None):
    """Assigns a salary structure to an employee."""
    emp = Employee.query.get(employee_id)
    if not emp:
        raise ValueError("Employee record not found.")

    struct = SalaryStructure.query.get(salary_structure_id)
    if not struct:
        raise ValueError("Salary structure not found.")

    eff_date = effective_from if isinstance(effective_from, date) else datetime.strptime(str(effective_from), '%Y-%m-%d').date() if effective_from else date.today()

    # Deactivate previous assignments
    prev_assignments = EmployeeSalaryAssignment.query.filter_by(employee_id=emp.id, is_active=True).all()
    for prev in prev_assignments:
        prev.is_active = False
        prev.effective_until = eff_date

    assignment = EmployeeSalaryAssignment(
        employee_id=emp.id,
        salary_structure_id=struct.id,
        effective_from=eff_date,
        is_active=True,
        notes=notes.strip() if notes else None
    )
    db.session.add(assignment)
    db.session.commit()
    return assignment


def get_employee_active_assignment(employee_id):
    """Retrieve active salary assignment for an employee."""
    return EmployeeSalaryAssignment.query.filter_by(employee_id=employee_id, is_active=True).first()


def calculate_employee_salary_snapshot(employee_id):
    """
    Calculates salary snapshot breakdown for an employee based on their active structure.
    Returns dict: {'structure': ..., 'items': [...], 'gross': Decimal, 'deductions': Decimal, 'net': Decimal}
    """
    emp = Employee.query.get(employee_id)
    if not emp:
        raise ValueError("Employee not found.")

    assignment = get_employee_active_assignment(employee_id)
    if not assignment or not assignment.structure:
        # Fallback to employee.monthly_salary if set
        base_salary = Decimal(str(emp.monthly_salary or 0.00))
        items = [{
            'component_name': 'Basic Salary',
            'component_type': 'EARNING',
            'calculation_type': 'FIXED_AMOUNT',
            'amount': base_salary
        }]
        return {
            'structure': None,
            'items': items,
            'gross': base_salary,
            'deductions': Decimal('0.00'),
            'net': base_salary
        }

    struct = assignment.structure
    items = []
    
    # 1. Process Fixed Earnings & find Basic Salary for percentage calculations
    basic_amount = Decimal('0.00')
    if emp.monthly_salary:
        basic_amount = Decimal(str(emp.monthly_salary))

    for item in struct.items:
        comp = item.component
        if not comp or not comp.is_active:
            continue

        if comp.name == 'Basic Salary' and item.amount_or_percentage > 0:
            basic_amount = Decimal(str(item.amount_or_percentage))

    # 2. Compute item amounts
    gross = Decimal('0.00')
    deductions = Decimal('0.00')

    for item in struct.items:
        comp = item.component
        if not comp or not comp.is_active:
            continue

        val = Decimal(str(item.amount_or_percentage))
        calc_t = item.calculation_type or comp.calculation_type

        if calc_t == 'PERCENTAGE':
            item_amount = round((basic_amount * val) / Decimal('100.00'), 2)
        else:
            item_amount = round(val, 2)

        if comp.type == 'EARNING':
            gross += item_amount
        elif comp.type == 'DEDUCTION':
            deductions += item_amount

        items.append({
            'component_name': comp.name,
            'component_type': comp.type,
            'calculation_type': calc_t,
            'amount': item_amount
        })

    # Ensure Basic Salary is present if gross is still 0
    if not items and basic_amount > 0:
        items.append({
            'component_name': 'Basic Salary',
            'component_type': 'EARNING',
            'calculation_type': 'FIXED_AMOUNT',
            'amount': basic_amount
        })
        gross = basic_amount

    net = max(round(gross - deductions, 2), Decimal('0.00'))

    return {
        'structure': struct,
        'items': items,
        'gross': gross,
        'deductions': deductions,
        'net': net
    }


def generate_salary_slip_number(payroll_period, employee_id):
    """Generates unique salary slip number e.g. PAY-2026-08-000123."""
    clean_period = str(payroll_period).replace('-', '')
    return f"PAY-{clean_period}-{employee_id:06d}"


def generate_batch_payroll(payroll_period, employee_ids=None, created_by_id=None, session_id=None):
    """
    Batch generates monthly payroll for employees for a given period (e.g. "2026-08").
    Prevents duplicate payroll generation for the same (employee_id, payroll_period).
    """
    if not payroll_period or not payroll_period.strip():
        raise ValueError("Payroll period is required (e.g. '2026-08').")

    period_key = payroll_period.strip()
    
    # Format label e.g., "August 2026"
    try:
        dt_obj = datetime.strptime(period_key, '%Y-%m')
        period_label = dt_obj.strftime('%B %Y')
    except Exception:
        period_label = period_key

    query = Employee.query.filter_by(is_active=True)
    if employee_ids:
        query = query.filter(Employee.id.in_(employee_ids))
    employees = query.all()

    if not employees:
        raise ValueError("No active employees found to generate payroll.")

    generated_records = []

    for emp in employees:
        # Check duplicate payroll record for period
        existing = PayrollRecord.query.filter_by(employee_id=emp.id, payroll_period=period_key).first()
        if existing:
            continue

        calc = calculate_employee_salary_snapshot(emp.id)
        slip_num = generate_salary_slip_number(period_key, emp.id)

        payroll = PayrollRecord(
            school_id=emp.institute_id,
            academic_session_id=session_id,
            employee_id=emp.id,
            payroll_period=period_key,
            period_label=period_label,
            salary_structure_id=calc['structure'].id if calc['structure'] else None,
            gross_salary=calc['gross'],
            total_deductions=calc['deductions'],
            net_salary=calc['net'],
            salary_slip_number=slip_num,
            status='GENERATED',
            generated_at=datetime.utcnow(),
            created_by_id=created_by_id
        )
        db.session.add(payroll)
        db.session.flush()

        # Save immutable snapshot items
        for item in calc['items']:
            p_item = PayrollItem(
                payroll_id=payroll.id,
                component_name=item['component_name'],
                component_type=item['component_type'],
                calculation_type=item['calculation_type'],
                amount=item['amount']
            )
            db.session.add(p_item)

        generated_records.append(payroll)

    db.session.commit()
    return generated_records


def approve_payroll(payroll_id, approved_by_id=None):
    """Approves a generated payroll record."""
    payroll = PayrollRecord.query.get(payroll_id)
    if not payroll:
        raise ValueError("Payroll record not found.")

    if payroll.status in ('PAID', 'CANCELLED'):
        raise ValueError(f"Cannot approve payroll in '{payroll.status}' status.")

    payroll.status = 'APPROVED'
    payroll.approved_at = datetime.utcnow()
    db.session.commit()
    return payroll


def record_salary_payment(payroll_id, payment_method='BANK_TRANSFER', payment_reference=None, paid_by_id=None):
    """
    Marks a payroll record as PAID and syncs as an expense transaction in Module 12 Accounts.
    """
    payroll = PayrollRecord.query.get(payroll_id)
    if not payroll:
        raise ValueError("Payroll record not found.")

    if payroll.status == 'PAID':
        return payroll

    pmeth = str(payment_method).upper().strip() if payment_method else 'BANK_TRANSFER'
    if pmeth not in VALID_PAYMENT_METHODS:
        pmeth = 'OTHER'

    payroll.status = 'PAID'
    payroll.payment_method = pmeth
    payroll.payment_reference = payment_reference.strip() if payment_reference else None
    payroll.paid_at = datetime.utcnow()
    db.session.commit()

    # Sync to Module 12 Accounts & Finance expense
    try:
        sync_payroll_to_finance_expense(payroll)
    except Exception:
        pass

    return payroll


def sync_payroll_to_finance_expense(payroll):
    """
    Syncs a completed salary payment as a Financial Transaction expense record in Module 12.
    Enforces duplicate accounting protection via (source_type='PAYROLL_PAYMENT', source_id=payroll.id).
    """
    if not payroll or payroll.status != 'PAID':
        return None

    # Duplicate protection check
    existing = FinancialTransaction.query.filter_by(source_type='PAYROLL_PAYMENT', source_id=payroll.id).first()
    if existing:
        return existing

    # Find or provision "Salaries" category
    cat = FinanceCategory.query.filter_by(name="Salaries", type="EXPENSE").first()
    if not cat:
        cat = FinanceCategory(name="Salaries", type="EXPENSE", description="Teacher and staff monthly payroll expenditures", is_active=True)
        db.session.add(cat)
        db.session.flush()

    sch = School.query.first()
    sch_id = sch.id if sch else None
    tx_num = f"TXN-SAL-{payroll.id:06d}"

    txn = FinancialTransaction(
        school_id=sch_id,
        academic_session_id=payroll.academic_session_id,
        category_id=cat.id,
        transaction_type='EXPENSE',
        transaction_number=tx_num,
        amount=payroll.net_salary,
        transaction_date=payroll.paid_at.date() if payroll.paid_at else date.today(),
        description=f"Salary Payment for {payroll.employee.full_name if payroll.employee else 'Employee'} ({payroll.period_label})",
        payment_method=payroll.payment_method if payroll.payment_method in VALID_PAYMENT_METHODS else 'OTHER',
        reference_number=payroll.payment_reference or payroll.salary_slip_number,
        vendor_or_payer=payroll.employee.full_name if payroll.employee else "Employee",
        source_type='PAYROLL_PAYMENT',
        source_id=payroll.id,
        status='COMPLETED',
        created_by_id=payroll.created_by_id
    )
    db.session.add(txn)
    db.session.commit()
    return txn


def get_payroll_records(payroll_period=None, department=None, status=None, search_query=None, employee_id=None):
    """Query payroll records with filters."""
    query = PayrollRecord.query

    if employee_id:
        query = query.filter_by(employee_id=employee_id)

    if payroll_period:
        query = query.filter_by(payroll_period=payroll_period)

    if status and status.upper() in VALID_PAYROLL_STATUSES:
        query = query.filter_by(status=status.upper())

    if department:
        query = query.join(Employee).filter(Employee.department == department)

    if search_query and search_query.strip():
        sq = f"%{search_query.strip()}%"
        query = query.join(Employee).filter(
            (PayrollRecord.salary_slip_number.ilike(sq)) |
            (Employee.full_name.ilike(sq)) |
            (Employee.registration_number.ilike(sq)) |
            (PayrollRecord.payment_reference.ilike(sq))
        )

    return query.order_by(PayrollRecord.generated_at.desc(), PayrollRecord.id.desc()).all()


def get_payroll_summary_metrics(payroll_period=None):
    """Calculates summary payroll metrics server-side using SQL aggregation."""
    query = db.session.query(
        func.count(PayrollRecord.id).label('total_count'),
        func.coalesce(func.sum(PayrollRecord.gross_salary), 0).label('total_gross'),
        func.coalesce(func.sum(PayrollRecord.total_deductions), 0).label('total_deductions'),
        func.coalesce(func.sum(PayrollRecord.net_salary), 0).label('total_net')
    ).filter(PayrollRecord.status != 'CANCELLED')

    if payroll_period:
        query = query.filter(PayrollRecord.payroll_period == payroll_period)

    row = query.first()

    paid_row = db.session.query(
        func.count(PayrollRecord.id).label('paid_count'),
        func.coalesce(func.sum(PayrollRecord.net_salary), 0).label('paid_net')
    ).filter(PayrollRecord.status == 'PAID')
    
    if payroll_period:
        paid_row = paid_row.filter(PayrollRecord.payroll_period == payroll_period)
    
    p_res = paid_row.first()

    return {
        'total_count': row.total_count or 0,
        'total_gross': float(row.total_gross or 0.0),
        'total_deductions': float(row.total_deductions or 0.0),
        'total_net': float(row.total_net or 0.0),
        'paid_count': p_res.paid_count or 0,
        'paid_net': float(p_res.paid_net or 0.0),
        'pending_count': (row.total_count or 0) - (p_res.paid_count or 0),
        'pending_net': float(row.total_net or 0.0) - float(p_res.paid_net or 0.0)
    }
