from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from app import db  
from datetime import datetime
import uuid

# ✅ User Model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='User')
    profile_picture = db.Column(db.String(255), nullable=True, default='None')
    contact_number = db.Column(db.String(20))
    category = db.Column(db.String(100), nullable=True)  # Only required for suppliers
    # Relationship to orders
    orders = db.relationship('Order', backref='staff', lazy=True)

    def _repr_(self):
        return f"<User {self.username}, Role: {self.role}>"

# ✅ Inventory Model
class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)  # Available stock
    price = db.Column(db.Float, nullable=False)
    supplier = db.Column(db.String(100), nullable=False)
    availability = db.Column(db.String(20), nullable=False, default="Available")

    # ✅ Method to update stock
    def reduce_stock(self, quantity):
        if self.quantity >= quantity:
            self.quantity -= quantity
            if self.quantity == 0:
                self.availability = "Out of Stock"
            db.session.commit()
            return True
        return False

    def _repr_(self):
        return f"<Inventory {self.name}, Category: {self.category}, Stock: {self.quantity}>"

# ✅ Order Model
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('inventory.id'), nullable=False)  
    quantity = db.Column(db.Integer, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    
    # ✅ Status with new state "Completed"
    status = db.Column(db.String(20), default="Pending") 
    
    # ✅ Created and Completion Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # ✅ Add relationship to Inventory
    product = db.relationship('Inventory', backref='orders')

    # ✅ Generate invoice method
    def generate_invoice(self):
        invoice_number = f"INV-{uuid.uuid4().hex[:8].upper()}"

        product = Inventory.query.get(self.product_id)
        if product:
            total_amount = product.price * self.quantity

            invoice = Invoice(
                order_id=self.id,
                invoice_number=invoice_number,
                total_amount=total_amount,
                payment_method=self.payment_method
            )
            db.session.add(invoice)
            db.session.commit()
            return invoice
        return None

    # ✅ Complete order method
    def complete_order(self):
        self.status = 'Completed'
        self.completed_at = datetime.utcnow()

        invoice = self.generate_invoice()

        db.session.commit()
        return invoice

    def _repr_(self):
        return f"<Order {self.id}, Product: {self.product_id}, Status: {self.status}>"

# ✅ Invoice Model
class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)  # Link to Order
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    issued_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)

    # Relationship to Order
    order = db.relationship('Order', backref='invoice', lazy=True)

    def _repr_(self):
        return f"<Invoice {self.invoice_number}, Order: {self.order_id}>"




# ✅ Supply Model (For Purchases)
class Supply(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Supplier
    product_id = db.Column(db.Integer, db.ForeignKey('inventory.id'), nullable=False)  # Purchased product
    quantity = db.Column(db.Integer, nullable=False)  # Quantity purchased
    cost_price = db.Column(db.Float, nullable=False)  # Purchase price per unit
    total_cost = db.Column(db.Float, nullable=False)  # Total cost of purchase
    purchase_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  # Timestamp
    status = db.Column(db.String(20), default='Pending')  # Add status field
    
    # ✅ Relationship with User (Supplier)
    supplier = db.relationship('User', backref='supplies')
    
    # ✅ Relationship with Inventory
    product = db.relationship('Inventory', backref='supplies')

    def __repr__(self):
        return f"<Supply {self.id}, Supplier: {self.supplier_id}, Product: {self.product_id}, Quantity: {self.quantity}, Status: {self.status}>"
