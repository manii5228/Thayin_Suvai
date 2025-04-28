# 🍴 Thyain Suvai - Restaurant Ordering System
Thyain Suvai is a full-featured web application designed to manage restaurant operations digitally.
Built using Flask (Python), Bootstrap 5, and SQLAlchemy, it supports both customer ordering and admin management — making restaurant workflows faster, smarter, and more user-friendly.

# ✨ Key Features
## Customer Side
🛒 Browse and order items from a dynamic menu

📦 Track orders in real-time (Order Status: Placed → Preparing → Delivered)

📝 Add special notes to dishes while ordering

💳 Select Dine-In (with table number) or Delivery (with address)

🧾 View detailed invoices after purchase

⭐ Submit reviews after order completion

## Admin Side
📋 Add, edit, delete, and manage menu items easily

📈 View all orders (filter by Today, This Month)

✅ Mark orders as Paid or Delivered manually

👩‍🍳 Manage customer reviews

📷 Update menu item images from the dashboard directly (no code needed)

## ⚙️ Technologies Used
Backend: Flask, SQLAlchemy

Frontend: Bootstrap 5, HTML5, CSS3, Jinja2

Database: SQLite

Others:

Dynamic form handling

Image uploads and updates

Responsive mobile-first design

Flash messaging system for actions

## 📂 Folder Structure
```
/static
    /uploads         --> Menu images uploaded dynamically
    /css             --> Styled CSS files for each page

/templates
    /admin_orders.html
    /customer_dashboard.html
    /track_order.html
    /login.html
    ... (other pages)

models.py             --> Database models
app.py                --> Main Flask application
forms.py              --> WTForms for login/register
```
## 🚀 How to Run
### Install required libraries:
```
pip install needs.txt
```
### Set up and initialise the database:
```
flask db init
flask db migrate
flask db upgrade
```
### Run the Flask app:

flask run
Visit http://localhost:5000 to use the system!

