from flask import Blueprint, render_template, request, redirect, session, flash, send_from_directory, render_template_string
import json, os, secrets
from datetime import datetime, timedelta
from werkzeug.security import check_password_hash, generate_password_hash

from backend.app import *
from backend.utils import *
from backend.app_factory import app
import urllib.request
import urllib.parse
import urllib.error
import base64

seller_bp = Blueprint('seller', __name__)



@seller_bp.route("/shopkeeper")
@role_required("seller")
def shopkeeper():
    return render_template("shopkeeper.html")

@seller_bp.route("/add_product", methods=["POST"])
@role_required("seller")
def add_product():

    seller_username = session.get("user")
    shop_names = request.form.getlist("shop_name")
    locations = request.form.getlist("location")
    product_names = request.form.getlist("product_name")
    prices = request.form.getlist("price")
    stocks = request.form.getlist("stock")
    units = request.form.getlist("unit")
    latitudes = request.form.getlist("latitude")
    longitudes = request.form.getlist("longitude")

    product_images = request.files.getlist("product_image")
    shop_images = request.files.getlist("shop_image")

    product_rows = [
        i for i, name in enumerate(product_names)
        if name.strip()
    ]
    total_products = len(product_rows)

    if not total_products:
        return "Please enter at least one product.", 400

    if not shop_names or not shop_names[0].strip():
        return "Shop name is required.", 400

    if not locations or not locations[0].strip():
        return "Shop location is required.", 400

    if not shop_images or not shop_images[0] or not shop_images[0].filename:
        return "Shop image is required.", 400
    if not allowed_file(shop_images[0].filename):
        return "Invalid shop image format.", 400

    if len(prices) < len(product_names) or len(stocks) < len(product_names) or len(units) < len(product_names) or len(product_images) < len(product_names):
        return "Missing product details. Please fill all fields and upload both images.", 400

    conn = get_db_conn()
    cursor = conn.cursor()

    from werkzeug.utils import secure_filename
    
    # Helper to handle upload or local save
    def save_image(file_obj):
        url = upload_to_cloudinary(file_obj)
        if url:
            return url
        # Fallback to local storage
        if file_obj and file_obj.filename:
            filename = secure_filename(file_obj.filename)
            # Make sure it's unique enough
            import time
            unique_filename = f"{int(time.time())}_{filename}"
            file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
            file_obj.seek(0)
            file_obj.save(file_path)
            return unique_filename
        return None

    # Upload shop image once (since it's the same for all products in this batch)
    shop_image_url = save_image(shop_images[0])
    if not shop_image_url:
        conn.close()
        return "Failed to save shop image.", 500

    for i in product_rows:
        # UPLOAD PRODUCT IMAGE
        product_image_url = save_image(product_images[i])

        if not product_image_url:
            conn.close()
            return f"Failed to save image for {product_names[i]}.", 500

        cursor.execute("""
        INSERT INTO products(
            shop_name,
            location,
            product_name,
            price,
            stock,
            product_image,
            shop_image,
            latitude,
            longitude,
            unit,
            seller_username
        )
        VALUES(?,?,?,?,?,?,?,?,?,?,?)
        """, (
            shop_names[0],
            locations[0],
            product_names[i],
            prices[i],
            stocks[i],
            product_image_url,
            shop_image_url,
            latitudes[0] if latitudes else "",
            longitudes[0] if longitudes else "",
            units[i] if i < len(units) else "",
            seller_username
        ))

    conn.commit()
    conn.close()

    return redirect("/shopkeeper")

@seller_bp.route("/shopkeeper_dashboard")
@role_required("seller")
def shopkeeper_dashboard():

    conn = get_db_conn()
    # conn.row_factory handled in get_db_conn()

    cursor = conn.cursor()

    seller = session.get("user")
    cursor.execute("""
    SELECT * FROM products WHERE seller_username=?
    """, (seller,))

    products = cursor.fetchall()

    cursor.execute("""
    SELECT * FROM orders WHERE seller_username=?
    ORDER BY id DESC
    """, (seller,))

    orders = cursor.fetchall()

    conn.close()

    return render_template(
        "shopkeeper_dashboard.html",
        products=products,
        orders=orders
    )

