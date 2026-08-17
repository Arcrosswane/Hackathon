import uuid
import html
from datetime import datetime, date
from decimal import Decimal
from app.models import (
    db, User, Student, Guardian, School,
    StoreCategory, StoreProduct, InventoryMovement, StoreOrder, StoreOrderItem, POSSale, POSSaleItem
)
from app.models.finance import FinanceCategory, FinancialTransaction

DEFAULT_CATEGORIES = [
    {'name': 'Uniform', 'description': 'Official school uniforms, blazers, shirts, trousers, and skirts.'},
    {'name': 'Books', 'description': 'Textbooks, workbooks, reference guides, and syllabus materials.'},
    {'name': 'Stationery', 'description': 'Notebooks, pens, pencils, geometry boxes, and drawing pads.'},
    {'name': 'Accessories', 'description': 'School bags, water bottles, lunch boxes, belts, and ties.'},
    {'name': 'School Supplies', 'description': 'Badges, ID card holders, sports equipment, and miscellaneous supplies.'}
]

DEFAULT_PRODUCTS = [
    {
        'category_name': 'Uniform',
        'sku': 'UNIF-SHIRT-M',
        'name': 'School White Shirt (Size M)',
        'description': 'Breathable cotton blend white uniform shirt with embroidered school logo.',
        'selling_price': Decimal('450.00'),
        'cost_price': Decimal('280.00'),
        'stock_quantity': 45,
        'low_stock_threshold': 10
    },
    {
        'category_name': 'Uniform',
        'sku': 'UNIF-BLAZER-L',
        'name': 'Official School Navy Blazer (Size L)',
        'description': 'Premium navy blue winter blazer with gold crest buttons and lining.',
        'selling_price': Decimal('1450.00'),
        'cost_price': Decimal('950.00'),
        'stock_quantity': 20,
        'low_stock_threshold': 5
    },
    {
        'category_name': 'Books',
        'sku': 'BOOK-MATH-G9',
        'name': 'NCERT Mathematics Grade 9 Textbook',
        'description': 'Official academic curriculum textbook for Grade 9 Mathematics.',
        'selling_price': Decimal('180.00'),
        'cost_price': Decimal('140.00'),
        'stock_quantity': 60,
        'low_stock_threshold': 15
    },
    {
        'category_name': 'Books',
        'sku': 'BOOK-SCI-G9',
        'name': 'NCERT Science Grade 9 Textbook',
        'description': 'Complete Physics, Chemistry & Biology textbook for Grade 9.',
        'selling_price': Decimal('210.00'),
        'cost_price': Decimal('160.00'),
        'stock_quantity': 50,
        'low_stock_threshold': 10
    },
    {
        'category_name': 'Stationery',
        'sku': 'STAT-NOTE-PACK6',
        'name': 'Classmate Ruled Notebook Pack (Set of 6)',
        'description': '172 pages single-line notebook set with high-grade paper.',
        'selling_price': Decimal('320.00'),
        'cost_price': Decimal('220.00'),
        'stock_quantity': 80,
        'low_stock_threshold': 20
    },
    {
        'category_name': 'Stationery',
        'sku': 'STAT-GEOM-BOX',
        'name': 'Camlin Geometry Box Kit',
        'description': 'Precision compass, dividers, set squares, ruler, and eraser set.',
        'selling_price': Decimal('120.00'),
        'cost_price': Decimal('85.00'),
        'stock_quantity': 35,
        'low_stock_threshold': 8
    },
    {
        'category_name': 'Accessories',
        'sku': 'ACC-BAG-NAVY',
        'name': 'Ergonomic Waterproof School Backpack',
        'description': '3-compartment padded navy backpack with bottle holder and reflective strips.',
        'selling_price': Decimal('850.00'),
        'cost_price': Decimal('550.00'),
        'stock_quantity': 25,
        'low_stock_threshold': 5
    }
]


