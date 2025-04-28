# ---------------------------- IMPORTS & SETUP ----------------------------
from flask import Flask, render_template, request, jsonify, session, redirect, url_for,flash
from models import db, MenuItem, Order, OrderItem, Payment, Review, Address, Customer
from datetime import datetime ,date, timedelta, timezone
from Thayin_Suvai_ok.forms import LoginForm,MenuItemForm, OrderForm, OrderItemForm, PaymentForm, CouponForm, ReviewForm 
import calendar
import os
from werkzeug.utils import secure_filename
from flask_migrate import Migrate
from datetime import datetime, timedelta, timezone
from pytz import timezone as pytz_timezone




app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///thyain_suvai.db'
app.config['SECRET_KEY'] = 'your_secret_key'
db.init_app(app)
migrate = Migrate(app, db)

# ----------------------------- CUSTOMER ROUTES -----------------------------
@app.route('/')
def index():
    menu = MenuItem.query.limit(6).all()
    return render_template('index.html',menu=menu)



@app.route('/customer_dashboard')
def customer_dashboard():
    if 'user_type' not in session or session['user_type'] != 'customer':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('login'))

    ist = pytz_timezone('Asia/Kolkata')
    
    # 🟢 Fetch orders first
    orders = Order.query.filter_by(customer_id=session['user_id']).order_by(Order.order_time.desc()).all()

    # 🔁 Then convert order times to IST
    for order in orders:
        order.order_time = order.order_time.replace(tzinfo=timezone.utc).astimezone(ist)

    return render_template('customer_dashboard.html', orders=orders)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        if username == 'admin@gmail.com' and password == 'Admin@password':
            session['user_id'] = 'admin'
            session['user_type'] = 'admin'
            flash('Welcome back Admin', 'success')
            return redirect(url_for('admin_dashboard'))

        customer = Customer.query.filter_by(username=username, password=password).first()
        if customer:
            session['user_id'] = customer.id
            session['user_type'] = 'customer'
            flash('Login successful!', 'success')
            return redirect(url_for('customer_dashboard'))

        flash('Invalid username or password', 'danger')

    return render_template('login.html', form=form)  # ✅ Pass form here!


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        name = request.form['name']

        customer = Customer(username=username, password=password, name=name)
        db.session.add(customer)
        db.session.commit()

        flash('Registration successful. Please login.')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/menu')
def browse_menu():
    menu = MenuItem.query.all()
    return render_template('menu.html', menu=menu)

@app.route('/cart', methods=['POST'])
def add_to_cart():
    item_id = request.form['item_id']
    quantity = int(request.form['quantity'])
    notes = request.form.get('notes', '')

    if 'cart' not in session:
        session['cart'] = []

     # Explicitly read-modify-write the cart
    cart = session['cart']
    cart.append({
        'menu_item_id': int(item_id),
        'quantity': quantity,
        'notes': notes
    })
    session['cart'] = cart  # 🔥 You MUST reassign back to session
    session.modified = True  # ✅ Ensures session updates

    flash("Item added to cart!", "success")
    return redirect(url_for('browse_menu'))

@app.route('/cart/view')
def view_cart():
    cart = session.get('cart', [])
    cart_items = []

    for item in cart:
        menu_item = MenuItem.query.get(item['menu_item_id'])
        if menu_item:
            quantity = int(item.get('quantity', 1))
            price = float(menu_item.price)
            total = quantity * price
            cart_items.append({
                'name': menu_item.name,
                'price': price,
                'quantity': quantity,
                'total': total,
                'id': menu_item.id
            })

    return render_template('cart.html', cart_items=cart_items)


@app.route('/place_order', methods=['POST'])
def place_order():
    if 'cart' not in session or 'user_id' not in session:
        flash("Session expired. Please try again.", "warning")
        return redirect(url_for('browse_menu'))

    # Step 1: Update Quantities
    for index, item in enumerate(session['cart']):
        new_qty = request.form.get(f'quantity_{index}')
        if new_qty and new_qty.isdigit():
            session['cart'][index]['quantity'] = int(new_qty)

    action = request.form.get('action')

    if action == 'update':
        flash('Cart updated successfully!', 'info')
        return redirect(url_for('view_cart'))  # Just refresh cart page

    # Step 2: If the action is 'buy', continue to process order
    order_type = request.form.get('order_type', 'Dine-In')
    table_number = request.form.get('table_number')
    grand_total = request.form.get('grand_total', type=float)


    session['order_type'] = order_type
    session['table_number'] = table_number if table_number else None

    if order_type == 'Delivery':
        return redirect(url_for('select_address'))  # ✅ updated flow

    return finalize_order()