@seller_bp.route("/api/shopkeeper/analytics")
@role_required("seller")
def shopkeeper_analytics():
    seller = session.get("user")
    conn = get_db_conn()
    cursor = conn.cursor()

    # Get recent orders for revenue chart
    cursor.execute("""
    SELECT created_at, price FROM orders
    WHERE seller_username=? AND status='Delivered'
    ORDER BY id ASC
    """, (seller,))
    orders = cursor.fetchall()

    revenue_data = {}
    for o in orders:
        date_str = o["created_at"].split()[0] if o["created_at"] else "Unknown"
        price_val = 0
        try:
            price_val = float(o["price"])
        except:
            pass
        revenue_data[date_str] = revenue_data.get(date_str, 0) + price_val

    # Get most popular products
    cursor.execute("""
    SELECT product_name, COUNT(*) as count FROM orders
    WHERE seller_username=?
    GROUP BY product_name
    ORDER BY count DESC
    LIMIT 5
    """, (seller,))
    popular = cursor.fetchall()
    
    conn.close()

    return {
        "revenue": {
            "labels": list(revenue_data.keys()),
            "data": list(revenue_data.values())
        },
        "popular": {
            "labels": [p["product_name"] for p in popular],
            "data": [p["count"] for p in popular]
        }
    }

@seller_bp.route("/export/orders/csv")
@role_required("seller")
def export_orders_csv():
    import csv
    from io import StringIO
    from flask import Response

    seller = session.get("user")
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT id, customer_name, product_name, price, status, created_at FROM orders WHERE seller_username=?", (seller,))
    orders = cursor.fetchall()
    conn.close()

    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(["Order ID", "Customer Name", "Product Name", "Price", "Status", "Date"])
    for o in orders:
        cw.writerow([o["id"], o["customer_name"], o["product_name"], o["price"], o["status"], o["created_at"]])

    return Response(
        si.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename=orders_{seller}.csv"}
    )

@seller_bp.route("/delete_product/<int:id>")
@role_required("seller")
def delete_product(id):

    seller = session.get("user")
    conn = get_db_conn()
    cursor = conn.cursor()

    # Only delete if the product belongs to this seller
    cursor.execute("""
    DELETE FROM products
    WHERE id=? AND seller_username=?
    """, (id, seller))

    conn.commit()
    conn.close()

    return redirect("/shopkeeper_dashboard")

@seller_bp.route("/edit_product/<int:id>")
def edit_product(id):

    conn = get_db_conn()
    # conn.row_factory handled in get_db_conn()

    cursor = conn.cursor()

    cursor.execute("""
    SELECT * FROM products
    WHERE id=?
    """, (id,))

    product = cursor.fetchone()

    conn.close()

    if product is None:
        return "Product not found", 404

    return render_template(
        "edit_product.html",
        product=product
    )

@seller_bp.route("/update_product/<int:id>", methods=["POST"])
@role_required("seller")
def update_product(id):

    seller = session.get("user")
    product_name = request.form.get("product_name")
    price = request.form.get("price")
    stock = request.form.get("stock")

    conn = get_db_conn()
    cursor = conn.cursor()

    # Only update if the product belongs to this seller
    cursor.execute("""
    UPDATE products
    SET product_name=?, price=?, stock=?
    WHERE id=? AND seller_username=?
    """, (
        product_name,
        price,
        stock,
        id,
        seller
    ))

    conn.commit()
    conn.close()

    return redirect("/shopkeeper_dashboard")

