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

customer_bp = Blueprint('customer', __name__)



@customer_bp.route("/customer")
@role_required("customer", "admin")
def customer():
    user_lat = request.args.get("lat")
    user_lng = request.args.get("lng")

    conn = get_db_conn()
    cursor = conn.cursor()
    
    # Fetch all products to sort them by distance
    cursor.execute("SELECT * FROM products")
    rows = cursor.fetchall()

    # Fetch reviews to compute average ratings
    cursor.execute("SELECT seller_username, product_name, rating FROM reviews")
    reviews = cursor.fetchall()
    conn.close()

    # Precompute seller stats
    seller_stats = {}
    for r in reviews:
        seller = r.get("seller_username")
        if not seller: continue
        if seller not in seller_stats:
            seller_stats[seller] = {"total_rating": 0, "count": 0}
        seller_stats[seller]["total_rating"] += r.get("rating", 5)
        seller_stats[seller]["count"] += 1

    trusted_sellers = set()
    for seller, stats in seller_stats.items():
        if stats["count"] >= 3 and (stats["total_rating"] / stats["count"]) >= 4.0:
            trusted_sellers.add(seller)

    # Product ratings
    product_stats = {}
    for r in reviews:
        p_name = r.get("product_name")
        if not p_name: continue
        if p_name not in product_stats:
            product_stats[p_name] = {"total": 0, "count": 0}
        product_stats[p_name]["total"] += r.get("rating", 5)
        product_stats[p_name]["count"] += 1

    products = [dict(r) for r in rows]
    for p in products:
        p["is_trusted"] = p.get("seller_username") in trusted_sellers
        p_name = p.get("product_name")
        if p_name in product_stats:
            p["avg_rating"] = round(product_stats[p_name]["total"] / product_stats[p_name]["count"], 1)
        else:
            p["avg_rating"] = 5.0 # default if no reviews

    if user_lat and user_lng:
        try:
            u_lat = float(user_lat)
            u_lng = float(user_lng)
            for p in products:
                if p.get("latitude") and p.get("longitude"):
                    p["distance_km"] = round(haversine_km(u_lat, u_lng, p["latitude"], p["longitude"]), 2)
                else:
                    p["distance_km"] = 9999
            
            # Sort by distance
            products.sort(key=lambda x: x.get("distance_km", 9999))
        except (ValueError, TypeError):
            pass
    else:
        # Default sort by ID if no location
        products.sort(key=lambda x: x["id"], reverse=True)

    return render_template(
        "customer.html",
        products=products[:30] # Show top 30
    )

@customer_bp.route("/search", methods=["GET", "POST"])
@role_required("customer", "admin")
def search():
    products = []
    search_term = ""
    user_lat = request.values.get("lat")
    user_lng = request.values.get("lng")

    if request.method == "POST":
        search_term = request.form.get("search", "").strip()
    else:
        search_term = request.args.get("search", "").strip()

    if search_term:
        conn = get_db_conn()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT * FROM products
        WHERE lower(product_name) LIKE ?
        OR lower(shop_name) LIKE ?
        OR lower(location) LIKE ?
        """, (f'%{search_term.lower()}%', f'%{search_term.lower()}%', f'%{search_term.lower()}%'))

        rows = cursor.fetchall()
        conn.close()

        products = [dict(r) for r in rows]

        if user_lat and user_lng:
            try:
                u_lat = float(user_lat)
                u_lng = float(user_lng)
                for p in products:
                    if p.get("latitude") and p.get("longitude"):
                        p["distance_km"] = round(haversine_km(u_lat, u_lng, p["latitude"], p["longitude"]), 2)
                    else:
                        p["distance_km"] = 9999
                
                products.sort(key=lambda x: x.get("distance_km", 9999))
            except (ValueError, TypeError):
                pass
    else:
        return redirect("/customer")

    return render_template(
        "customer.html",
        products=products,
        search_term=search_term
    )

@customer_bp.route("/place_order", methods=["POST"])
@role_required("customer", "admin")
def place_order():

    customer_name = session.get("user")

    product_name = request.form.get("product_name")
    customer_phone = request.form.get("phone")
    address = request.form.get("address")
    payment = request.form.get("payment")

    price = request.form.get("price", "0")
    product_id = request.form.get("product_id")

    product_image = request.form.get("product_image", "")
    rider_name, rider_phone = assign_delivery_rider()
    delivery_otp = generate_delivery_otp()

    try:
        conn = get_db_conn()
        # conn.row_factory handled in get_db_conn()
        cursor = conn.cursor()

        seller_username = ""
        if product_id:
            cursor.execute("SELECT seller_username FROM products WHERE id=?", (product_id,))
            prod = cursor.fetchone()
            if prod and prod["seller_username"]:
                seller_username = prod["seller_username"]

        cursor.execute("""
        INSERT INTO orders(
            customer_name,
            customer_phone,
            product_name,
            price,
            product_image,
            address,
            payment_method,
            status,
            rider_name,
            rider_phone,
            delivery_otp,
            otp_verified,
            created_at,
            seller_username
        )
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            customer_name,
            customer_phone,
            product_name,
            price,
            product_image,
            address,
            payment,
            "Order Confirmed",
            rider_name,
            rider_phone,
            delivery_otp,
            "No",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            seller_username
        ))

        conn.commit()
        order_id = cursor.lastrowid
        conn.close()

        return render_template(
            "success.html",
            order_id=order_id,
            delivery_otp=delivery_otp,
            rider_name=rider_name
        )
    except Exception as e:
        if 'conn' in locals(): conn.close()
        return f"Database Error: {str(e)}", 500