@app.route('/select_address', methods=['GET', 'POST'])
def select_address():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    addresses = Address.query.filter_by(customer_id=session['user_id']).all()

    if request.method == 'POST':
        selected_address_id = request.form.get('selected_address')
        if selected_address_id:
            session['selected_address_id'] = selected_address_id
            return redirect(url_for('payment_page'))
        elif request.form.get('line1'):
            new_address = Address(
                customer_id=session['user_id'],
                line1=request.form['line1'],
                line2=request.form.get('line2', ''),
                city=request.form['city'],
                state=request.form['state'],
                mobile_number=request.form['mobile_number'],
                zip_code=request.form['zip_code'],
                is_default='is_default' in request.form
            )
            db.session.add(new_address)
            db.session.commit()
            session['selected_address_id'] = new_address.id
            return redirect(url_for('payment_page'))

    return render_template('select_address.html', addresses=addresses)


def finalize_order(payment_method=None, amount=None):
    # Retrieve session data
    order_type = session.get('order_type', 'Dine-In')
    table_number = session.get('table_number')
    address_id = session.get('selected_address_id')
    cart = session.get('cart', [])

    # Create new order
    order = Order(
        customer_id=session['user_id'],
        status='Placed',
        order_time=datetime.utcnow(),
        order_type=order_type,
        table_number=int(table_number) if table_number else None,
        address_id=int(address_id) if address_id else None
    )
    db.session.add(order)
    db.session.flush()  # Get order ID before commit

    # Add ordered items and update menu stock
    for item in cart:
        menu_item = MenuItem.query.get(item['menu_item_id'])
        quantity = item['quantity']

        if not menu_item or not menu_item.is_available or menu_item.quantity_available < quantity:
            db.session.rollback()
            flash("An item is out of stock or not found.", "danger")
            return redirect(url_for('view_cart'))

        menu_item.quantity_available -= quantity
        if menu_item.quantity_available == 0:
            menu_item.is_available = False

        db.session.add(OrderItem(
            order_id=order.id,
            menu_item_id=menu_item.id,
            quantity=quantity,
            notes=item.get('notes', '')
        ))

    
   
    # Commit changes and clear session
    db.session.commit()
    session.pop('cart', None)
    session.pop('order_type', None)
    session.pop('table_number', None)
    session.pop('selected_address_id', None)

    flash("Order placed successfully!", "success")
    return redirect(url_for('track_order', order_id=order.id))


@app.route('/cart/remove/<int:index>', methods=['GET'])
def remove_from_cart(index):
    cart = session.get('cart', [])
    if 0 <= index < len(cart):
        del cart[index]
        session['cart'] = cart
        flash('Item removed from cart.', 'info')
    else:
        flash('Invalid item index.', 'danger')
    return redirect(url_for('view_cart'))

@app.route('/cart/clear', methods=['GET'])
def clear_cart():
    session.pop('cart', None)
    flash('Your cart has been cleared.', 'info')
    return redirect(url_for('view_cart'))

@app.route('/cart/update', methods=['POST'])
def update_cart():
    cart = session.get('cart', [])
    updated_cart = []

    for i, item in enumerate(cart):
        qty_key = f'quantity_{i}'
        new_qty = request.form.get(qty_key)

        if new_qty and new_qty.isdigit():
            item['quantity'] = int(new_qty)

        updated_cart.append(item)

    session['cart'] = updated_cart
    flash("Cart updated successfully!", "success")
    return redirect(url_for('view_cart'))



@app.route('/admin/orders')
def admin_orders():
    orders = Order.query.order_by(Order.order_time.desc()).all()

    ist = pytz_timezone('Asia/Kolkata')
    for order in orders:
        order.order_time = order.order_time.replace(tzinfo=timezone.utc).astimezone(ist)

    return render_template('admin_orders.html', orders=orders)

@app.route('/order/<int:order_id>/cancel', methods=['POST'])
def cancel_order(order_id):
    order = Order.query.get(order_id)
    if order.customer_id == session.get('user_id') and order.status == 'Placed':
        order.status = 'Cancelled'
        db.session.commit()
        return redirect(url_for('track_order', order_id=order.id))
    return "Cannot cancel at this stage", 403



@app.route('/payment_page', methods=['GET', 'POST'])
def payment_page():
    if 'user_id' not in session or 'cart' not in session:
        flash("Session expired. Please try again.", "warning")
        return redirect(url_for('browse_menu'))

    # Check address for Delivery orders
    if session.get('order_type') == 'Delivery' and not session.get('selected_address_id'):
        flash("Please select your delivery address first.", "warning")
        return redirect(url_for('manage_address'))

    cart = session['cart']
    total = 0
    for item in cart:
        menu_item = MenuItem.query.get(item['menu_item_id'])
        if menu_item:
            total += menu_item.price * item['quantity']

    if request.method == 'POST':
        payment_method = "Cash on Delivery"
        return finalize_order(payment_method=payment_method, amount=total)

    return render_template('payment_page.html', total_amount=total)



