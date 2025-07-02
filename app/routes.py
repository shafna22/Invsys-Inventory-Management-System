from flask import Blueprint, render_template, request, redirect, url_for, flash,session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models import User, Inventory  # Ensure Inventory model exists
from flask import current_app as app
import os
from werkzeug.utils import secure_filename
from app.models import db, Order, Inventory,Invoice,Supply
from flask import flash
from datetime import datetime
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")  # Admin routes
main_bp = Blueprint("main", __name__)  # Main routes
staff_bp = Blueprint("staff", __name__, url_prefix="/staff")
# Create a blueprint for order routes
order_bp = Blueprint('order_bp', __name__)


@admin_bp.route('/')
@login_required
def admin_home():
    if current_user.role == "Admin":
        return render_template("admin/admin_dashboard.html")
    elif current_user.role == "Manager":
        return redirect(url_for('admin.manager_dashboard'))  # Redirect Manager to Manager Dashboard
    else:
        flash("Access denied!", "danger")
        return redirect(url_for('main.index'))
@admin_bp.route('/dashboard')
@login_required
def admin_dashboard():
    return render_template('admin/admin_dashboard.html')


# Home Page
@main_bp.route("/")
def index():
    return render_template("index.html")
# @admin_bp.route('/dashboard')
# def admin_dashboard():
#     return render_template('admin/admin_dashboard.html')
@admin_bp.route('/manager_dashboard')
@login_required
def manager_dashboard():
    if current_user.role != "Manager":
        flash("Access denied!", "danger")
        return redirect(url_for('main.index'))  # Redirect unauthorized users
    return render_template("admin/manager_dashboard.html")
@main_bp.route('/features')
def features():
    return render_template('features.html')

@main_bp.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        role = request.form.get('role', 'Staff')  # Default role is Staff
        contact_number = request.form.get('contact_number', '').strip()

        # Capture category if the user is a supplier
        category = request.form.get('category', '').strip() if role == 'Supplier' else None

        # Validate Required Fields
        if not username or not email or not password or not contact_number:
            flash('All fields are required!', 'danger')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return render_template('register.html')

        if role == 'Supplier' and not category:
            flash('Category is required for suppliers!', 'danger')
            return render_template('register.html')

        # Check if username or email is already registered
        existing_user = User.query.filter((User.email == email) | (User.username == username)).first()
        if existing_user:
            flash('Username or email already registered. Please login.', 'warning')
            return redirect(url_for('main.login'))

        # Hash the password
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        # Create and save the user
        new_user = User(
            username=username,
            email=email,
            password=hashed_password,
            role=role,
            contact_number=contact_number,
            category=category  # Store category if supplier
        )

        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('main.login'))

    return render_template('register.html')

# Login Route
@main_bp.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user, remember=True)
            flash(f'Welcome, {user.username}!', 'success')

            # Redirect based on user role
            if user.role == "Admin":
                return redirect(url_for('main.admin_dashboard'))
            elif user.role == "Manager":
                return redirect(url_for('main.manager_dashboard'))
            elif user.role == "Supplier":
                return redirect(url_for('main.supplier_dashboard'))
            else:
                return redirect(url_for('main.staff_dashboard'))
        else:
            flash('Invalid email or password!', 'danger')

    return render_template('login.html')

# Logout Route
@main_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'info')
    return redirect(url_for('main.index'))

# Admin Dashboard
@main_bp.route("/admin_dashboard")
@login_required
def admin_dashboard():
    if current_user.role != "Admin":
        flash("Access denied!", "danger")
        return redirect(url_for('main.index'))
    return render_template("admin/admin_dashboard.html", username=current_user.username)

# Manager Dashboard
@main_bp.route("/manager_dashboard")
@login_required
def manager_dashboard():
    if current_user.role not in ["Admin", "Manager"]:
        flash("Access denied!", "danger")
        return redirect(url_for('main.index'))
    return render_template("manager_dashboard.html", username=current_user.username)
# Staff Dashboard
@main_bp.route("/supplier_dashboard")
@login_required
def supplier_dashboard():
    return render_template("admin/supplier_dashboard.html", username=current_user.username)