def seed_default_categories(school_id=None):
    """Auto-seeds standard store categories if empty."""
    try:
        sch = School.query.first()
        sch_id = school_id or (sch.id if sch else None)

        if StoreCategory.query.count() == 0:
            for cat_data in DEFAULT_CATEGORIES:
                cat = StoreCategory(
                    school_id=sch_id,
                    name=cat_data['name'],
                    description=cat_data['description'],
                    is_active=True
                )
                db.session.add(cat)
            db.session.commit()
    except Exception as e:
        db.session.rollback()


def seed_default_products_if_empty(school_id=None):
    """Auto-seeds demo products if catalog is empty."""
    try:
        seed_default_categories(school_id)
        sch = School.query.first()
        sch_id = school_id or (sch.id if sch else None)

        if StoreProduct.query.count() == 0:
            for p_data in DEFAULT_PRODUCTS:
                cat = StoreCategory.query.filter_by(name=p_data['category_name']).first()
                if not cat:
                    continue

                prod = StoreProduct(
                    school_id=sch_id,
                    category_id=cat.id,
                    sku=p_data['sku'],
                    name=p_data['name'],
                    description=p_data['description'],
                    selling_price=p_data['selling_price'],
                    cost_price=p_data['cost_price'],
                    stock_quantity=p_data['stock_quantity'],
                    low_stock_threshold=p_data['low_stock_threshold'],
                    is_active=True
                )
                db.session.add(prod)
                db.session.flush()

                # Log initial inventory movement
                movement = InventoryMovement(
                    product_id=prod.id,
                    quantity_change=p_data['stock_quantity'],
                    new_stock_level=p_data['stock_quantity'],
                    movement_type='PURCHASE',
                    notes='Initial Stock Seeding'
                )
                db.session.add(movement)

            db.session.commit()
    except Exception as e:
        db.session.rollback()


def get_store_categories(school_id=None):
    """Returns active store categories."""
    seed_default_categories(school_id)
    return StoreCategory.query.filter_by(is_active=True).all()


def get_store_products(school_id=None, category_id=None, search_query=None, is_admin=False):
    """
    Returns products matching filters.
    Students/Parents see active in-stock products. Admins see all products.
    """
    seed_default_products_if_empty(school_id)

    query = StoreProduct.query
    if not is_admin:
        query = query.filter(StoreProduct.is_active == True)

    if category_id:
        query = query.filter(StoreProduct.category_id == category_id)

    if search_query:
        sq = f"%{search_query.strip()}%"
        query = query.filter(
            db.or_(
                StoreProduct.name.ilike(sq),
                StoreProduct.sku.ilike(sq),
                StoreProduct.description.ilike(sq)
            )
        )

    return query.order_by(StoreProduct.name.asc()).all()


def create_store_product(
    school_id,
    name,
    category_id,
    sku,
    selling_price,
    stock_quantity=0,
    low_stock_threshold=5,
    cost_price=None,
    description=None,
    image_url=None,
    user_id=None
):
    """Creates a new store product and records initial inventory movement."""
    clean_sku = (sku or '').strip().upper()
    clean_name = html.escape((name or '').strip())

    if not clean_name:
        raise ValueError("Product name is required.")
    if not clean_sku:
        raise ValueError("SKU code is required.")

    if StoreProduct.query.filter_by(sku=clean_sku).first():
        raise ValueError(f"Product with SKU '{clean_sku}' already exists.")

    try:
        price = Decimal(str(selling_price))
        if price <= 0:
            raise ValueError("Selling price must be greater than zero.")
    except Exception:
        raise ValueError("Invalid selling price value.")

    c_price = Decimal(str(cost_price)) if cost_price else None

    product = StoreProduct(
        school_id=school_id or 1,
        category_id=category_id,
        sku=clean_sku,
        name=clean_name,
        description=html.escape((description or '').strip()) if description else None,
        selling_price=price,
        cost_price=c_price,
        stock_quantity=max(0, int(stock_quantity)),
        low_stock_threshold=max(1, int(low_stock_threshold)),
        image_url=image_url,
        is_active=True
    )
    db.session.add(product)
    db.session.flush()

    if product.stock_quantity > 0:
        mv = InventoryMovement(
            product_id=product.id,
            user_id=user_id,
            quantity_change=product.stock_quantity,
            new_stock_level=product.stock_quantity,
            movement_type='PURCHASE',
            notes='Initial stock addition'
        )
        db.session.add(mv)

    db.session.commit()
    return product


