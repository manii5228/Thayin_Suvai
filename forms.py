from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FloatField, IntegerField, BooleanField, TextAreaField, SelectField, DateTimeField, SubmitField
from wtforms.validators import DataRequired, Length, Email, NumberRange, Optional

#------------------Login-----------------------
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

# ------------------ Customer ------------------

class CustomerRegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=120)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    name = StringField('Full Name', validators=[DataRequired(), Length(max=120)])
    moblile = StringField('Mobile Number', validators=[DataRequired(), Length(min=10, max=15)])
    submit = SubmitField('Register')


# ------------------ Menu Item ------------------

class MenuItemForm(FlaskForm):
    name = StringField('Item Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional()])
    price = FloatField('Price', validators=[DataRequired()])
    quantity_available = IntegerField('Quantity Available', validators=[DataRequired(), NumberRange(min=0)])
    image = StringField('Image Filename', validators=[Optional()])  # Assuming filename is provided
    is_available = BooleanField('Available')
    submit = SubmitField('Save Item')
    category = SelectField('Category', choices=[
        ('Appetizer', 'Appetizer'),
        ('Main Course', 'Main Course'),
        ('Dessert', 'Dessert'),
        ('Beverage', 'Beverage')
    ], validators=[DataRequired()])


# ------------------ Order ------------------

class OrderForm(FlaskForm):
    customer_id = IntegerField('Customer ID', validators=[DataRequired()])
    status = SelectField('Order Status', choices=[
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Preparing', 'Preparing'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled')
    ])
    address_id = IntegerField('Address ID', validators=[Optional()])
    coupon_id = IntegerField('Coupon ID', validators=[Optional()])
    payment_id = IntegerField('Payment ID', validators=[Optional()])
    submit = SubmitField('Place Order')


# ------------------ Order Item ------------------

class OrderItemForm(FlaskForm):
    order_id = IntegerField('Order ID', validators=[DataRequired()])
    menu_item_id = IntegerField('Menu Item ID', validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Add Item')


# ------------------ Payment ------------------

class PaymentForm(FlaskForm):
    customer_id = IntegerField('Customer ID', validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired()])
    method = SelectField('Payment Method', choices=[
        ('Card', 'Card'),
        ('UPI', 'UPI'),
        ('COD', 'Cash on Delivery')
    ])
    status = SelectField('Status', choices=[
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Failed', 'Failed'),
        ('Refunded', 'Refunded')
    ])
    submit = SubmitField('Make Payment')


# ------------------ Coupon ------------------

class CouponForm(FlaskForm):
    code = StringField('Coupon Code', validators=[DataRequired()])
    discount = FloatField('Discount %', validators=[DataRequired(), NumberRange(min=0, max=100)])
    is_active = BooleanField('Is Active')
    valid_till = DateTimeField('Valid Till', format='%Y-%m-%d %H:%M:%S', validators=[Optional()])
    submit = SubmitField('Save Coupon')


# ------------------ Review ------------------

class ReviewForm(FlaskForm):
    user_id = IntegerField('Customer ID', validators=[DataRequired()])
    order_id = IntegerField('Order ID', validators=[DataRequired()])
    rating = IntegerField('Rating (1-5)', validators=[DataRequired(), NumberRange(min=1, max=5)])
    comment = TextAreaField('Comment', validators=[Optional()])
    submit = SubmitField('Submit Review')


# ------------------ Address ------------------

class AddressForm(FlaskForm):
    customer_id = IntegerField('Customer ID', validators=[DataRequired()])
    line1 = StringField('Address Line 1', validators=[DataRequired()])
    line2 = StringField('Address Line 2', validators=[Optional()])
    city = StringField('City', validators=[DataRequired()])
    state = StringField('State', validators=[DataRequired()])
    zip_code = StringField('Zip Code', validators=[DataRequired()])
    is_default = BooleanField('Set as Default')
    mobile_number = StringField('Mobile Number', validators=[DataRequired(), Length(min=10, max=15)])
    submit = SubmitField('Save Address')