@customer_bp.route("/online_payment/<int:product_id>", methods=["POST"])
@role_required("customer", "admin")
def online_payment(product_id):
    customer_name = request.form.get("customer_name")
    customer_phone = request.form.get("customer_phone")
    address = request.form.get("customer_address")
    
    conn = get_db_conn()
    # conn.row_factory handled in get_db_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE id=?", (product_id,))
    product = cursor.fetchone()
    
    if not product:
        conn.close()
        return "Product not found", 404
        
    rider_name, rider_phone = assign_delivery_rider()
    delivery_otp = generate_delivery_otp()
    
    cursor.execute("""
    INSERT INTO orders(customer_name, customer_phone, product_name, price, product_image, address, payment_method, status, rider_name, rider_phone, delivery_otp, otp_verified, created_at, seller_username)
    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        customer_name, customer_phone, product["product_name"], product["price"], product["product_image"],
        address, "Online Paid", "Order Confirmed", rider_name, rider_phone, delivery_otp, "No",
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"), product["seller_username"]
    ))
    conn.commit()
    order_id = cursor.lastrowid
    conn.close()
    
    return render_template("success.html", order_id=order_id, delivery_otp=delivery_otp, rider_name=rider_name)

@customer_bp.route("/cash_on_delivery/<int:product_id>", methods=["POST"])
@role_required("customer", "admin")
def cash_on_delivery(product_id):
    customer_name = request.form.get("customer_name")
    customer_phone = request.form.get("customer_phone")
    address = request.form.get("customer_address")
    
    conn = get_db_conn()
    # conn.row_factory handled in get_db_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE id=?", (product_id,))
    product = cursor.fetchone()
    
    if not product:
        conn.close()
        return "Product not found", 404
        
    rider_name, rider_phone = assign_delivery_rider()
    delivery_otp = generate_delivery_otp()
    
    cursor.execute("""
    INSERT INTO orders(customer_name, customer_phone, product_name, price, product_image, address, payment_method, status, rider_name, rider_phone, delivery_otp, otp_verified, created_at, seller_username)
    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        customer_name, customer_phone, product["product_name"], product["price"], product["product_image"],
        address, "Cash on Delivery", "Order Confirmed", rider_name, rider_phone, delivery_otp, "No",
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"), product["seller_username"]
    ))
    conn.commit()
    order_id = cursor.lastrowid
    conn.close()
    
    return render_template("success.html", order_id=order_id, delivery_otp=delivery_otp, rider_name=rider_name)