@seller_bp.route("/update_order_status/<int:id>", methods=["POST"])
def update_order_status(id):

    status = request.form["status"]

    if status == "Delivered":
        flash("Enter the customer's delivery OTP to mark this order as Delivered.")
        return redirect("/shopkeeper_dashboard")

    conn = get_db_conn()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE orders
    SET status=?
    WHERE id=?
    """, (
        status,
        id
    ))

    conn.commit()
    conn.close()

    return redirect("/shopkeeper_dashboard")

@seller_bp.route("/confirm_delivery/<int:id>", methods=["POST"])
def confirm_delivery(id):

    entered_otp = request.form.get("delivery_otp", "").strip()

    conn = get_db_conn()
    # conn.row_factory handled in get_db_conn()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT delivery_otp
    FROM orders
    WHERE id=?
    """, (id,))

    order = cursor.fetchone()

    if order is None:
        conn.close()
        flash("Order not found.")
        return redirect("/shopkeeper_dashboard")

    if entered_otp != (order["delivery_otp"] or ""):
        conn.close()
        flash("Wrong delivery OTP. Ask the customer for the 6-digit code shown on their tracking page.")
        return redirect("/shopkeeper_dashboard")

    cursor.execute("""
    UPDATE orders
    SET status=?, otp_verified=?
    WHERE id=?
    """, ("Delivered", "Yes", id))

    conn.commit()
    conn.close()

    flash("Delivery confirmed successfully with OTP.")
    return redirect("/shopkeeper_dashboard")

@seller_bp.route("/shopkeeper_orders")
@role_required("seller")
def shopkeeper_orders():

    conn = get_db_conn()
    # conn.row_factory handled in get_db_conn()

    cursor = conn.cursor()

    seller = session.get("user")
    cursor.execute("""
    SELECT * FROM orders WHERE seller_username=?
    ORDER BY id DESC
    """, (seller,))

    orders = cursor.fetchall()

    total_orders = len(orders)
    revenue = 0
    delivered = 0
    for order in orders:
        if order["status"] == "Delivered":
            delivered += 1
        try:
            if order["price"]:
                revenue += float(order["price"])
        except ValueError:
            pass

    conn.close()

    return render_template(
        "shopkeeper_orders.html",
        orders=orders,
        total_orders=total_orders,
        revenue=revenue,
        delivered=delivered
    )