def adjust_inventory(product_id, quantity_change, movement_type, notes=None, user_id=None):
    """
    Atomic inventory adjustment.
    Updates stock_quantity, records InventoryMovement, and triggers low-stock warning if threshold is breached.
    """
    product = StoreProduct.query.get(product_id)
    if not product:
        raise ValueError("Product not found.")

    qty = int(quantity_change)
    new_stock = product.stock_quantity + qty

    if new_stock < 0:
        raise ValueError(f"Insufficient stock for '{product.name}'. Current stock: {product.stock_quantity}, Attempted change: {qty}")

    product.stock_quantity = new_stock

    mv = InventoryMovement(
        product_id=product.id,
        user_id=user_id,
        quantity_change=qty,
        new_stock_level=new_stock,
        movement_type=movement_type,
        notes=html.escape((notes or '').strip()) if notes else None,
        created_at=datetime.utcnow()
    )
    db.session.add(mv)

    # Low-Stock Notification Trigger (Module 23)
    if product.is_low_stock() and qty < 0:
        try:
            from app.services.notification_service import create_bulk_notifications
            admin_users = User.query.filter_by(user_type='Admin').all()
            admin_ids = [u.id for u in admin_users]
            create_bulk_notifications(
                recipient_ids=admin_ids,
                title=f"⚠️ Low Stock Warning: {product.name}",
                message=f"Stock level for '{product.name}' (SKU: {product.sku}) has fallen to {new_stock} units.",
                category='System',
                priority='Important',
                related_entity_type='StoreProduct',
                related_entity_id=product.id,
                action_url='/store/admin',
                school_id=product.school_id
            )
        except Exception as ne:
            db.session.rollback()

    db.session.commit()
    return product