@customer_bp.route("/track/<int:order_id>")
def track_order(order_id):

    conn = get_db_conn()
    # conn.row_factory handled in get_db_conn()

    cursor = conn.cursor()

    cursor.execute("""
    SELECT * FROM orders
    WHERE id=?
    """, (order_id,))

    order = cursor.fetchone()

    if order is None:
        conn.close()
        return "Order not found", 404

    # Compute this customer's personal order number (1st, 2nd, 3rd...)
    customer_name = order["customer_name"]
    cursor.execute("""
    SELECT COUNT(*) FROM orders
    WHERE customer_name=? AND id <= ?
    """, (customer_name, order_id))
    customer_order_number = cursor.fetchone()[0]

    conn.close()

    # Ordinal suffix: 1st, 2nd, 3rd, 4th...
    def ordinal(n):
        if 11 <= (n % 100) <= 13:
            return f"{n}th"
        return {1: f"{n}st", 2: f"{n}nd", 3: f"{n}rd"}.get(n % 10, f"{n}th")

    return render_template(
        "track.html",
        order_id=order_id,
        order_label=ordinal(customer_order_number),
        status=order["status"],
        order=order
    )

@customer_bp.route("/track_status/<int:order_id>")
def track_status(order_id):

    conn = get_db_conn()
    # conn.row_factory handled in get_db_conn()

    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, customer_name, product_name, price, address, payment_method, status,
           rider_name, rider_phone, delivery_otp, otp_verified
    FROM orders
    WHERE id=?
    """, (order_id,))

    order = cursor.fetchone()

    conn.close()

    if order is None:
        return {"found": False}, 404

    # Security: only show OTP to the order owner (logged-in customer)
    current_user = session.get("user")
    is_owner = current_user and (current_user == order["customer_name"])

    return {
        "found": True,
        "order": {
            "id": order["id"],
            "customer_name": order["customer_name"] or "Guest",
            "product_name": order["product_name"] or "Product",
            "price": order["price"] or "0",
            "address": order["address"] or "Customer location",
            "payment_method": order["payment_method"] or "Payment",
            "status": order["status"] or "Order Confirmed",
            "rider_name": order["rider_name"] or "Assigned Rider",
            # Mask rider phone for non-owners
            "rider_phone": (order["rider_phone"] or "+91 98765 12000") if is_owner else "***",
            # SECURITY: Never expose OTP to non-owners
            "delivery_otp": (order["delivery_otp"] or "000000") if is_owner else "hidden",
            "otp_verified": order["otp_verified"] or "No",
        }
    }

@customer_bp.route("/leave_review/<int:order_id>")
@role_required("customer")
def leave_review(order_id):
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE id=? AND customer_name=?", (order_id, session.get("user")))
    order = cursor.fetchone()
    conn.close()

    if not order:
        return "Order not found or unauthorized", 404

    return render_template("leave_review.html", order=order)

@customer_bp.route("/submit_review/<int:order_id>", methods=["POST"])
@role_required("customer")
def submit_review(order_id):
    rating = request.form.get("rating", 5, type=int)
    review_text = request.form.get("review_text", "")
    customer_name = session.get("user")

    conn = get_db_conn()
    cursor = conn.cursor()

    # Verify order belongs to customer
    cursor.execute("SELECT * FROM orders WHERE id=? AND customer_name=?", (order_id, customer_name))
    order = cursor.fetchone()
    
    if not order:
        conn.close()
        return "Order not found", 404

    # Check if already reviewed
    cursor.execute("SELECT * FROM reviews WHERE order_id=?", (order_id,))
    existing = cursor.fetchone()

    if existing:
        conn.close()
        flash("You have already reviewed this order.")
        return redirect("/customer")

    cursor.execute("""
    INSERT INTO reviews (order_id, customer_name, product_name, seller_username, rating, review_text, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        order_id,
        customer_name,
        order["product_name"],
        order["seller_username"],
        rating,
        review_text,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()

    flash("Review submitted successfully! Thank you.")
    return redirect("/customer")

@customer_bp.route("/buy")
@role_required("customer", "admin")
def buy():

    product_id = request.args.get("product_id")
    product_name = request.args.get("product_name")
    price = request.args.get("price")
    product_image = request.args.get("product_image")

    return render_template(
        "buy.html",
        product_id=product_id,
        product_name=product_name,
        price=price,
        product_image=product_image
    )

@customer_bp.route("/cart")
@role_required("customer", "admin")
def view_cart():
    customer = session.get("user", "Guest")
    conn = get_db_conn()
    # conn.row_factory handled in get_db_conn()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT * FROM cart WHERE customer_name=? ORDER BY id ASC
    """, (customer,))
    items = cursor.fetchall()
    conn.close()

    total = sum(
        float(item["price"] or 0) * int(item["quantity"] or 1)
        for item in items
    )

    return render_template("cart.html", items=items, total=total, customer=customer)

@customer_bp.route("/add_to_cart", methods=["POST"])
@role_required("customer", "admin")
def add_to_cart():
    customer = session.get("user", "Guest")
    product_id    = request.form.get("product_id", "")
    product_name  = request.form.get("product_name", "")
    price         = request.form.get("price", "0")
    product_image = request.form.get("product_image", "")
    shop_name     = request.form.get("shop_name", "")
    unit          = request.form.get("unit", "unit")

    conn = get_db_conn()
    # conn.row_factory handled in get_db_conn()
    cursor = conn.cursor()

    # If already in cart, increment quantity
    cursor.execute("""
    SELECT id, quantity FROM cart
    WHERE customer_name=? AND product_id=?
    """, (customer, product_id))
    existing = cursor.fetchone()

    if existing:
        cursor.execute("""
        UPDATE cart SET quantity=? WHERE id=?
        """, (existing["quantity"] + 1, existing["id"]))
        flash(f"'{product_name}' quantity updated in cart.")
    else:
        cursor.execute("""
        INSERT INTO cart(customer_name, product_id, product_name, price, product_image, shop_name, quantity, unit, added_at)
        VALUES(?,?,?,?,?,?,?,?,?)
        """, (
            customer, product_id, product_name, price,
            product_image, shop_name, 1, unit,
            datetime.now().strftime("%d %b %Y, %I:%M %p")
        ))
        flash(f"'{product_name}' added to cart!")

    conn.commit()
    conn.close()

    return redirect(request.referrer or "/home")

@customer_bp.route("/remove_from_cart/<int:item_id>", methods=["POST"])
@role_required("customer", "admin")
def remove_from_cart(item_id):
    customer = session.get("user", "Guest")
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cart WHERE id=? AND customer_name=?", (item_id, customer))
    conn.commit()
    conn.close()
    flash("Item removed from cart.")
    return redirect("/cart")

@customer_bp.route("/update_cart/<int:item_id>", methods=["POST"])
@role_required("customer", "admin")
def update_cart(item_id):
    customer = session.get("user", "Guest")
    qty = int(request.form.get("quantity", 1))
    if qty < 1:
        qty = 1

    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE cart SET quantity=? WHERE id=? AND customer_name=?
    """, (qty, item_id, customer))
    conn.commit()
    conn.close()
    return redirect("/cart")