@seller_bp.route("/update_status/<int:order_id>", methods=["POST"])
@role_required("seller")
def update_status(order_id):

    status = request.form["status"]

    if status == "Delivered":
        flash("Use the delivery OTP confirmation form to mark an order as Delivered.")
        return redirect("/shopkeeper_orders")

    conn = get_db_conn()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE orders
    SET status=?
    WHERE id=?
    """, (status, order_id))

    conn.commit()
    conn.close()

    return redirect("/shopkeeper_orders")

@seller_bp.route("/delete_order/<int:order_id>", methods=["POST"])
@role_required("seller")
def delete_order(order_id):

    conn = get_db_conn()
    cursor = conn.cursor()

    cursor.execute("""
    DELETE FROM orders
    WHERE id=?
    """, (order_id,))

    conn.commit()
    conn.close()

    return redirect("/shopkeeper_orders")

@seller_bp.route("/seller_dashboard")
@role_required("seller")
def seller_dashboard():

    conn = get_db_conn()
    # conn.row_factory handled in get_db_conn()

    cursor = conn.cursor()

    seller = session.get("user")
    
    # Fetch all products for the seller
    cursor.execute("SELECT * FROM products WHERE seller_username=? ORDER BY id DESC", (seller,))
    products = cursor.fetchall()
    
    total_products = len(products)

    # Fetch all orders for the seller
    cursor.execute("SELECT * FROM orders WHERE seller_username=? ORDER BY id DESC", (seller,))
    orders = cursor.fetchall()
    
    total_orders = len(orders)

    revenue = 0
    for order in orders:
        try:
            if order["price"]:
                revenue += float(order["price"])
        except ValueError:
            pass

    conn.close()

    return render_template(
        "shopkeeper_dashboard.html",
        products=products,
        orders=orders,
        total_products=total_products,
        total_orders=total_orders,
        revenue=revenue
    )

@seller_bp.route("/seller_products")
@role_required("seller")
def seller_products():

    conn = get_db_conn()
    # conn.row_factory handled in get_db_conn()

    cursor = conn.cursor()

    seller = session.get("user")
    cursor.execute("""
    SELECT * FROM products WHERE seller_username=?
    ORDER BY id DESC
    """, (seller,))

    products = cursor.fetchall()

    conn.close()

    return render_template(
        "shopkeeper_dashboard.html",
        products=products
    )

@seller_bp.route("/seller_orders")
@role_required("seller")
def seller_orders():
    return redirect("/shopkeeper_orders")

@seller_bp.route("/seller_maps")
@role_required("seller")
def seller_maps():

    conn = get_db_conn()
    # conn.row_factory handled in get_db_conn()

    cursor = conn.cursor()

    seller = session.get("user")
    cursor.execute("""
    SELECT * FROM products
    WHERE latitude IS NOT NULL
    AND latitude != ''
    AND longitude IS NOT NULL
    AND longitude != ''
    AND seller_username = ?
    ORDER BY id DESC
    """, (seller,))

    products = cursor.fetchall()

    conn.close()

    return render_template(
        "seller_maps.html",
        products=products
    )

@seller_bp.route("/seller_settings")
@role_required("seller")
def seller_settings():

    return '''
    <h1 style="font-family:Arial;text-align:center;margin-top:100px;">
    Seller Settings Coming Soon ⚙️
    </h1>
    '''

@seller_bp.route("/api/seller_stats")
@role_required("seller")
def seller_stats():
    # In a real app, we'd filter by the current seller's products
    # For this project, we'll show global stats for the dashboard demo
    conn = get_db_conn()
    # conn.row_factory handled in get_db_conn()
    cursor = conn.cursor()

    seller = session.get("user")
    # 1. Revenue over last 7 days
    revenue_data = []
    labels = []
    for i in range(6, -1, -1):
        day = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        cursor.execute("SELECT SUM(price) FROM orders WHERE created_at LIKE ? AND seller_username=?", (f"{day}%", seller))
        rev = cursor.fetchone()[0] or 0
        revenue_data.append(rev)
        labels.append((datetime.now() - timedelta(days=i)).strftime("%b %d"))

    # 2. Order Status Breakdown
    cursor.execute("SELECT status, COUNT(*) as count FROM orders WHERE seller_username=? GROUP BY status", (seller,))
    status_counts = {row["status"]: row["count"] for row in cursor.fetchall()}

    # 3. Top 5 Products
    cursor.execute("""
        SELECT product_name, COUNT(*) as count 
        FROM orders 
        WHERE seller_username=?
        GROUP BY product_name 
        ORDER BY count DESC 
        LIMIT 5
    """, (seller,))
    top_products = [{"name": row["product_name"], "count": row["count"]} for row in cursor.fetchall()]

    conn.close()

    return {
        "revenue": {
            "labels": labels,
            "data": revenue_data
        },
        "status": status_counts,
        "top_products": top_products
    }

@seller_bp.route("/api/seller_notifications")
@role_required("seller")
def seller_notifications():
    def event_stream():
        # Simple polling-based SSE for development
        last_order_id = 0
        while True:
            conn = get_db_conn()
            cursor = conn.cursor()
            seller = session.get("user")
            cursor.execute("SELECT MAX(id) FROM orders WHERE seller_username=?", (seller,))
            max_id = cursor.fetchone()[0] or 0
            conn.close()

            if max_id > last_order_id:
                if last_order_id != 0: # Skip first run
                    yield f"data: {json.dumps({'new_order': True, 'id': max_id})}\n\n"
                last_order_id = max_id
            
            import time
            time.sleep(3) # Check every 3 seconds

    from flask import Response
    return Response(event_stream(), mimetype="text/event-stream")