def create_online_order(buyer_user, items, payment_method='Pay at School', notes=None, student_id=None, payment_status='Pending'):
    """
    Creates an Online Store Order with STRICT SERVER-SIDE PRICE RECALCULATION & STOCK RESERVATION.
    """
    if not buyer_user:
        raise PermissionError("Authentication required to place an order.")

    if not items or not isinstance(items, list):
        raise ValueError("Order must contain at least one item.")

    sch_id = buyer_user.school_id or 1
    total_amount = Decimal('0.00')
    order_items_to_create = []

    for item in items:
        pid = item.get('product_id')
        qty = int(item.get('quantity', 1))

        if qty <= 0:
            continue

        prod = StoreProduct.query.get(pid)
        if not prod or not prod.is_active:
            raise ValueError(f"Product #{pid} is no longer available.")

        if prod.stock_quantity < qty:
            raise ValueError(f"Insufficient stock for '{prod.name}'. Only {prod.stock_quantity} available.")

        unit_price = prod.selling_price
        line_total = unit_price * qty
        total_amount += line_total

        order_items_to_create.append({
            'product': prod,
            'quantity': qty,
            'unit_price': unit_price,
            'line_total': line_total
        })

    if not order_items_to_create:
        raise ValueError("No valid products in cart.")

    # Generate Human-Readable Order Number (ORD-2026-XXXXXX)
    short_hash = uuid.uuid4().hex[:6].upper()
    order_num = f"ORD-{datetime.utcnow().year}-{short_hash}"

    is_paid = (payment_status == 'Paid') or ('Online' in str(payment_method)) or ('Card' in str(payment_method))
    final_pay_status = 'Paid' if is_paid else 'Pending'
    final_ord_status = 'Confirmed' if is_paid else 'Pending'

    order = StoreOrder(
        school_id=sch_id,
        order_number=order_num,
        buyer_id=buyer_user.id,
        student_id=student_id,
        total_amount=total_amount,
        payment_method=payment_method,
        payment_status=final_pay_status,
        order_status=final_ord_status,
        notes=html.escape((notes or '').strip()) if notes else None,
        created_at=datetime.utcnow()
    )
    db.session.add(order)
    db.session.flush()

    # Accounts Integration for Paid Online Orders
    if is_paid:
        try:
            store_cat = FinanceCategory.query.filter_by(name='School Store Sales').first()
            if not store_cat:
                store_cat = FinanceCategory(
                    school_id=sch_id,
                    name='School Store Sales',
                    type='INCOME',
                    description='Income generated from School Store Online & POS Sales',
                    is_active=True
                )
                db.session.add(store_cat)
                db.session.flush()

            fin_txn = FinancialTransaction(
                school_id=sch_id,
                category_id=store_cat.id,
                transaction_type='INCOME',
                transaction_number=f"TXN-{order_num}",
                amount=total_amount,
                transaction_date=date.today(),
                description=f"Online Store Sale #{order_num} ({buyer_user.username})",
                payment_method=payment_method,
                reference_number=order_num,
                vendor_or_payer=buyer_user.username
            )
            db.session.add(fin_txn)
        except Exception as fe:
            db.session.rollback()

    # Deduct stock and attach items
    for item_data in order_items_to_create:
        prod = item_data['product']
        qty = item_data['quantity']

        oi = StoreOrderItem(
            order_id=order.id,
            product_id=prod.id,
            product_name=prod.name,
            sku=prod.sku,
            quantity=qty,
            unit_price=item_data['unit_price'],
            line_total=item_data['line_total']
        )
        db.session.add(oi)

        # Atomic stock deduction
        adjust_inventory(
            product_id=prod.id,
            quantity_change=-qty,
            movement_type='SALE',
            notes=f"Online Order #{order_num}",
            user_id=buyer_user.id
        )

    db.session.commit()

    # Trigger Order Placed Notification (Module 23)
    try:
        from app.services.notification_service import create_notification
        create_notification(
            recipient_id=buyer_user.id,
            title=f"Order Placed Successfully: {order_num}",
            message=f"Your order for {len(order_items_to_create)} item(s) totalling ₹{total_amount} has been received.",
            category='Fees',
            priority='Important',
            related_entity_type='StoreOrder',
            related_entity_id=order.id,
            action_url='/store/orders',
            school_id=sch_id
        )
    except Exception as ne:
        db.session.rollback()

    return order


