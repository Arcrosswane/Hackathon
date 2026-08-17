from datetime import datetime
from decimal import Decimal
from flask import Blueprint, render_template, request, jsonify, session, flash, redirect, url_for
from app.models import db, User, Student, Guardian, GuardianStudent, StoreCategory, StoreProduct, InventoryMovement, StoreOrder, StoreOrderItem, POSSale
from app.utils.decorators import login_required
from app.services.store_service import (
    seed_default_categories,
    seed_default_products_if_empty,
    get_store_categories,
    get_store_products,
    create_store_product,
    adjust_inventory,
    create_online_order,
    process_pos_sale,
    update_order_status
)

store_bp = Blueprint('store', __name__, url_prefix='/store')


@store_bp.route('/')
@store_bp.route('/catalog')
@login_required
def catalog():
    """Renders the Student/Parent Online Store Catalog & Product Directory Page."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None

    if not current_user:
        flash('Authentication required to access the School Store.', 'danger')
        return redirect(url_for('auth.login'))

    category_id = request.args.get('category_id', type=int)
    search_q = request.args.get('q', '').strip()

    categories = get_store_categories(current_user.school_id)
    products = get_store_products(
        school_id=current_user.school_id,
        category_id=category_id,
        search_query=search_q,
        is_admin=False
    )

    formatted_products = []
    for p in products:
        formatted_products.append({
            'id': p.id,
            'sku': p.sku,
            'name': p.name,
            'category_name': p.category.name if p.category else 'General',
            'description': p.description or '',
            'price': float(p.selling_price),
            'formatted_price': f"₹{p.selling_price:.2f}",
            'stock': p.stock_quantity,
            'is_available': p.is_available(),
            'is_low_stock': p.is_low_stock()
        })

    children = []
    if (current_user.user_type or '').lower() in ('parent', 'guardian'):
        gdn_id = current_user.linked_entity_id
        if gdn_id:
            links = GuardianStudent.query.filter_by(guardian_id=gdn_id).all()
            s_ids = [l.student_id for l in links]
            children = Student.query.filter(Student.id.in_(s_ids)).all() if s_ids else []

    print(f"[STORE BACKEND DEBUG] catalog() requested by user_id={current_user.id} ({current_user.username}), school_id={current_user.school_id}, total_products={len(formatted_products)}")

    return render_template(
        'store/catalog.html',
        current_user=current_user,
        categories=categories,
        products=formatted_products,
        active_category_id=category_id,
        search_q=search_q,
        children=children
    )


@store_bp.route('/orders/create', methods=['POST'])
@login_required
def submit_order():
    """Form / JSON API endpoint for submitting an online store order."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

    if request.is_json:
        data = request.get_json() or {}
    else:
        data = request.form

    print(f"[STORE BACKEND DEBUG] submit_order() payload received from user_id={current_user.id}: {data}")

    items = data.get('items', [])
    payment_method = data.get('payment_method', 'Pay at School')
    payment_status = data.get('payment_status', 'Pending')
    notes = data.get('notes', '')
    student_id = data.get('student_id')

    try:
        order = create_online_order(
            buyer_user=current_user,
            items=items,
            payment_method=payment_method,
            notes=notes,
            student_id=int(student_id) if student_id else None,
            payment_status=payment_status
        )

        msg = f"Order #{order.order_number} placed successfully!"
        if request.is_json:
            return jsonify({
                'status': 'success',
                'message': msg,
                'order_number': order.order_number,
                'total_amount': float(order.total_amount)
            })
        flash(msg, 'success')
        return redirect(url_for('store.user_orders'))

    except (ValueError, PermissionError) as ve:
        if request.is_json:
            return jsonify({'status': 'error', 'message': str(ve)}), 400
        flash(str(ve), 'danger')
        return redirect(url_for('store.catalog'))


@store_bp.route('/orders')
@login_required
def user_orders():
    """Renders user's order history & purchases ledger page."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user:
        return redirect(url_for('auth.login'))

    user_role = (current_user.user_type or '').lower()
    if user_role in ('admin', 'teacher', 'employee'):
        orders_query = StoreOrder.query.order_by(StoreOrder.created_at.desc()).all()
    else:
        orders_query = StoreOrder.query.filter_by(buyer_id=current_user.id).order_by(StoreOrder.created_at.desc()).all()

    return render_template(
        'store/orders.html',
        current_user=current_user,
        orders=orders_query
    )


@store_bp.route('/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    """Dedicated Order Detail & Printable Receipt Voucher Page."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user:
        return redirect(url_for('auth.login'))

    order = StoreOrder.query.get_or_404(order_id)
    user_role = (current_user.user_type or '').lower()
    if user_role not in ('admin', 'teacher', 'employee') and order.buyer_id != current_user.id:
        flash('Unauthorized to view this order detail.', 'danger')
        return redirect(url_for('store.user_orders'))

    return render_template(
        'store/order_detail.html',
        current_user=current_user,
        order=order
    )