# Staff Dashboard
@main_bp.route("/staff_dashboard")
@login_required
def staff_dashboard():
    return render_template("staff_dashboard.html", username=current_user.username)

# Manage Users (Admin Only)
@admin_bp.route("/manage_users")
@login_required
def manage_users():
    if current_user.role not in ["Admin","Manager"]:
        flash("Access denied!", "danger")
        return redirect(url_for("main.index"))
    
    users = User.query.all()
    return render_template("admin/manage_users.html", users=users)

# Delete a User (Admin Only)
@admin_bp.route("/delete_user/<int:user_id>", methods=["POST"])
@login_required
def delete_user(user_id):
    if current_user.role != "Admin":
        flash("Access denied!", "danger")
        return redirect(url_for("main.index"))

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash("User deleted successfully!", "success")
    return redirect(url_for("admin.manage_users"))

# Edit User Role (Admin Only)
@admin_bp.route("/edit_user/<int:user_id>", methods=["POST"])
@login_required
def edit_user(user_id):
    if current_user.role != "Admin":
        flash("Access denied!", "danger")
        return redirect(url_for("main.index"))

    user = User.query.get_or_404(user_id)
    new_role = request.form.get("role")

    if new_role not in ["Admin", "Manager", "Staff","Supplier"]:
        flash("Invalid role selection!", "danger")
    else:
        user.role = new_role
        db.session.commit()
        flash("User role updated successfully!", "success")

    return redirect(url_for("admin.manage_users"))
@admin_bp.route('/debug_user')
@login_required
def debug_user():
    return f"Current User: {current_user.username}, Role: {current_user.role}"

# Manage Inventory with Search and Filters
@admin_bp.route('/manage_inventory', methods=['GET'])
@login_required
def manage_inventory():
    if current_user.role not in ["Admin", "Manager", "Staff"]:
        flash("Access denied!", "danger")
        return redirect(url_for("main.index"))

    # Fetch search and filter parameters from request
    search_query = request.args.get('search', '').strip()
    category_filter = request.args.get('category', '')
    supplier_filter = request.args.get('supplier', '')
    availability_filter = request.args.get('availability', '')

    # Base query
    query = Inventory.query

    # Apply search filter
    if search_query:
        query = query.filter((Inventory.name.ilike(f"%{search_query}%")) | (Inventory.category.ilike(f"%{search_query}%")))

    # Apply category filter
    if category_filter:
        query = query.filter(Inventory.category == category_filter)

    # Apply supplier filter
    if supplier_filter:
        query = query.filter(Inventory.supplier == supplier_filter)

    # Apply availability filter
    if availability_filter:
        query = query.filter(Inventory.availability == availability_filter)

    # Execute query
    inventory_items = query.all()

    # Get unique values for dropdown filters
    categories = [item.category for item in Inventory.query.distinct(Inventory.category)]
    suppliers = [item.supplier for item in Inventory.query.distinct(Inventory.supplier)]
    availabilities = [item.availability for item in Inventory.query.distinct(Inventory.availability)]

    return render_template(
        'admin/manage_inventory.html',
        inventory_items=inventory_items,
        search_query=search_query,
        categories=categories,
        suppliers=suppliers,
        availabilities=availabilities
    )


# Add/Edit Inventory Form (Admin Only)
@admin_bp.route('/inventory_form', methods=['GET', 'POST'])
@login_required
def inventory_form():
    if current_user.role not in ["Admin","Manager"]:
        flash("Access denied!", "danger")
        return redirect(url_for("main.index"))

    if request.method == 'POST':
        return add_inventory()  # Calls the add_inventory function

    return render_template('admin/inventory_form.html')

