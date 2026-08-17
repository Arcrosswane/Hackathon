from datetime import datetime
from app.models import db

class StoreCategory(db.Model):
    __tablename__ = 'store_categories'

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    products = db.relationship('StoreProduct', backref='category', lazy=True)

    def __repr__(self):
        return f'<StoreCategory #{self.id} "{self.name}">'


class StoreProduct(db.Model):
    __tablename__ = 'store_products'

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('store_categories.id'), nullable=False)
    
    sku = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)

    selling_price = db.Column(db.Numeric(10, 2), nullable=False)
    cost_price = db.Column(db.Numeric(10, 2), nullable=True)

    stock_quantity = db.Column(db.Integer, default=0, nullable=False)
    low_stock_threshold = db.Column(db.Integer, default=5, nullable=False)

    image_url = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    inventory_movements = db.relationship('InventoryMovement', backref='product', cascade='all, delete-orphan', lazy=True)

    def is_low_stock(self):
        return self.stock_quantity <= self.low_stock_threshold

    def is_available(self):
        return self.is_active and self.stock_quantity > 0

    def to_dict(self):
        return {
            'id': self.id,
            'sku': self.sku,
            'name': self.name,
            'category_name': self.category.name if self.category else 'General',
            'selling_price': float(self.selling_price) if self.selling_price else 0.0,
            'cost_price': float(self.cost_price) if self.cost_price else 0.0,
            'stock_quantity': self.stock_quantity,
            'low_stock_threshold': self.low_stock_threshold,
            'is_active': self.is_active,
            'is_low_stock': self.is_low_stock()
        }

    def __repr__(self):
        return f'<StoreProduct SKU={self.sku} "{self.name}" Stock={self.stock_quantity}>'


class InventoryMovement(db.Model):
    __tablename__ = 'inventory_movements'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('store_products.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    quantity_change = db.Column(db.Integer, nullable=False) # positive or negative
    new_stock_level = db.Column(db.Integer, nullable=False)
    movement_type = db.Column(db.String(30), nullable=False) # PURCHASE, SALE, POS_SALE, MANUAL_ADJUSTMENT, RETURN, DAMAGE, CORRECTION
    notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship('User', lazy=True)

    def __repr__(self):
        return f'<InventoryMovement Product #{self.product_id} Change={self.quantity_change} Type={self.movement_type}>'


class StoreOrder(db.Model):
    __tablename__ = 'store_orders'

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    buyer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=True)

    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(db.String(30), default='Pay at School', nullable=False) # Pay at School, Cash, Online / Card, Fee Account
    payment_status = db.Column(db.String(20), default='Pending', nullable=False) # Pending, Paid, Refunded
    order_status = db.Column(db.String(30), default='Pending', nullable=False) # Pending, Confirmed, Preparing, Ready for Pickup, Completed, Cancelled, Returned

    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    buyer = db.relationship('User', lazy=True)
    student = db.relationship('Student', lazy=True)
    items = db.relationship('StoreOrderItem', backref='order', cascade='all, delete-orphan', lazy=True)

    def __repr__(self):
        return f'<StoreOrder #{self.order_number} Status={self.order_status} Total={self.total_amount}>'


class StoreOrderItem(db.Model):
    __tablename__ = 'store_order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('store_orders.id', ondelete='CASCADE'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('store_products.id'), nullable=False)

    product_name = db.Column(db.String(150), nullable=False)
    sku = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    line_total = db.Column(db.Numeric(10, 2), nullable=False)

    product = db.relationship('StoreProduct', lazy=True)

    def __repr__(self):
        return f'<StoreOrderItem Order #{self.order_id} SKU={self.sku} Qty={self.quantity}>'


class POSSale(db.Model):
    __tablename__ = 'pos_sales'

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=True)
    sale_number = db.Column(db.String(50), unique=True, nullable=False)
    cashier_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    customer_name = db.Column(db.String(100), nullable=True)
    customer_type = db.Column(db.String(30), default='Walk-in', nullable=False) # Student, Parent, Teacher, Staff, Walk-in
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(db.String(30), default='CASH', nullable=False) # CASH, UPI, CARD, OTHER

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    cashier = db.relationship('User', lazy=True)
    items = db.relationship('POSSaleItem', backref='sale', cascade='all, delete-orphan', lazy=True)

    def __repr__(self):
        return f'<POSSale #{self.sale_number} Total={self.total_amount}>'


class POSSaleItem(db.Model):
    __tablename__ = 'pos_sale_items'

    id = db.Column(db.Integer, primary_key=True)
    pos_sale_id = db.Column(db.Integer, db.ForeignKey('pos_sales.id', ondelete='CASCADE'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('store_products.id'), nullable=False)

    product_name = db.Column(db.String(150), nullable=False)
    sku = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    line_total = db.Column(db.Numeric(10, 2), nullable=False)

    product = db.relationship('StoreProduct', lazy=True)

    def __repr__(self):
        return f'<POSSaleItem Sale #{self.pos_sale_id} SKU={self.sku} Qty={self.quantity}>'