@app.route('/payment', methods=['POST'])
def process_payment():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    order_id = request.form['order_id']
    method = request.form['method']
    amount = request.form['amount']

    # 1. Record payment
    payment = Payment(
        order_id=order_id,
        customer_id=session['user_id'],
        amount=amount,
        status='Success',
        method=method
    )
    db.session.add(payment)

    # 2. Update order status to 'Placed' if payment is successful
    order = Order.query.get(order_id)
    if order and order.status in ['Payment Pending']:
        order.status = 'Placed'
        db.session.commit()
        flash("Payment successful! Order confirmed.", "success")
    else:
        flash("Payment recorded, but unable to update order status.", "warning")

    return redirect(url_for('track_order', order_id=order_id))



@app.route('/orders')
def past_orders():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    orders = Order.query.filter_by(customer_id=session['user_id']).all()

    # Convert each order time to IST for display
    ist = pytz_timezone('Asia/Kolkata')
    for order in orders:
        order.order_time = order.order_time.replace(tzinfo=timezone.utc).astimezone(ist)

    return render_template('past_orders.html', orders=orders)

@app.route('/reorder/<int:order_id>', methods=['POST'])
def reorder(order_id):
    old_order = Order.query.get_or_404(order_id)
    if old_order.customer_id != session.get('user_id'):
        return "Unauthorized", 403
    new_order = Order(customer_id=session['user_id'], status='Placed', order_time=datetime.utcnow())
    db.session.add(new_order)
    db.session.flush()
    for item in old_order.items:
        db.session.add(OrderItem(order_id=new_order.id, menu_item_id=item.menu_item_id, quantity=item.quantity))
    db.session.commit()
    return redirect(url_for('track_order', order_id=new_order.id))


@app.route('/my_reviews')
def customer_reviews():
    


    if 'user_id' not in session:
        flash("Please login to view your reviews.", "warning")
        return redirect(url_for('login'))

    reviews = Review.query.filter_by(customer_id=session['user_id']).order_by(Review.timestamp.desc()).all()

    review_data = []
    for review in reviews:
        order = Order.query.get(review.order_id)
        review_data.append({
            'order_id': review.order_id,
            'comment': review.comment,
            'rating': review.rating,
            'timestamp': review.timestamp,
            'status': order.status if order else 'Unknown'
        })
    
    return render_template('customer_reviews.html', reviews=review_data)


@app.route('/orders/monthly')
def monthly_orders():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    now = datetime.now()
    first_day = date(now.year, now.month, 1)
    last_day = date(now.year, now.month, calendar.monthrange(now.year, now.month)[1])

    orders = Order.query.filter(
        Order.customer_id == session['user_id'],
        Order.order_time >= first_day,
        Order.order_time <= last_day
    ).order_by(Order.order_time.desc()).all()

    ist = pytz_timezone('Asia/Kolkata')
    for order in orders:
        order.order_time = order.order_time.replace(tzinfo=timezone.utc).astimezone(ist)

    return render_template('monthly_orders.html', orders=orders)

@app.route('/review/<int:order_id>', methods=['POST'])
def add_review(order_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    rating = int(request.form['rating'])
    comment = request.form.get('comment', '')

    review = Review(order_id=order_id, customer_id=session['user_id'], rating=rating, comment=comment, timestamp=datetime.utcnow())
    db.session.add(review)
    db.session.commit()
    flash('Review submitted successfully!')
    return redirect(url_for('track_order', order_id=order_id))

@app.route('/address', methods=['GET', 'POST'])
def manage_address():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        address = Address(
            customer_id=session['user_id'],
            line1=request.form['line1'],
            line2=request.form.get('line2', ''),
            city=request.form['city'],
            state=request.form['state'],
            mobile_number=request.form['mobile_number'],
            zip_code=request.form['zip_code'],
            is_default='is_default' in request.form
        )
        db.session.add(address)
        db.session.commit()
        flash('Address added successfully!')
        return redirect(url_for('manage_address'))

    addresses = Address.query.filter_by(customer_id=session['user_id']).all()
    return render_template('address.html', addresses=addresses)

@app.route('/menu/search')
def search_menu():
    query = request.args.get('query', '').strip()
    veg_filter = request.args.get('veg')
    sort_price = request.args.get('sort')  # 'asc' or 'desc'

    items = MenuItem.query
    if query:
        items = items.filter(MenuItem.name.ilike(f"%{query}%"))
    if veg_filter == 'veg':
        items = items.filter(MenuItem.description.ilike('%veg%'))
    elif veg_filter == 'nonveg':
        items = items.filter(MenuItem.description.ilike('%non-veg%'))

    if sort_price == 'asc':
        items = items.order_by(MenuItem.price.asc())
    elif sort_price == 'desc':
        items = items.order_by(MenuItem.price.desc())

    items = items.all()
    return render_template('menu_search.html', menu=items)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('index'))