# Add Inventory Item (Admin Only)
@admin_bp.route('/add_inventory', methods=['POST'])
@login_required
def add_inventory():
    if current_user.role not in ["Admin","Manager"]:
        flash("Access denied!", "danger")
        return redirect(url_for("main.index"))

    product_id = request.form.get('product_id')
    name = request.form.get('name')
    category = request.form.get('category')
    quantity = request.form.get('quantity')
    price = request.form.get('price')
    supplier = request.form.get('supplier')
    availability = request.form.get('availability')


      # Debugging
    print("Received Form Data:")
    print(f"Product ID: {product_id}, Name: {name}, Category: {category}, Quantity: {quantity}, Price: {price}, Supplier: {supplier}, Availability: {availability}")

    if not product_id or not name or not category or not quantity or not price or not supplier or not availability:
        flash("All fields are required!", "danger")
        return redirect(url_for('admin.inventory_form'))
    


    # Check if product_id already exists
    existing_item = Inventory.query.filter_by(product_id=product_id).first()
    if existing_item:
        flash("Product ID already exists. Please use a different ID.", "danger")
        return redirect(url_for('admin.inventory_form'))

    new_item = Inventory(
        product_id=product_id,
        name=name,
        category=category,
        quantity=quantity,
        price=price,
        supplier=supplier,
        availability=availability
    )

    try:
        db.session.add(new_item)
        db.session.commit()
        flash("Item added successfully!", "success")
        return redirect(url_for('admin.manage_inventory'))
    except Exception as e:
        db.session.rollback()
        flash(f"Error adding item: {str(e)}", "danger")

    return redirect(url_for('admin.manage_inventory'))  # Redirect back to the form