@store_bp.route('/admin')
@login_required
def admin_dashboard():
    """Renders Admin Store & Inventory Command Center Dashboard."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user:
        return redirect(url_for('auth.login'))

    user_role = (current_user.user_type or '').lower()
    if user_role not in ('admin', 'teacher', 'employee'):
        flash('Access restricted to store administrators.', 'danger')
        return redirect(url_for('store.catalog'))

    categories = get_store_categories(current_user.school_id)
    products = get_store_products(school_id=current_user.school_id, is_admin=True)
    recent_movements = InventoryMovement.query.order_by(InventoryMovement.created_at.desc()).limit(10).all()
    recent_orders = StoreOrder.query.order_by(StoreOrder.created_at.desc()).limit(10).all()

    total_products = len(products)
    low_stock_count = sum(1 for p in products if p.is_low_stock())
    pending_orders_count = sum(1 for o in recent_orders if o.order_status == 'Pending')

    return render_template(
        'store/admin/dashboard.html',
        current_user=current_user,
        categories=categories,
        products=products,
        recent_movements=recent_movements,
        recent_orders=recent_orders,
        total_products=total_products,
        low_stock_count=low_stock_count,
        pending_orders_count=pending_orders_count
    )


@store_bp.route('/admin/products')
@login_required
def admin_products():
    """Dedicated Products Master Roster Page."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user:
        return redirect(url_for('auth.login'))

    user_role = (current_user.user_type or '').lower()
    if user_role not in ('admin', 'teacher', 'employee'):
        flash('Access restricted to store administrators.', 'danger')
        return redirect(url_for('store.catalog'))

    category_id = request.args.get('category_id', type=int)
    search_q = request.args.get('q', '').strip()

    categories = get_store_categories(current_user.school_id)
    products = get_store_products(
        school_id=current_user.school_id,
        category_id=category_id,
        search_query=search_q,
        is_admin=True
    )

    return render_template(
        'store/admin/products_list.html',
        current_user=current_user,
        products=products,
        categories=categories,
        active_category_id=category_id,
        search_q=search_q
    )


@store_bp.route('/admin/movements')
@login_required
def admin_movements():
    """Dedicated Stock Movement Audit Log Page."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user:
        return redirect(url_for('auth.login'))

    user_role = (current_user.user_type or '').lower()
    if user_role not in ('admin', 'teacher', 'employee'):
        flash('Access restricted to store administrators.', 'danger')
        return redirect(url_for('store.catalog'))

    movements = InventoryMovement.query.order_by(InventoryMovement.created_at.desc()).limit(100).all()

    return render_template(
        'store/admin/movements_list.html',
        current_user=current_user,
        movements=movements
    )


@store_bp.route('/admin/orders')
@login_required
def admin_orders():
    """Dedicated Store Orders Queue Page."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user:
        return redirect(url_for('auth.login'))

    user_role = (current_user.user_type or '').lower()
    if user_role not in ('admin', 'teacher', 'employee'):
        flash('Access restricted to store administrators.', 'danger')
        return redirect(url_for('store.catalog'))

    status_filter = request.args.get('status', '').strip()
    query = StoreOrder.query
    if status_filter:
        query = query.filter_by(order_status=status_filter)

    orders = query.order_by(StoreOrder.created_at.desc()).all()

    return render_template(
        'store/admin/orders_list.html',
        current_user=current_user,
        orders=orders,
        status_filter=status_filter
    )