# ----------------------------- ADMIN ROUTES -----------------------------
@app.route('/admin_dashboard')
def admin_dashboard():
    menu = MenuItem.query.all()
    customers = Customer.query.all()
    return render_template('admin_dashboard.html', menu=menu, customers=customers)

@app.route('/admin/add_menu', methods=['POST'])
def add_menu():
    name = request.form.get('name')
    description = request.form.get('description')
    base_price = request.form.get('base_price')
    quantity_available = request.form.get('quantity_available')
    is_available = request.form.get('is_available') == 'on'

    image_file = request.files.get('image')
    filename = None
    if image_file:
        filename = image_file.filename
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image_file.save(image_path)

    # Convert types properly
    try:
        new_menu = MenuItem(
            name=name,
            description=description,
            price=float(base_price),
            quantity_available=int(quantity_available),
            is_available=is_available,
            image=filename
        )
        db.session.add(new_menu)
        db.session.commit()
        flash('Item added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Error adding item: {str(e)}", 'danger')

    return redirect(url_for('admin_dashboard'))


@app.route('/admin/delete_menu/<int:menu_id>', methods=['POST'])
def delete_menu(menu_id):
    menu = MenuItem.query.get(menu_id)
    if menu:
        db.session.delete(menu)
        db.session.commit()
        flash('Item deleted successfully!')
    else:
        flash('Item not found!')
    return redirect(url_for('admin_dashboard'))




@app.route('/admin/update_status/<int:order_id>', methods=['POST'])
def update_status(order_id):
    new_status = request.form['status']
    valid_statuses = ['Pending', 'Accepted', 'Preparing', 'Ready', 'Delivered', 'Cancelled']
    if new_status not in valid_statuses:
        return "Invalid status value", 400

    order = Order.query.get_or_404(order_id)
    order.status = new_status
    db.session.commit()
    return redirect(url_for('admin_orders'))


@app.route('/edit_menu/<int:menu_id>', methods=['GET', 'POST'])
def edit_menu(menu_id):
    menu = MenuItem.query.get_or_404(menu_id)

    if request.method == 'POST':
        menu.name = request.form['name']
        menu.description = request.form['description']
        menu.price = float(request.form['price'])
        menu.quantity_available = int(request.form['quantity_available'])
        menu.is_available = 'is_available' in request.form

        # 🔄 Check and update image if a new one is uploaded
        if 'image' in request.files:
            image = request.files['image']
            if image and image.filename != "":
                filename = secure_filename(image.filename)
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                menu.image = filename  # Update image filename in DB

        db.session.commit()
        flash('Menu item updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('edit_menu.html', menu=menu)



@app.route('/admin/toggle_availability/<int:menu_id>', methods=['POST'])
def toggle_availability(menu_id):
    menu = MenuItem.query.get_or_404(menu_id)
    menu.is_available = not menu.is_available
    db.session.commit()
    flash(f"{menu.name} marked as {'Available' if menu.is_available else 'Sold Out'}.", 'info')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_customer/<int:customer_id>', methods=['POST'])
def delete_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    db.session.delete(customer)
    db.session.commit()
    flash('Customer deleted successfully!')
    return redirect(url_for('manage_customers'))


def get_date_range(filter_type):
    today = date.today()
    if filter_type == 'today':
        return today, today
    elif filter_type == 'week':
        start = today - timedelta(days=today.weekday())  # Monday
        end = start + timedelta(days=6)  # Sunday
        return start, end
    elif filter_type == 'month':
        start = date(today.year, today.month, 1)
        end = date(today.year, today.month, calendar.monthrange(today.year, today.month)[1])
        return start, end



@app.route('/admin_orders_today')
def admin_orders_today():
    if 'user_type' not in session or session['user_type'] != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('login'))

    # Get start and end of "today" in IST, convert to UTC
    ist = pytz_timezone('Asia/Kolkata')
    today_ist = datetime.now(ist).date()
    start_ist = datetime.combine(today_ist, datetime.min.time()).replace(tzinfo=ist)
    end_ist = datetime.combine(today_ist, datetime.max.time()).replace(tzinfo=ist)

    # Convert to UTC for filtering
    start_utc = start_ist.astimezone(timezone.utc)
    end_utc = end_ist.astimezone(timezone.utc)

    # Fetch orders placed in that UTC window
    todays_orders = Order.query.filter(
        Order.order_time >= start_utc,
        Order.order_time <= end_utc
    ).order_by(Order.order_time.desc()).all()

    # Categorize and convert times
    paid_orders = []
    unpaid_orders = []

    for order in todays_orders:
        # Convert UTC to IST for display
        order.order_time = order.order_time.replace(tzinfo=timezone.utc).astimezone(ist)

        payment = Payment.query.filter_by(order_id=order.id).first()
        if payment and payment.status == 'Success':
            paid_orders.append(order)
        else:
            unpaid_orders.append(order)

    return render_template('admin_orders_today.html', paid_orders=paid_orders, unpaid_orders=unpaid_orders)




@app.route('/admin/orders/week')
def admin_orders_week():
    start, end = get_date_range('week')
    orders = Order.query.filter(Order.order_time >= start, Order.order_time <= end).order_by(Order.order_time.desc()).all()
    return render_template('admin_orders_week_month.html', orders=orders, title="This Week's Orders")

@app.route('/admin/orders/month')
def admin_orders_month():
    start, end = get_date_range('month')
    orders = Order.query.filter(Order.order_time >= start, Order.order_time <= end).order_by(Order.order_time.desc()).all()

    ist = pytz_timezone('Asia/Kolkata')
    for order in orders:
        order.order_time = order.order_time.replace(tzinfo=timezone.utc).astimezone(ist)

    return render_template('admin_orders_week_month.html', orders=orders, title="This Month's Orders")


@app.route('/admin/reviews')
def admin_reviews():
    if 'user_type' not in session or session['user_type'] != 'admin':
        flash("Unauthorized access!", "danger")
        return redirect(url_for('login'))

    reviews = Review.query.order_by(Review.timestamp.desc()).all()
    review_data = []

    for review in reviews:
        order = Order.query.get(review.order_id)
        customer = Customer.query.get(review.customer_id)
        review_data.append({
            'id': review.id,
            'order_id': review.order_id,
            'customer_name': customer.name if customer else "Unknown",
            'comment': review.comment,
            'rating': review.rating,
            'timestamp': review.timestamp,
        })

    return render_template('admin_reviews.html', reviews=review_data)


@app.route('/admin/review/<int:review_id>/delete', methods=['POST'])
def delete_review(review_id):
    review = Review.query.get_or_404(review_id)
    db.session.delete(review)
    db.session.commit()
    flash('Review deleted successfully!', 'success')
    return redirect(url_for('admin_reviews'))



@app.route("/invoice/<int:order_id>")
def view_invoice(order_id):
    order = Order.query.get_or_404(order_id)
    items_with_details = []
    total = 0

    # Convert UTC to IST
    ist = pytz_timezone('Asia/Kolkata')
    local_time = order.order_time.replace(tzinfo=timezone.utc).astimezone(ist)

    for item in order.items:
        detail = {
            'name': item.menu_item.name,
            'quantity': item.quantity,
            'price': item.menu_item.price,
            'total': item.menu_item.price * item.quantity
        }
        items_with_details.append(detail)
        total += detail['total']

    return render_template("invoice.html", order=order, items=items_with_details, total_amount=total, local_time=local_time)

@app.route('/admin/order/<int:order_id>/mark_paid', methods=['POST'])
def mark_order_paid(order_id):
    order = Order.query.get_or_404(order_id)

    # Only mark if there's no payment already
    existing_payment = Payment.query.filter_by(order_id=order.id).first()
    if not existing_payment:
        payment = Payment(
            order_id=order.id,
            customer_id=order.customer_id,
            amount=sum(item.menu_item.price * item.quantity for item in order.items),
            method="Marked as Paid by Admin",
            status="Success"
        )
        db.session.add(payment)
        db.session.commit()
        flash(f"Order #{order.id} marked as paid.", "success")
    else:
        flash(f"Order #{order.id} is already marked as paid.", "info")

    return redirect(url_for('admin_orders'))

@app.route('/order/<int:order_id>/track')
def track_order(order_id):
    order = Order.query.get_or_404(order_id)

    # Convert to IST
    ist = pytz_timezone('Asia/Kolkata')
    order.order_time = order.order_time.replace(tzinfo=timezone.utc).astimezone(ist)

    

    return render_template('track_order.html', order=order)