@customer_bp.route("/checkout", methods=["POST"])
@role_required("customer", "admin")
def checkout():
    customer = session.get("user", "Guest")
    address  = request.form.get("address", "")
    payment  = request.form.get("payment", "Cash on Delivery")

    if not address.strip():
        flash("Please enter a delivery address.")
        return redirect("/cart")

    try:
        conn = get_db_conn()
        # conn.row_factory handled in get_db_conn()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM cart WHERE customer_name=?", (customer,))
        items = cursor.fetchall()

        if not items:
            flash("Your cart is empty.")
            conn.close()
            return redirect("/cart")

        order_ids = []
        for item in items:
            rider_name, rider_phone = assign_delivery_rider()
            delivery_otp = generate_delivery_otp()

            cursor.execute("""
            INSERT INTO orders(
                customer_name, product_name, price, product_image,
                address, payment_method, status,
                rider_name, rider_phone, delivery_otp, otp_verified, created_at
            )
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                customer,
                item["product_name"],
                str(float(item["price"] or 0) * int(item["quantity"] or 1)),
                item["product_image"],
                address,
                payment,
                "Order Confirmed",
                rider_name,
                rider_phone,
                delivery_otp,
                "No",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            order_ids.append(cursor.lastrowid)

        # Clear cart after successful checkout
        cursor.execute("DELETE FROM cart WHERE customer_name=?", (customer,))
        conn.commit()
        conn.close()

        return render_template(
            "checkout_success.html",
            order_ids=order_ids,
            item_count=len(items),
            address=address,
            payment=payment,
        )
    except Exception as e:
        if 'conn' in locals(): conn.close()
        return f"Checkout Database Error: {str(e)}", 500

@customer_bp.route("/api/nearby_products")
def api_nearby_products():
    """Return JSON list of products sorted by distance from the given lat/lng.
    Query params: lat, lng, q (optional search term), radius_km (default 15)
    """
    try:
        user_lat = float(request.args.get("lat", 0))
        user_lng = float(request.args.get("lng", 0))
    except (TypeError, ValueError):
        return {"error": "Invalid lat/lng"}, 400

    radius_km = float(request.args.get("radius_km", 15))
    search_q  = request.args.get("q", "").strip()

    conn = get_db_conn()
    # conn.row_factory handled in get_db_conn()
    cursor = conn.cursor()

    if search_q:
        cursor.execute("""
        SELECT id, shop_name, location, product_name, price, stock,
               product_image, shop_image, latitude, longitude
        FROM products
        WHERE lower(product_name) LIKE ?
        AND latitude IS NOT NULL AND latitude != ''
        AND longitude IS NOT NULL AND longitude != ''
        """, (f"%{search_q.lower()}%",))
    else:
        cursor.execute("""
        SELECT id, shop_name, location, product_name, price, stock,
               product_image, shop_image, latitude, longitude
        FROM products
        WHERE latitude IS NOT NULL AND latitude != ''
        AND longitude IS NOT NULL AND longitude != ''
        """)

    rows = cursor.fetchall()
    conn.close()

    results = []
    for row in rows:
        dist = haversine_km(user_lat, user_lng, row["latitude"], row["longitude"])
        if dist <= radius_km:
            results.append({
                "id":            row["id"],
                "shop_name":     row["shop_name"] or "",
                "location":      row["location"] or "",
                "product_name":  row["product_name"] or "",
                "price":         row["price"] or "0",
                "stock":         row["stock"] or "",
                "product_image": row["product_image"] or "",
                "shop_image":    row["shop_image"] or "",
                "lat":           row["latitude"],
                "lng":           row["longitude"],
                "distance_km":   round(dist, 2),
            })

    results.sort(key=lambda x: x["distance_km"])
    return {"products": results, "count": len(results)}

@customer_bp.route("/api/products")
def api_all_products():
    """Return all products as JSON for mobile app."""
    conn = get_db_conn()
    # conn.row_factory handled in get_db_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    
    products = []
    for r in rows:
        img_url = r["product_image"]
        if img_url and not img_url.startswith("http"):
            img_url = f"/static/uploads/{img_url}"
        elif not img_url:
            img_url = "assets/shop.png"

        products.append({
            "id": r["id"],
            "shopName": r["shop_name"],
            "location": r["location"],
            "productName": r["product_name"],
            "price": float(r["price"] or 0),
            "stock": r["stock"],
            "image": img_url,
            "latitude": r["latitude"],
            "longitude": r["longitude"],
            "unit": r["unit"] or "unit"
        })
    return {"products": products}

@customer_bp.route("/api/orders")
@role_required("customer", "seller", "admin")
def api_orders():
    """Return orders for current user as JSON."""
    user = session.get("user")
    role = session.get("role")
    
    conn = get_db_conn()
    # conn.row_factory handled in get_db_conn()
    cursor = conn.cursor()
    
    if role == "seller":
        # Sellers only see orders for their own products (filtered by seller_username)
        cursor.execute("SELECT * FROM orders WHERE seller_username=? ORDER BY id DESC", (user,))
    else:
        cursor.execute("SELECT * FROM orders WHERE customer_name=? ORDER BY id DESC", (user,))
        
    rows = cursor.fetchall()
    conn.close()
    
    orders = []
    for r in rows:
        orders.append({
            "id": r["id"],
            "productName": r["product_name"],
            "price": float(r["price"] or 0),
            "customerName": r["customer_name"],
            "customerPhone": r["customer_phone"],
            "address": r["address"],
            "paymentMethod": r["payment_method"],
            "status": r["status"],
            "riderName": r["rider_name"],
            "riderPhone": r["rider_phone"],
            "deliveryOtp": r["delivery_otp"],
            "otpVerified": r["otp_verified"],
            "createdAt": r["created_at"]
        })
    return {"orders": orders}


@customer_bp.route("/api/product_reviews")
def api_product_reviews():
    """Return reviews for a product by name."""
    product_name = request.args.get("product", "")
    conn = get_db_conn()
    # conn.row_factory handled in get_db_conn()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT customer_name, rating, review_text, created_at
    FROM reviews WHERE lower(product_name) LIKE ?
    ORDER BY id DESC LIMIT 20
    """, (f"%{product_name.lower()}%",))
    reviews = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return {"reviews": reviews}