@store_bp.route('/admin/products/create', methods=['GET', 'POST'])
@login_required
def admin_create_product():
    """Dedicated Add New Product Page (GET & POST)."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user:
        return redirect(url_for('auth.login'))

    user_role = (current_user.user_type or '').lower()
    if user_role not in ('admin', 'teacher', 'employee'):
        flash('Access restricted to store administrators.', 'danger')
        return redirect(url_for('store.catalog'))

    categories = get_store_categories(current_user.school_id)

    if request.method == 'GET':
        return render_template(
            'store/admin/product_form.html',
            current_user=current_user,
            categories=categories
        )

    data = request.form
    name = data.get('name')
    category_id = data.get('category_id')
    sku = data.get('sku')
    selling_price = data.get('selling_price')
    cost_price = data.get('cost_price')
    stock_quantity = data.get('stock_quantity', 0)
    low_stock_threshold = data.get('low_stock_threshold', 5)
    description = data.get('description', '')

    try:
        prod = create_store_product(
            school_id=current_user.school_id,
            name=name,
            category_id=int(category_id),
            sku=sku,
            selling_price=selling_price,
            stock_quantity=int(stock_quantity),
            low_stock_threshold=int(low_stock_threshold),
            cost_price=cost_price if cost_price else None,
            description=description,
            user_id=current_user.id
        )

        flash(f"Product '{prod.name}' (SKU: {prod.sku}) created successfully!", 'success')
        return redirect(url_for('store.admin_products'))

    except (ValueError, PermissionError) as ve:
        flash(str(ve), 'danger')
        return render_template(
            'store/admin/product_form.html',
            current_user=current_user,
            categories=categories,
            form_data=data
        )


@store_bp.route('/admin/inventory/adjust', methods=['GET', 'POST'])
@login_required
def admin_adjust_inventory():
    """Dedicated Stock Adjustment Page (GET & POST)."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user:
        return redirect(url_for('auth.login'))

    user_role = (current_user.user_type or '').lower()
    if user_role not in ('admin', 'teacher', 'employee'):
        flash('Access restricted to store administrators.', 'danger')
        return redirect(url_for('store.catalog'))

    products = get_store_products(school_id=current_user.school_id, is_admin=True)
    selected_product_id = request.args.get('product_id', type=int)

    if request.method == 'GET':
        return render_template(
            'store/admin/inventory_adjust_form.html',
            current_user=current_user,
            products=products,
            selected_product_id=selected_product_id
        )

    data = request.form
    product_id = data.get('product_id')
    quantity_change = data.get('quantity_change')
    movement_type = data.get('movement_type', 'MANUAL_ADJUSTMENT')
    notes = data.get('notes', '')

    try:
        prod = adjust_inventory(
            product_id=int(product_id),
            quantity_change=int(quantity_change),
            movement_type=movement_type,
            notes=notes,
            user_id=current_user.id
        )

        flash(f"Inventory for '{prod.name}' adjusted. New stock: {prod.stock_quantity}", 'success')
        return redirect(url_for('store.admin_products'))

    except (ValueError, PermissionError) as ve:
        flash(str(ve), 'danger')
        return render_template(
            'store/admin/inventory_adjust_form.html',
            current_user=current_user,
            products=products,
            selected_product_id=int(product_id) if product_id else None
        )


@store_bp.route('/admin/orders/<int:order_id>/status', methods=['POST'])
@login_required
def admin_update_order_status(order_id):
    """Admin endpoint to update order status."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

    new_status = request.form.get('order_status')
    try:
        order = update_order_status(order_id, new_status, staff_user=current_user)
        flash(f"Order #{order.order_number} status updated to '{new_status}'.", 'success')
        return redirect(url_for('store.admin_orders'))
    except (ValueError, PermissionError) as ve:
        flash(str(ve), 'danger')
        return redirect(url_for('store.admin_orders'))


@store_bp.route('/pos')
@login_required
def pos_terminal():
    """Renders the Physical School Store POS Terminal Page."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None

    if not current_user:
        flash('Authentication required for POS terminal.', 'danger')
        return redirect(url_for('auth.login'))

    user_role = (current_user.user_type or '').lower()
    if user_role not in ('admin', 'teacher', 'employee'):
        flash('Access to POS Terminal is restricted to store staff.', 'danger')
        return redirect(url_for('store.catalog'))

    products = get_store_products(school_id=current_user.school_id, is_admin=False)
    categories = get_store_categories(current_user.school_id)

    formatted_products = []
    for p in products:
        formatted_products.append({
            'id': p.id,
            'sku': p.sku,
            'name': p.name,
            'category_name': p.category.name if p.category else 'General',
            'price': float(p.selling_price),
            'formatted_price': f"₹{p.selling_price:.2f}",
            'stock': p.stock_quantity,
            'is_available': p.is_available()
        })

    return render_template(
        'store/pos.html',
        current_user=current_user,
        products=formatted_products,
        categories=categories
    )


@store_bp.route('/pos/checkout', methods=['POST'])
@login_required
def pos_checkout():
    """JSON API endpoint for completing a POS Counter Sale."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

    data = request.get_json() or {}
    items = data.get('items', [])
    customer_name = data.get('customer_name', 'Walk-in Customer')
    customer_type = data.get('customer_type', 'Walk-in')
    payment_method = data.get('payment_method', 'CASH')

    try:
        sale = process_pos_sale(
            cashier_user=current_user,
            items=items,
            customer_name=customer_name,
            customer_type=customer_type,
            payment_method=payment_method
        )

        formatted_items = []
        for item in sale.items:
            formatted_items.append({
                'name': item.product_name,
                'sku': item.sku,
                'quantity': item.quantity,
                'unit_price': float(item.unit_price),
                'line_total': float(item.line_total)
            })

        return jsonify({
            'status': 'success',
            'message': f"POS Sale #{sale.sale_number} completed successfully!",
            'receipt': {
                'sale_number': sale.sale_number,
                'created_at': sale.created_at.strftime('%b %d, %Y at %I:%M %p'),
                'customer_name': sale.customer_name,
                'customer_type': sale.customer_type,
                'payment_method': sale.payment_method,
                'total_amount': float(sale.total_amount),
                'cashier_name': current_user.username.capitalize(),
                'items': formatted_items
            }
        })

    except (ValueError, PermissionError) as ve:
        return jsonify({'status': 'error', 'message': str(ve)}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': f"Checkout failed: {str(e)}"}), 500
