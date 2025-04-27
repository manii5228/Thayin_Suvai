from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
db = SQLAlchemy()


class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
  
    name = db.Column(db.String(120), nullable=False)



class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    price = db.Column(db.Float, nullable=False)
    quantity_available = db.Column(db.Integer, nullable=False)  # quantity available in stock
    is_available = db.Column(db.Boolean, default=True)
    image = db.Column(db.String(100))  # stores image filename


# Order Model
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    status = db.Column(db.String(50), default='Pending')  # e.g., Pending, Accepted, Preparing, Delivered, Cancelled
    order_time = db.Column(db.DateTime, server_default=db.func.now())
    items = db.relationship('OrderItem', backref='order')
    table_number = db.Column(db.Integer , nullable=True)
    order_type=db.Column(db.String(20),default="Dine-In")  
    payment_id = db.Column(db.Integer, db.ForeignKey('payment.id'), nullable=True)
    coupon_id = db.Column(db.Integer, db.ForeignKey('coupon.id'), nullable=True)
    address_id = db.Column(db.Integer, db.ForeignKey('address.id'))
    address = db.relationship('Address')  # ✅ This is important
    customer = db.relationship('Customer', backref='orders')


# OrderItem Model
class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_item.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    menu_item = db.relationship('MenuItem')
    notes = db.Column(db.String(255))



# Payment Model
class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    method = db.Column(db.String(50))  # e.g., Card, UPI, COD
    status = db.Column(db.String(50), default='Pending')  # Paid, Failed, Refunded
    timestamp = db.Column(db.DateTime, server_default=db.func.now())
    

# Coupon Model
class Coupon(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    discount = db.Column(db.Float, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    valid_till = db.Column(db.DateTime)

# Optional: Review Model
class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime)

    customer = db.relationship('Customer', backref='reviews')
    order = db.relationship('Order', backref='review')

# Optional: Address Model
class Address(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    line1 = db.Column(db.String(100))
    line2 = db.Column(db.String(100))
    city = db.Column(db.String(50))
    state = db.Column(db.String(50))
    zip_code = db.Column(db.String(20))
    mobile_number = db.Column(db.String(15))
    is_default = db.Column(db.Boolean, default=False)