def process_pos_sale(cashier_user, items, customer_name=None, customer_type='Walk-in', payment_method='CASH'):
    """
    Processes a Physical School Store POS Checkout.
    Deducts stock, generates receipt POS-2026-XXXXXX, and records FinancialTransaction in Accounts.
    """
    if not cashier_user:
        raise PermissionError("Cashier authentication required.")

    if not items or not isinstance(items, list):
        raise ValueError("POS transaction must contain at least one item.")

    sch_id = cashier_user.school_id or 1
    total_amount = Decimal('0.00')
    sale_items_to_create = []

    for item in items:
        pid = item.get('product_id')
        qty = int(item.get('quantity', 1))

        if qty <= 0:
            continue

        prod = StoreProduct.query.get(pid)
        if not prod or not prod.is_active:
            raise ValueError(f"Product SKU '{item.get('sku')}' is unavailable.")

        if prod.stock_quantity < qty:
            raise ValueError(f"Insufficient stock for '{prod.name}'. Current stock: {prod.stock_quantity}.")

        unit_price = prod.selling_price
        line_total = unit_price * qty
        total_amount += line_total

        sale_items_to_create.append({
            'product': prod,
            'quantity': qty,
            'unit_price': unit_price,
            'line_total': line_total
        })

    if not sale_items_to_create:
        raise ValueError("No valid products in POS cart.")

    # Generate POS Receipt Number (POS-2026-XXXXXX)
    short_hash = uuid.uuid4().hex[:6].upper()
    sale_num = f"POS-{datetime.utcnow().year}-{short_hash}"

    pos_sale = POSSale(
        school_id=sch_id,
        sale_number=sale_num,
        cashier_user_id=cashier_user.id,
        customer_name=html.escape((customer_name or 'Walk-in Customer').strip()),
        customer_type=customer_type,
        total_amount=total_amount,
        payment_method=payment_method,
        created_at=datetime.utcnow()
    )
    db.session.add(pos_sale)
    db.session.flush()

    for item_data in sale_items_to_create:
        prod = item_data['product']
        qty = item_data['quantity']

        psi = POSSaleItem(
            pos_sale_id=pos_sale.id,
            product_id=prod.id,
            product_name=prod.name,
            sku=prod.sku,
            quantity=qty,
            unit_price=item_data['unit_price'],
            line_total=item_data['line_total']
        )
        db.session.add(psi)

        # Deduct stock
        adjust_inventory(
            product_id=prod.id,
            quantity_change=-qty,
            movement_type='POS_SALE',
            notes=f"POS Sale #{sale_num}",
            user_id=cashier_user.id
        )

    # Accounts Integration: Record FinancialTransaction (INCOME)
    try:
        store_cat = FinanceCategory.query.filter_by(name='School Store Sales').first()
        if not store_cat:
            store_cat = FinanceCategory(
                school_id=sch_id,
                name='School Store Sales',
                type='INCOME',
                description='Income generated from School Store & POS Sales',
                is_active=True
            )
            db.session.add(store_cat)
            db.session.flush()

        fin_txn = FinancialTransaction(
            school_id=sch_id,
            category_id=store_cat.id,
            transaction_type='INCOME',
            transaction_number=f"TXN-{sale_num}",
            amount=total_amount,
            transaction_date=date.today(),
            description=f"POS Counter Sale #{sale_num} ({pos_sale.customer_name})",
            payment_method=payment_method,
            reference_number=sale_num,
            vendor_or_payer=pos_sale.customer_name
        )
        db.session.add(fin_txn)
    except Exception as fe:
        db.session.rollback()

    db.session.commit()
    return pos_sale


def update_order_status(order_id, new_status, staff_user=None):
    """
    Updates order status and triggers customer notifications.
    """
    order = StoreOrder.query.get(order_id)
    if not order:
        raise ValueError("Order not found.")

    valid_statuses = ['Pending', 'Confirmed', 'Preparing', 'Ready for Pickup', 'Completed', 'Cancelled', 'Returned']
    if new_status not in valid_statuses:
        raise ValueError(f"Invalid status '{new_status}'.")

    old_status = order.order_status
    order.order_status = new_status
    if new_status == 'Completed':
        order.payment_status = 'Paid'

    # If order cancelled or returned, restock items
    if new_status in ('Cancelled', 'Returned') and old_status not in ('Cancelled', 'Returned'):
        for item in order.items:
            adjust_inventory(
                product_id=item.product_id,
                quantity_change=item.quantity,
                movement_type='RETURN' if new_status == 'Returned' else 'CORRECTION',
                notes=f"Restocked due to Order #{order.order_number} {new_status}",
                user_id=staff_user.id if staff_user else None
            )

    db.session.commit()

    # Trigger Notification to buyer
    try:
        from app.services.notification_service import create_notification
        create_notification(
            recipient_id=order.buyer_id,
            title=f"Order Status Update: {order.order_number}",
            message=f"Your order #{order.order_number} status is now '{new_status}'.",
            category='Fees',
            priority='Important',
            related_entity_type='StoreOrder',
            related_entity_id=order.id,
            action_url='/store/orders',
            school_id=order.school_id
        )
    except Exception as ne:
        db.session.rollback()

    return order