# Edit Inventory Item (Admin Only)
@admin_bp.route('/edit_inventory/<product_id>', methods=['GET', 'POST'])
@login_required
def edit_inventory(product_id):
    if current_user.role not in ["Admin","Manager"]:
        flash("Access denied!", "danger")
        return redirect(url_for("main.index"))
    print(f"Editing item: {product_id}")  # Debugging
    item = Inventory.query.filter_by(product_id=product_id).first()    # print(f"Found item: {item.name}")  # Debugging
    if request.method == 'POST':
        item.name = request.form.get('name')
        item.category = request.form.get('category')
        item.quantity = int(request.form.get('quantity',0))  # Ensure it's an integer
        item.price = float(request.form.get('price',0.0))  # Ensure it's a float
        item.supplier = request.form.get('supplier')
        item.availability = request.form.get('availability')

        try:
            db.session.commit()
            flash("Item updated successfully!", "success")
            return redirect(url_for('admin.manage_inventory'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating item: {str(e)}", "danger")

    return render_template('admin/inventory_form.html', item=item)  # FIXED TEMPLATE PATH


# Delete Inventory Item (Admin Only)
# Delete Inventory Item (Admin Only)
@admin_bp.route('/delete_inventory/<product_id>', methods=['POST'])
@login_required
def delete_inventory(product_id):
    if current_user.role != "Admin":  # Fix role check
        flash("Access denied!", "danger")
        return redirect(url_for("admin.manage_inventory"))

    item = Inventory.query.filter_by(product_id=product_id).first()

    if not item:  # Handle nonexistent items
        flash("Item not found!", "warning")
        return redirect(url_for("admin.manage_inventory"))

    try:
        db.session.delete(item)
        db.session.commit()
        flash("Item deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting item: {str(e)}", "danger")

    return redirect(url_for('admin.manage_inventory'))

#========================SETTINGS

@admin_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    return render_template('admin/profile.html', user=current_user)


# Assuming you have a directory set up for saving profile pictures
@admin_bp.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    # Get form data
    current_user.username = request.form.get('username')
    current_user.email = request.form.get('email')
    current_user.contact_number = request.form.get('contact')

    # ✅ Check if password is provided and update it
    password = request.form.get('password')
    if password:
        current_user.password = generate_password_hash(password)

    # ✅ Handle profile picture upload
    profile_picture = request.files.get('profile_picture')
    if profile_picture and allowed_file(profile_picture.filename):
        filename = secure_filename(profile_picture.filename)
        
        # ✅ Use app context to get the folder path
        upload_folder_path = os.path.join(app.config['PROFILE_PICTURE_FOLDER'])
        os.makedirs(upload_folder_path, exist_ok=True)

        # ✅ Construct file path and save the file
        profile_picture_path = os.path.join(upload_folder_path, filename)
        profile_picture.save(profile_picture_path)

        # ✅ Save relative path to database
        current_user.profile_picture = f'static/uploads/profile_pics/{filename}'
    else:
        # ✅ If no image uploaded and no existing picture, set default
        if not current_user.profile_picture:
            current_user.profile_picture = 'images/user.jpg'  # ✅ Set to default path

    # ✅ Save changes to database
    db.session.commit()

    flash("Profile updated successfully!", "success")
    
    # ✅ Role-based redirection
    if current_user.role == "Admin":
        return redirect(url_for('admin.admin_dashboard'))
    elif current_user.role == "Manager":
        return redirect(url_for('main.manager_dashboard'))
    elif current_user.role == "Staff":
        return redirect(url_for('main.staff_dashboard'))
    
    else:
        return redirect(url_for('main.index'))
   


@admin_bp.route('/my_profile')
@login_required
def my_profile():
    user = User.query.get(current_user.id)  # Get logged-in user's details
    return render_template('admin/my_profile.html', user=user)


#====================take order

@staff_bp.route("/take_order", methods=["GET", "POST"])
@login_required
def take_order():
    # Ensure only staff can access this route
    if current_user.role != "Staff":
        flash("Access Denied!", "danger")
        return redirect(url_for("main.index"))

    if request.method == "POST":
        product_id = request.form.get("product")
        quantity = request.form.get("quantity")
        payment_method = request.form.get("payment_method")
        notes = request.form.get("notes", "")

        # ✅ Validate required fields
        if not product_id or not quantity or not payment_method:
            flash("Please fill all required fields!", "warning")
            return redirect(url_for("staff.take_order"))

        # ✅ Ensure quantity is a valid positive number
        try:
            quantity = int(quantity)
            if quantity <= 0:
                flash("Quantity must be a positive number!", "warning")
                return redirect(url_for("staff.take_order"))
        except ValueError:
            flash("Invalid quantity entered!", "warning")
            return redirect(url_for("staff.take_order"))

        # ✅ Check if the product exists in the inventory
        product = Inventory.query.get(product_id)
        if not product:
            flash("Selected product not found!", "danger")
            return redirect(url_for("staff.take_order"))

        # ✅ Check if the requested quantity is available
        if quantity > product.quantity:
            flash(f"Only {product.quantity} units available in stock!", "warning")
            return redirect(url_for("staff.take_order"))

        # ✅ Save order to the database
        try:
            new_order = Order(
                staff_id=current_user.id,
                product_id=product_id,
                quantity=quantity,
                payment_method=payment_method,
                notes=notes,
                status="Pending",  # Waiting for admin approval
                created_at=datetime.utcnow()
            )
            db.session.add(new_order)

            # ✅ Reduce inventory quantity after order placement
           
            db.session.commit()

            flash("Order submitted successfully! Waiting for admin approval.", "success")
            return redirect(url_for("staff.order_status"))

        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {str(e)}", "danger")
            return redirect(url_for("staff.take_order"))

    # ✅ Load available products
    products = Inventory.query.all()
    return render_template("staff/take_order.html", products=products)


# ✅ Route for showing order status
@staff_bp.route("/order_status", methods=["GET"])
@login_required
def order_status():
    # Ensure only staff can access this route
    if current_user.role != "Staff":
        flash("Access Denied!", "danger")
        return redirect(url_for("main.index"))

    try:
        # ✅ Fetch orders placed by the current staff
        orders = Order.query.filter_by(staff_id=current_user.id).order_by(Order.created_at.desc()).all()
        return render_template("staff/order_status.html", orders=orders)
    except Exception as e:
        flash(f"An error occurred: {str(e)}", "danger")
        return redirect(url_for("main.index"))

# ✅ Route for showing order history (completed orders)
@staff_bp.route("/order_history", methods=["GET"])
@login_required
def order_history():
    # Ensure only staff can access this route
    if current_user.role != "Staff":
        flash("Access Denied!", "danger")
        return redirect(url_for("main.index"))

    try:
        # ✅ Fetch only completed orders by the current staff
        orders = Order.query.filter(
            Order.staff_id == current_user.id,
            Order.status == "Completed",
            Order.completed_at != None
        ).order_by(Order.completed_at.desc()).all()

        return render_template("staff/order_history.html", orders=orders)
    except Exception as e:
        flash(f"An error occurred: {str(e)}", "danger")
        return redirect(url_for("main.index"))
@admin_bp.route('/update_order_status/<int:order_id>', methods=['POST'])
@login_required
def update_order_status(order_id):
    if current_user.role not in ["Admin", "Manager"]:
        flash("Access denied!", "danger")
        return redirect(url_for('main.index'))
    
    order = Order.query.get_or_404(order_id)
    product = Inventory.query.get(order.product_id)
    
    action = request.form.get('action')

    if action == 'approve':
        if product and product.quantity >= order.quantity:
            product.quantity -= order.quantity
            order.status = "Completed"
            order.completed_at = datetime.utcnow()
            if product.quantity == 0:
                product.availability = "Out of Stock"  # ✅ Update availability if stock is zero
            db.session.commit()
            flash(f"Order {order.id} has been approved and stock updated.", "success")
        else:
            flash("Not enough stock available to approve this order.", "danger")
    
    elif action == 'reject':
        order.status = "Rejected"
        db.session.commit()
        flash(f"Order {order.id} has been rejected.", "warning")

    return redirect(url_for('admin.manage_orders'))
@admin_bp.route("/manage_orders", methods=["GET", "POST"])
@login_required
def manage_orders():
    if current_user.role not in ["Admin", "Manager"]:
        flash("Access denied!", "danger")
        return redirect(url_for('main.index'))
    
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template("admin/manage_orders.html", orders=orders)
# Route to show all completed orders
@admin_bp.route('/all_orders')
def all_orders():
    completed_orders = Order.query.filter_by(status="Completed").all()
    return render_template('admin/all_orders.html', orders=completed_orders)
# ✅ Route to complete an order and generate an invoice
@order_bp.route('/complete_order/<int:order_id>', methods=['POST'])
def complete_order(order_id):
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404

    if order.status == "Completed":
        return jsonify({"message": "Order already completed"}), 400

    # ✅ Mark order as completed
    order.status = "Completed"
    order.completed_at = datetime.utcnow()
    db.session.commit()

    # ✅ Generate the invoice
    invoice = order.generate_invoice()

    return jsonify({
        "message": "Order completed successfully",
        "invoice_id": invoice.id,
        "total_amount": invoice.total_amount,
        "invoice_date": invoice.invoice_date.isoformat()
    }), 200

@staff_bp.route('/invoice/<int:order_id>', methods=['GET'])
@login_required
def generate_invoice(order_id):
    order = Order.query.get_or_404(order_id)

    # ✅ Ensure the logged-in staff created the order
    if order.staff_id != current_user.id:
        flash("You are not authorized to view this invoice.", "danger")
        return redirect(url_for('staff.order_history'))

    # ✅ Fetch product and staff details
    product = Inventory.query.get(order.product_id)
    staff = User.query.get(order.staff_id)

    return render_template('staff/invoice.html', order=order, product=product, staff=staff)
#==================================================SUPPLY
# ✅ Manage Suppliers (View & Search)
@admin_bp.route("/manage_suppliers", methods=["GET"])
def manage_suppliers():
    search_query = request.args.get("search", "").strip()

    # Fetch only users who are suppliers
    query = User.query.filter_by(role="Supplier")

    if search_query:
        query = query.filter(
            (User.username.ilike(f"%{search_query}%")) |
            (User.category.ilike(f"%{search_query}%"))
        )

    suppliers = query.all()
    return render_template("admin/manage_suppliers.html", suppliers=suppliers, search_query=search_query)

@admin_bp.route('/admin/order_from_supplier/<int:supplier_id>', methods=['GET', 'POST'])
@login_required
def order_from_supplier(supplier_id):
    # Fetch the supplier by ID and check if the role is 'Supplier'
    supplier = User.query.filter_by(id=supplier_id, role="Supplier").first_or_404()

    if request.method == 'POST':
        # Get product details from the form
        product_id = request.form.get('product_id')
        quantity = request.form.get('quantity')
        cost_price = request.form.get('cost_price')

        # Debugging print statements
        print(f"Product ID: {product_id}")
        print(f"Quantity: {quantity}")
        print(f"Cost Price: {cost_price}")

        # Validation for product ID, quantity, and cost price
        if not product_id or not quantity.isdigit() or int(quantity) <= 0 or (cost_price and not cost_price.replace('.', '', 1).isdigit()):
            flash("Invalid product details!", "danger")
            return redirect(url_for('admin.order_from_supplier', supplier_id=supplier_id))

        # Fetch the product from the inventory to ensure it exists
        product = Inventory.query.get(product_id)
        if not product:
            flash("Product not found in inventory!", "danger")
            return redirect(url_for('admin.order_from_supplier', supplier_id=supplier_id))

        # Convert quantity to integer
        quantity = int(quantity)

        # Handle cost_price conversion
        if cost_price and cost_price.replace('.', '', 1).isdigit():
            cost_price = float(cost_price)
        else:
            # Handle invalid cost_price by setting a default value or raising an error
            cost_price = 0.0  # You can set a default or raise an error here

        # Calculate total cost
        total_cost = quantity * cost_price

        # Debugging print statements for the calculated total cost
        print(f"Total Cost: {total_cost}")

        # Create a new Supply entry
        new_supply = Supply(
            supplier_id=supplier.id,
            product_id=product.id,
            quantity=quantity,
            cost_price=cost_price,
            total_cost=total_cost
        )

        # Debugging: Check if new_supply is created properly
        print(f"New Supply Entry: {new_supply}")

        # Add the new supply entry to the database
        db.session.add(new_supply)

        # Commit the transaction to save it to the database
        try:
            db.session.commit()
            flash("Supply order placed successfully!", "success")
            return redirect(url_for('admin.manage_suppliers'))
        except Exception as e:
            # If there's an error with the commit, print the error
            print(f"Error committing the transaction: {e}")
            flash("There was an error placing the order. Please try again.", "danger")
            db.session.rollback()  # Rollback the session in case of an error
            return redirect(url_for('admin.order_from_supplier', supplier_id=supplier_id))

    # If the method is GET, fetch all products from the inventory
    products = Inventory.query.all()
    return render_template("admin/order_from_supplier.html", supplier=supplier, products=products)



@admin_bp.route("/manage_supplier", methods=["GET", "POST"])
@login_required
def manage_supplier():
    if current_user.role != "Supplier":
        flash("Unauthorized access!", "danger")
        return redirect(url_for("main.dashboard"))

    # Fetch supplies specific to the logged-in supplier
    supplies = Supply.query.filter_by(supplier_id=current_user.id).all()

    if request.method == "POST":
        supply_id = request.form.get("supply_id")
        new_status = request.form.get("status")

        # Validate the status
        valid_statuses = ["Pending", "Approved", "Rejected"]
        if new_status not in valid_statuses:
            flash("Invalid status selected!", "danger")
            return redirect(url_for("admin.manage_supplier"))

        supply = Supply.query.get(supply_id)
        if supply and supply.supplier_id == current_user.id:
            try:
                # Update the status and commit to the database
                supply.status = new_status
                db.session.commit()
                flash("Supply status updated!", "success")
            except Exception as e:
                db.session.rollback()
                flash(f"Error updating supply status: {e}", "danger")
        else:
            flash("Invalid supply order!", "danger")

        return redirect(url_for("admin.manage_supplier"))

    return render_template("admin/manage_supplier.html", supplies=supplies)


@admin_bp.route('/update_status/<int:supply_id>', methods=['POST'])
def update_status(supply_id):
    supply = Supply.query.get_or_404(supply_id)
    
    # Get the status from the form (assume it's a dropdown)
    new_status = request.form.get('status')
    
    if new_status in ['Pending', 'Approved', 'Rejected']:  # Validate status
        supply.status = new_status
        db.session.commit()
    
    return redirect(url_for('main.supplier_dashboard'))  # Redirect back to the dashboard or wherever you need


# ✅ Supplier Order Status (Admin View)
@admin_bp.route("/supplier_status")
@login_required
def supplier_status():
    supplies = Supply.query.all()  # Fetch all supply orders
    return render_template("admin/supplier_status.html", supplies=supplies)


# ✅ Confirm Supply Order (Before Invoice Generation)
@admin_bp.route("/confirm_order/<int:supply_id>", methods=["GET", "POST"])
@login_required
def confirm_order(supply_id):
    supply = Supply.query.get_or_404(supply_id)

    if supply.status == "Approved":
        return redirect(url_for("admin.supply_invoice", supply_id=supply.id))

    flash("Order must be approved before confirmation!", "warning")
    return redirect(url_for("admin.supplier_status"))



# ✅ Generate Supply Invoice
@admin_bp.route("/supply_invoice/<int:supply_id>")
@login_required
def supply_invoice(supply_id):
    supply = Supply.query.get_or_404(supply_id)
    
    # ✅ Fetch price per unit from Inventory based on supply.product_id
    inventory_item = Inventory.query.filter_by(product_id=supply.product_id).first()

    # ✅ Ensure inventory_item exists before accessing price
    price_per_unit = inventory_item.price if inventory_item else 0  
    total_price = price_per_unit * supply.quantity  # ✅ Calculate total price

    return render_template("admin/supply_invoice.html", 
                           supply=supply, 
                           price_per_unit=price_per_unit, 
                           total_price=total_price)



# ✅ Complete Supply Order & Update Inventory

@admin_bp.route("/complete_order/<int:supply_id>", methods=["POST"])
@login_required
def complete_order(supply_id):
    supply = Supply.query.get_or_404(supply_id)

    if supply.status != "Approved":
        flash("Only approved orders can be completed!", "warning")
        return redirect(url_for("admin.supplier_status"))

   # ✅ Change status from "Approved" to "Confirmed"
    supply.status = "Confirmed"

    db.session.commit()  # Save changes to database
    # ✅ Update inventory quantity
    inventory_item = Inventory.query.get(supply.product_id)

    if inventory_item:
        inventory_item.quantity += supply.quantity  # Increase stock
    else:
        # If product does not exist, create a new one
        inventory_item = Inventory(
            product_id=supply.product_id,
            name="Unknown Product",  # Placeholder (should be updated properly)
            category="Unknown",  # Placeholder
            quantity=supply.quantity,
            price=supply.cost_price  # Set purchase price as the default selling price
        )
        db.session.add(inventory_item)

    db.session.commit()
    flash("Inventory updated successfully!", "success")
    return redirect(url_for("admin.supplier_status"))

@admin_bp.route('/delivery_status')
@login_required
def delivery_status():
    # Fetch orders related to the logged-in supplier
    supplier_orders = Supply.query.filter_by(supplier_id=current_user.id).all()

    return render_template('admin/delivery_status.html', orders=supplier_orders)



#===================================================
import csv
import io
from flask import Response, render_template
from sqlalchemy.sql import func


@admin_bp.route('/view_report')
def view_report():
    total_products = Inventory.query.count()
    low_stock_count = Inventory.query.filter(Inventory.quantity < 10).count()
    total_orders = Order.query.filter_by(status='Completed').count()

    # ✅ Stock data for the Line Graph
    stock_data = {item.name: item.quantity for item in Inventory.query.all()}

    # ✅ Sales data for the Line Graph (Ensures zero sales for unsold products)
    sales_data = db.session.query(
        Inventory.name, 
        func.coalesce(func.sum(Order.quantity), 0)
    ).outerjoin(Order).group_by(Inventory.id).all()

    sales_dict = {name: sales for name, sales in sales_data}

    # ✅ Top Selling Product (Most sold item)
    top_product, top_sales = max(sales_data, key=lambda x: x[1], default=("None", 0))

    # ✅ User role count
    user_roles = dict(db.session.query(User.role, func.count(User.id)).group_by(User.role).all())

    return render_template('admin/view_report.html', 
                           total_products=total_products, 
                           low_stock_count=low_stock_count, 
                           total_orders=total_orders,
                           top_product=top_product, 
                           top_sales=top_sales,
                           stock_labels=list(stock_data.keys()), 
                           stock_data=list(stock_data.values()),
                           sales_labels=list(sales_dict.keys()), 
                           sales_data=list(sales_dict.values()),
                           user_roles=user_roles)


# ✅ CSV Download Route (Optimized)
@admin_bp.route('/download_report')
def download_report():
    orders = Order.query.all()

    # ✅ Store product names in a dictionary to avoid duplicate queries
    product_names = {item.id: item.name for item in Inventory.query.all()}

    # ✅ Generate CSV Data
    csv_data = [["Order ID", "Product", "Quantity", "Status", "Date"]]
    for order in orders:
        product_name = product_names.get(order.product_id, "Unknown")
        csv_data.append([order.id, product_name, order.quantity, order.status, order.created_at.strftime("%Y-%m-%d")])

    # ✅ Use io.StringIO() for writing CSV data
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerows(csv_data)
    
    # ✅ Create Flask Response
    response = Response(output.getvalue(), mimetype="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=inventory_report.csv"
    
    return response



#=================================ML

from .ml_sales_predictor import predict_next_week_sales

from sklearn.linear_model import LinearRegression
import numpy as np
import pandas as pd
from datetime import datetime
from flask import jsonify

@admin_bp.route('/sales_prediction')
@login_required
def sales_prediction():
    # Only admins or managers can access
    if current_user.role not in ["Admin", "Manager"]:
        flash("Access denied!", "danger")
        return redirect(url_for("main.index"))

    # Fetch all completed orders
    completed_orders = Order.query.filter_by(status='Completed').all()

    # Prepare data for each product
    product_data = {}

    for order in completed_orders:
        product = order.product
        date = order.created_at.date()
        qty = order.quantity

        if product not in product_data:
            product_data[product] = {}

        if date not in product_data[product]:
            product_data[product][date] = 0

        product_data[product][date] += qty

    # Predict future sales using Linear Regression
    prediction_results = {}

    for product, date_qty in product_data.items():
        # Convert dates to ordinal format
        dates = [pd.to_datetime(date).toordinal() for date in date_qty.keys()]
        quantities = list(date_qty.values())

        if len(dates) < 2:
            continue  # Not enough data to predict

        X = np.array(dates).reshape(-1, 1)
        y = np.array(quantities)

        model = LinearRegression()
        model.fit(X, y)

        # Predict sales for the next day
        next_day = max(dates) + 1
        predicted_qty = model.predict([[next_day]])[0]

        prediction_results[product.name] = round(predicted_qty)

    return render_template('admin/sales_prediction.html', predictions=prediction_results)


@admin_bp.route('/low_stock_forecast')
@login_required
def low_stock_forecast():
    if current_user.role not in ["Admin", "Manager"]:
        flash("Access denied!", "danger")
        return redirect(url_for("main.index"))

    from datetime import datetime, timedelta  # in case not already at top
    today = datetime.today().date()
    last_week = today - timedelta(days=7)

    recent_orders = Order.query.filter(
        Order.created_at >= last_week,
        Order.status == 'Completed'
    ).all()

    sales_data = {}

    for order in recent_orders:
        product = Inventory.query.get(order.product_id)
        if product:
            if product.id not in sales_data:
                sales_data[product.id] = 0
            sales_data[product.id] += order.quantity

    forecast = []

    products = Inventory.query.all()
    for product in products:
        stock = product.quantity
        total_sales = sales_data.get(product.id, 0)
        avg_daily_sales = total_sales / 7 if total_sales > 0 else 0

        if avg_daily_sales > 0:
            days_remaining = round(stock / avg_daily_sales, 1)
        else:
            days_remaining = "N/A"

        forecast.append({
            'product_name': product.name,
            'stock': stock,
            'avg_daily_sales': round(avg_daily_sales, 2),
            'days_remaining': days_remaining
        })

    return render_template('admin/low_stock_forecast.html', forecast=forecast)
