from pathlib import Path

from flask import Flask, render_template, request, redirect, session, flash, send_from_directory
import base64
import sqlite3
import os
import re
import secrets
import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from functools import wraps
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = BASE_DIR / "frontend"
RELEASE_DIR = BASE_DIR / "release"
DATABASE_PATH = str(BASE_DIR / "database.db")
UPLOAD_FOLDER = str(FRONTEND_DIR / "static" / "uploads")

app = Flask(
    __name__,
    template_folder=str(FRONTEND_DIR / "templates"),
    static_folder=str(FRONTEND_DIR / "static"),
    static_url_path="/static",
)
app.secret_key = os.environ.get("NPF_SECRET_KEY", "nearbypricefinder")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
OTP_EXPIRY_MINUTES = 5
VALID_ROLES = {"customer", "seller", "admin"}
PUBLIC_ROLES = {"customer", "seller"}
OWNER_ADMIN_USERNAME = os.environ.get("NPF_ADMIN_USERNAME", "admin")
OWNER_ADMIN_PASSWORD = os.environ.get("NPF_ADMIN_PASSWORD", "admin@123")
DELIVERY_RIDERS = [
    ("Arjun Kumar", "+91 98765 12001"),
    ("Meera Singh", "+91 98765 12002"),
    ("Ravi Patel", "+91 98765 12003"),
    ("Ananya Rao", "+91 98765 12004"),
]

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ================= DATABASE =================

conn = sqlite3.connect(DATABASE_PATH)
cursor = conn.cursor()
# ================= CHAT TABLE =================

conn = sqlite3.connect(DATABASE_PATH)

cursor = conn.cursor()

# USERS TABLE

cursor.execute("""

CREATE TABLE IF NOT EXISTS users(

    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    email TEXT,
    password TEXT

)

""")

# PRODUCTS TABLE

cursor.execute("""

CREATE TABLE IF NOT EXISTS products(

    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name TEXT,
    price TEXT

)

""")

# ORDERS TABLE

cursor.execute("""

CREATE TABLE IF NOT EXISTS orders(

    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name TEXT,
    product_name TEXT

)

""")

# CHAT TABLE

cursor.execute("""

CREATE TABLE IF NOT EXISTS chats(

    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender TEXT,
    message TEXT,
    created_at TEXT

)

""")

# USERS TABLE

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password TEXT
)
""")

# PRODUCTS TABLE

cursor.execute("""
CREATE TABLE IF NOT EXISTS products(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shop_name TEXT,
    location TEXT,
    product_name TEXT,
    price TEXT,
    stock TEXT,
    product_image TEXT,
    shop_image TEXT,
    latitude TEXT,
    longitude TEXT
)
""")

for column_name in ("latitude", "longitude"):
    try:
        cursor.execute(f"ALTER TABLE products ADD COLUMN {column_name} TEXT")
    except sqlite3.OperationalError:
        pass

try:
    cursor.execute("ALTER TABLE chats ADD COLUMN created_at TEXT")
except sqlite3.OperationalError:
    pass

try:
    cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'customer'")
except sqlite3.OperationalError:
    pass

for column_name, column_definition in (
    ("rider_name", "TEXT"),
    ("rider_phone", "TEXT"),
    ("delivery_otp", "TEXT"),
    ("otp_verified", "TEXT DEFAULT 'No'"),
):
    try:
        cursor.execute(f"ALTER TABLE orders ADD COLUMN {column_name} {column_definition}")
    except sqlite3.OperationalError:
        pass

# ORDERS TABLE

cursor.execute("""
CREATE TABLE IF NOT EXISTS orders(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name TEXT,
    product_name TEXT,
    price TEXT,
    product_image TEXT,
    address TEXT,
    payment_method TEXT,
    status TEXT DEFAULT 'Order Confirmed'
)
""")

conn.commit()
conn.close()


def normalize_role(role):
    role = (role or "customer").strip().lower()
    return role if role in VALID_ROLES else "customer"


def normalize_public_role(role):
    role = (role or "customer").strip().lower()
    return role if role in PUBLIC_ROLES else "customer"


def is_owner_admin_login(username, password):
    return (
        secrets.compare_digest(username or "", OWNER_ADMIN_USERNAME)
        and secrets.compare_digest(password or "", OWNER_ADMIN_PASSWORD)
    )


def generate_delivery_otp():
    return f"{secrets.randbelow(900000) + 100000}"


def assign_delivery_rider(order_id=None):
    index = (order_id or secrets.randbelow(len(DELIVERY_RIDERS))) % len(DELIVERY_RIDERS)
    return DELIVERY_RIDERS[index]


def dashboard_for_role(role):
    role = normalize_role(role)
    if role == "seller":
        return "/shopkeeper_dashboard"
    if role == "admin":
        return "/admin"
    return "/home"


def label_for_role(role):
    role = normalize_role(role)
    if role == "seller":
        return "seller"
    if role == "admin":
        return "owner admin"
    return "customer"


def role_required(*roles):
    allowed_roles = {normalize_role(role) for role in roles}

    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            if not session.get("user"):
                return redirect("/")

            current_role = normalize_role(session.get("role"))

            if current_role == "admin" and session.get("is_owner_admin"):
                return view_func(*args, **kwargs)

            if "admin" in allowed_roles:
                flash("Owner admin access is required for that panel.")
                return redirect(dashboard_for_role(current_role))

            if current_role in allowed_roles:
                return view_func(*args, **kwargs)

            needed_role = label_for_role(next(iter(allowed_roles), "customer"))
            flash(f"Please login with a {needed_role} account to open that panel.")
            return redirect(dashboard_for_role(current_role))

        return wrapped

    return decorator


@app.context_processor
def inject_current_account():
    return {
        "current_user": session.get("user", "Guest"),
        "current_role": normalize_role(session.get("role")),
        "is_owner_admin": bool(session.get("is_owner_admin")),
    }


@app.route("/manifest.json")
def web_manifest():
    return send_from_directory(app.static_folder, "manifest.json", mimetype="application/manifest+json")


@app.route("/service-worker.js")
def service_worker():
    return send_from_directory(app.static_folder, "service-worker.js", mimetype="application/javascript")


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(app.static_folder, "app-icon.svg", mimetype="image/svg+xml")


@app.route("/download_app")
def download_app():
    windows_zip = RELEASE_DIR / "NearbyPriceFinder-Windows.zip"
    android_apk = RELEASE_DIR / "NearbyPriceFinder-Android.apk"
    return render_template(
        "download_app.html",
        windows_zip_exists=windows_zip.exists(),
        android_apk_exists=android_apk.exists(),
    )


@app.route("/download/windows")
def download_windows():
    windows_zip = RELEASE_DIR / "NearbyPriceFinder-Windows.zip"

    if not windows_zip.exists():
        return "Windows download is not built yet. Run make_downloads.bat first.", 404

    return send_from_directory(RELEASE_DIR, windows_zip.name, as_attachment=True)


@app.route("/download/android")
def download_android():
    android_apk = RELEASE_DIR / "NearbyPriceFinder-Android.apk"

    if android_apk.exists():
        return send_from_directory(RELEASE_DIR, android_apk.name, as_attachment=True)

    return render_template("android_download.html")

# ================= HOME =================

@app.route("/")
def index():
    return render_template("login.html")

# ================= NORMAL LOGIN =================

@app.route("/login", methods=["POST"])
def login():

    username = request.form["username"]
    password = request.form["password"]

    session.clear()

    if is_owner_admin_login(username, password):
        session["user"] = OWNER_ADMIN_USERNAME
        session["role"] = "admin"
        session["is_owner_admin"] = True

        return redirect("/admin")

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, username, role FROM users
    WHERE username=? AND password=?
    """, (username, password))

    user = cursor.fetchone()

    conn.close()

    if user:

        session["user"] = username
        role = normalize_role(user["role"] if isinstance(user, sqlite3.Row) else user[2])
        session["role"] = role if role != "admin" else "customer"
        session["is_owner_admin"] = False

        return redirect(dashboard_for_role(session["role"]))

    else:

        return "Invalid Username or Password"

# ================= OTP LOGIN PAGE =================

@app.route("/otp_login")
def otp_login():
    return render_template("otp_login.html")


def normalize_phone_number(phone):
    cleaned = re.sub(r"[^\d+]", "", phone or "")

    if cleaned.startswith("+") and re.fullmatch(r"\+\d{10,15}", cleaned):
        return cleaned

    digits = re.sub(r"\D", "", cleaned)

    if len(digits) == 10:
        return f"+91{digits}"

    if 10 < len(digits) <= 15:
        return f"+{digits}"

    return None


def send_sms_otp(phone, otp):
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
    from_number = os.environ.get("TWILIO_FROM_NUMBER")

    if not account_sid or not auth_token or not from_number:
        raise RuntimeError(
            "SMS is not configured. Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_FROM_NUMBER."
        )

    message = f"Your Nearby Price Finder login OTP is {otp}. It expires in {OTP_EXPIRY_MINUTES} minutes."
    payload = urllib.parse.urlencode({
        "To": phone,
        "From": from_number,
        "Body": message,
    }).encode("utf-8")
    auth = base64.b64encode(f"{account_sid}:{auth_token}".encode("utf-8")).decode("ascii")
    request_obj = urllib.request.Request(
        f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json",
        data=payload,
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request_obj, timeout=15) as response:
            if response.status >= 300:
                raise RuntimeError("SMS provider rejected the OTP request.")
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="ignore")
        print("Twilio SMS error:", details)
        raise RuntimeError("Could not send OTP. Check your SMS provider settings and phone number.") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError("Could not connect to the SMS provider. Please try again.") from exc


# ================= SEND OTP =================

@app.route("/send_otp", methods=["POST"])
def send_otp():

    phone = request.form["phone"]
    normalized_phone = normalize_phone_number(phone)

    if not normalized_phone:
        flash("Please enter a valid mobile number with country code, or a 10-digit Indian number.")
        return redirect("/otp_login")

    otp = f"{secrets.randbelow(900000) + 100000}"

    try:
        send_sms_otp(normalized_phone, otp)
    except RuntimeError as exc:
        flash(str(exc))
        return redirect("/otp_login")

    session["otp"] = otp
    session["otp_expires_at"] = (datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES)).isoformat()
    session["phone"] = normalized_phone

    flash("OTP sent to your mobile number.")
    return render_template("verify_otp.html")

# ================= VERIFY OTP =================

@app.route("/verify_otp", methods=["POST"])
def verify_otp():

    entered_otp = request.form["otp"]

    real_otp = session.get("otp")
    expires_at = session.get("otp_expires_at")

    if not real_otp or not expires_at:
        flash("Please request a new OTP.")
        return redirect("/otp_login")

    try:
        otp_expired = datetime.utcnow() > datetime.fromisoformat(expires_at)
    except ValueError:
        otp_expired = True

    if otp_expired:
        session.pop("otp", None)
        session.pop("otp_expires_at", None)
        flash("OTP expired. Please request a new one.")
        return redirect("/otp_login")

    if entered_otp == real_otp:

        session["user"] = session.get("phone")
        session["role"] = "customer"
        session.pop("otp", None)
        session.pop("otp_expires_at", None)

        return redirect(dashboard_for_role(session["role"]))

    else:

        flash("Wrong OTP. Please check the SMS and try again.")
        return render_template("verify_otp.html")

# ================= REGISTER PAGE =================

@app.route("/register")
def register():
    return render_template("register.html")

# ================= REGISTER USER =================

@app.route("/register_user", methods=["POST"])
def register_user():

    username = request.form["username"]
    password = request.form["password"]
    role = normalize_public_role(request.form.get("role"))

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO users(username,password,role)
    VALUES(?,?,?)
    """, (username, password, role))

    conn.commit()
    conn.close()

    session["user"] = username
    session["role"] = role

    return redirect(dashboard_for_role(role))

# ================= HOME PAGE =================

@app.route("/home")
def home():
    return render_template("home.html")


@app.route("/role_dashboard")
def role_dashboard():
    return redirect(dashboard_for_role(session.get("role")))

# ================= SHOPKEEPER PAGE =================

@app.route("/shopkeeper")
def shopkeeper():
    return render_template("shopkeeper.html")

# ================= ADD MULTIPLE PRODUCTS =================

@app.route("/add_product", methods=["POST"])
def add_product():

    shop_names = request.form.getlist("shop_name")
    locations = request.form.getlist("location")
    product_names = request.form.getlist("product_name")
    prices = request.form.getlist("price")
    stocks = request.form.getlist("stock")
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

    if len(prices) < len(product_names) or len(stocks) < len(product_names) or len(product_images) < len(product_names):
        return "Missing product details. Please fill all fields and upload both images.", 400

    shop_image = shop_images[0]
    shop_filename = secure_filename(shop_image.filename)
    shop_path = os.path.join(UPLOAD_FOLDER, shop_filename)
    shop_image.save(shop_path)

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    for i in product_rows:

        # PRODUCT IMAGE

        product_image = product_images[i]

        if not product_image or not product_image.filename:
            conn.close()
            return "Product image is required.", 400

        product_filename = secure_filename(
            product_image.filename
        )

        product_path = os.path.join(
            UPLOAD_FOLDER,
            product_filename
        )

        product_image.save(product_path)

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
            longitude
        )

        VALUES(?,?,?,?,?,?,?,?,?)
        """, (

            shop_names[0],
            locations[0],
            product_names[i],
            prices[i],
            stocks[i],
            product_filename,
            shop_filename,
            latitudes[0] if latitudes else "",
            longitudes[0] if longitudes else ""

        ))

    conn.commit()
    conn.close()

    return redirect("/shopkeeper")

# ================= CUSTOMER PAGE =================

@app.route("/customer")
@role_required("customer")
def customer():

    return render_template(
        "customer.html",
        products=[]
    )

# ================= SEARCH PRODUCTS =================

@app.route("/search", methods=["GET", "POST"])
def search():

    products = []

    if request.method == "POST":

        search = request.form.get("search")

        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()

        cursor.execute("""
        SELECT * FROM products
        WHERE product_name LIKE ?
        """, ('%' + search + '%',))

        products = cursor.fetchall()

        conn.close()

    return render_template(
        "customer.html",
        products=products
    )

# ================= PLACE ORDER =================

@app.route("/place_order", methods=["POST"])
def place_order():

    customer_name = session.get("user")

    product_name = request.form.get("product_name")
    address = request.form.get("address")
    payment = request.form.get("payment")

    price = request.form.get("price", "0")

    product_image = request.form.get("product_image", "")
    rider_name, rider_phone = assign_delivery_rider()
    delivery_otp = generate_delivery_otp()

    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO orders(
        customer_name,
        product_name,
        price,
        product_image,
        address,
        payment_method,
        status,
        rider_name,
        rider_phone,
        delivery_otp,
        otp_verified
    )

    VALUES(?,?,?,?,?,?,?,?,?,?,?)
    """, (
        customer_name,
        product_name,
        price,
        product_image,
        address,
        payment,
        "Order Confirmed",
        rider_name,
        rider_phone,
        delivery_otp,
        "No"
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

# ================= TRACK ORDER =================

@app.route("/track/<int:order_id>")
def track_order(order_id):

    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("""
    SELECT * FROM orders
    WHERE id=?
    """, (order_id,))

    order = cursor.fetchone()

    conn.close()

    if order is None:
        return "Order not found", 404

    return render_template(
        "track.html",
        order_id=order_id,
        status=order["status"],
        order=order
    )


@app.route("/track_status/<int:order_id>")
def track_status(order_id):

    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row

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
            "rider_phone": order["rider_phone"] or "+91 98765 12000",
            "delivery_otp": order["delivery_otp"] or "000000",
            "otp_verified": order["otp_verified"] or "No",
        }
    }

# ================= SHOPKEEPER DASHBOARD =================

@app.route("/shopkeeper_dashboard")
def shopkeeper_dashboard():

    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("""
    SELECT * FROM products
    """)

    products = cursor.fetchall()

    cursor.execute("""
    SELECT * FROM orders
    ORDER BY id DESC
    """)

    orders = cursor.fetchall()

    conn.close()

    return render_template(
        "shopkeeper_dashboard.html",
        products=products,
        orders=orders
    )

# ================= DELETE PRODUCT =================

@app.route("/delete_product/<int:id>")
def delete_product(id):

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    DELETE FROM products
    WHERE id=?
    """, (id,))

    conn.commit()
    conn.close()

    return redirect("/shopkeeper_dashboard")

# ================= EDIT PRODUCT =================

@app.route("/edit_product/<int:id>")
def edit_product(id):

    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row

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

# ================= UPDATE PRODUCT =================

@app.route("/update_product/<int:id>", methods=["POST"])
def update_product(id):

    product_name = request.form.get("product_name")
    price = request.form.get("price")
    stock = request.form.get("stock")

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE products
    SET product_name=?, price=?, stock=?
    WHERE id=?
    """, (
        product_name,
        price,
        stock,
        id
    ))

    conn.commit()
    conn.close()

    return redirect("/shopkeeper_dashboard")

# ================= UPDATE ORDER STATUS =================

@app.route("/update_order_status/<int:id>", methods=["POST"])
def update_order_status(id):

    status = request.form["status"]

    if status == "Delivered":
        flash("Enter the customer's delivery OTP to mark this order as Delivered.")
        return redirect("/shopkeeper_dashboard")

    conn = sqlite3.connect(DATABASE_PATH)
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


@app.route("/confirm_delivery/<int:id>", methods=["POST"])
def confirm_delivery(id):

    entered_otp = request.form.get("delivery_otp", "").strip()

    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
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

# ================= SHOPKEEPER ORDERS =================

@app.route("/shopkeeper_orders")
def shopkeeper_orders():

    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("""
    SELECT * FROM orders
    ORDER BY id DESC
    """)

    orders = cursor.fetchall()

    cursor.execute("""
    SELECT COUNT(*) FROM orders
    """)

    total_orders = cursor.fetchone()[0]

    cursor.execute("""
    SELECT SUM(price) FROM orders
    """)

    revenue = cursor.fetchone()[0]

    if revenue is None:
        revenue = 0

    cursor.execute("""
    SELECT COUNT(*) FROM orders
    WHERE status='Delivered'
    """)

    delivered = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "shopkeeper_orders.html",
        orders=orders,
        total_orders=total_orders,
        revenue=revenue,
        delivered=delivered
    )

# ================= UPDATE STATUS =================

@app.route("/update_status/<int:order_id>", methods=["POST"])
def update_status(order_id):

    status = request.form["status"]

    if status == "Delivered":
        flash("Use the delivery OTP confirmation form to mark an order as Delivered.")
        return redirect("/shopkeeper_orders")

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE orders
    SET status=?
    WHERE id=?
    """, (status, order_id))

    conn.commit()
    conn.close()

    return redirect("/shopkeeper_orders")

# ================= DELETE ORDER =================

@app.route("/delete_order/<int:order_id>", methods=["POST"])
def delete_order(order_id):

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    DELETE FROM orders
    WHERE id=?
    """, (order_id,))

    conn.commit()
    conn.close()

    return redirect("/shopkeeper_orders")

# ================= ANALYTICS DASHBOARD =================

@app.route("/dashboard")
def dashboard():

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM products"
    )

    total_products = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM users"
    )

    total_users = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM orders"
    )

    total_orders = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "dashboard.html",
        total_products=total_products,
        total_users=total_users,
        total_orders=total_orders
    )
# ================= BUY PAGE =================

@app.route("/buy")
def buy():

    product_name = request.args.get("product_name")
    price = request.args.get("price")
    product_image = request.args.get("product_image")

    return render_template(
        "buy.html",
        product_name=product_name,
        price=price,
        product_image=product_image
    )
# ================= SELLER DASHBOARD =================

@app.route("/seller_dashboard")
def seller_dashboard():

    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM products")
    total_products = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM orders")
    total_orders = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(price) FROM orders")
    revenue = cursor.fetchone()[0]

    if revenue is None:
        revenue = 0

    conn.close()

    return render_template(
        "shopkeeper_dashboard.html",
        total_products=total_products,
        total_orders=total_orders,
        revenue=revenue
    )

# ================= PRODUCTS PANEL =================

@app.route("/seller_products")
def seller_products():

    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("""
    SELECT * FROM products
    ORDER BY id DESC
    """)

    products = cursor.fetchall()

    conn.close()

    return render_template(
        "shopkeeper_dashboard.html",
        products=products
    )

# ================= ORDERS PANEL =================

@app.route("/seller_orders")
def seller_orders():

    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("""
    SELECT * FROM orders
    ORDER BY id DESC
    """)

    orders = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM orders")
    total_orders = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(price) FROM orders")
    revenue = cursor.fetchone()[0]

    if revenue is None:
        revenue = 0

    cursor.execute("SELECT COUNT(*) FROM orders WHERE status='Delivered'")
    delivered = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "shopkeeper_orders.html",
        orders=orders,
        total_orders=total_orders,
        revenue=revenue,
        delivered=delivered
    )

# ================= MAPS PANEL =================

@app.route("/seller_maps")
def seller_maps():

    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("""
    SELECT * FROM products
    WHERE latitude IS NOT NULL
    AND latitude != ''
    AND longitude IS NOT NULL
    AND longitude != ''
    ORDER BY id DESC
    """)

    products = cursor.fetchall()

    conn.close()

    return render_template(
        "seller_maps.html",
        products=products
    )

# ================= PRODUCT MAP =================

@app.route("/product_map/<int:product_id>")
def product_map(product_id):

    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("""
    SELECT * FROM products
    WHERE id=?
    """, (product_id,))

    product = cursor.fetchone()

    conn.close()

    if product is None:
        return "Product not found", 404

    return render_template(
        "product_map.html",
        product=product
    )


# ================= 3D PRODUCT VIEWER =================

@app.route("/product_3d/<int:product_id>")
def product_3d(product_id):

    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("""
    SELECT * FROM products
    WHERE id=?
    """, (product_id,))

    product = cursor.fetchone()

    conn.close()

    if product is None:
        return "Product not found", 404

    return render_template(
        "product_3d.html",
        product=product
    )

# ================= SETTINGS PANEL =================

@app.route("/seller_settings")
def seller_settings():

    return '''
    <h1 style="font-family:Arial;text-align:center;margin-top:100px;">
    Seller Settings Coming Soon ⚙️
    </h1>
    '''
@app.route("/payment_demo")
def payment_demo():

    return render_template(
        "buy.html",
        product_name="Demo Product",
        price="999",
        product_image="/static/demo.jpg"
    )
# ================= AI CHATBOT =================

@app.route("/chatbot")
def chatbot():

    return render_template("chatbot.html")


def find_matching_products(user_message):
    ignored_words = {
        "show", "find", "near", "nearby", "cheap", "cheapest", "price",
        "product", "products", "available", "with", "under", "want", "need",
        "please", "best", "lowest", "local", "shop", "shops",
    }
    searchable_words = [
        word for word in user_message.lower().replace(",", " ").replace(".", " ").split()
        if len(word) > 2 and word not in ignored_words
    ]

    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    products = []
    seen_products = set()

    for word in searchable_words[:4]:
        cursor.execute("""
        SELECT product_name, price, shop_name, location, stock
        FROM products
        WHERE lower(product_name) LIKE ?
        ORDER BY CAST(price AS INTEGER) ASC
        LIMIT 4
        """, (f"%{word}%",))

        for product in cursor.fetchall():
            key = (product["product_name"], product["shop_name"], product["price"])
            if key not in seen_products:
                products.append(dict(product))
                seen_products.add(key)

    conn.close()
    return products[:8]


def local_chatbot_reply(user_message, products):
    clean_message = user_message.lower()

    if products:
        lines = []
        for product in products[:3]:
            stock_text = f", stock: {product['stock']}" if product.get("stock") else ""
            shop_text = product.get("shop_name") or "Nearby shop"
            location_text = f" at {product['location']}" if product.get("location") else ""
            lines.append(
                f"{product['product_name']} - Rs. {product['price']} from {shop_text}{location_text}{stock_text}"
            )

        return "I found these nearby options: " + " | ".join(lines)

    if any(word in clean_message for word in ["hello", "hi", "hey"]):
        return "Hello! Tell me what product you need and I will help you find nearby options."

    if any(word in clean_message for word in ["help", "what can you do", "how"]):
        return "I can search products, suggest cheaper nearby items, explain order tracking, and guide you to customer or shopkeeper pages."

    if any(word in clean_message for word in ["cheap", "cheapest", "lowest"]):
        return "For the lowest price, search the product name on the customer page and compare nearby shops."

    if "track" in clean_message or "order" in clean_message:
        return "You can track orders from the orders page after placing a product order."

    if "shop" in clean_message or "seller" in clean_message:
        return "Shopkeepers can upload products, stock, price, location, and images from the shopkeeper page."

    return "I could not find that product yet. Try a clear product name like laptop, bag, shoes, mobile, charger, or milk."


def ask_chatgpt(user_message, products):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    model = os.getenv("OPENAI_MODEL", "gpt-5.4-mini")
    payload = {
        "model": model,
        "instructions": (
            "You are the AI shopping assistant for Nearby Price Finder. "
            "Help users find nearby products, compare prices, understand stock, "
            "and use customer, seller, checkout, and tracking flows. "
            "Use the provided product context when available. "
            "Keep replies short, friendly, practical, and under 90 words. "
            "Do not invent products, prices, shop names, stock, or locations."
        ),
        "input": (
            f"User message: {user_message}\n\n"
            f"Matching product context as JSON: {json.dumps(products, ensure_ascii=True)}"
        ),
        "max_output_tokens": 220,
    }

    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError):
        return None

    if data.get("output_text"):
        return data["output_text"].strip()

    for item in data.get("output", []):
        for content in item.get("content", []):
            if content.get("type") == "output_text" and content.get("text"):
                return content["text"].strip()

    return None


# ================= CHATBOT RESPONSE =================

@app.route("/chat_response", methods=["POST"])
def chat_response():

    raw_message = request.form.get("message", "").strip()

    if not raw_message:
        return {"reply": "Please type a product name or shopping question."}

    products = find_matching_products(raw_message)
    chatgpt_reply = ask_chatgpt(raw_message, products)

    return {
        "reply": chatgpt_reply or local_chatbot_reply(raw_message, products)
    }

    reply = ""

    # ================= SMART RESPONSES =================

    if "laptop" in user_message:

        reply = "💻 Found nearby laptop products under ₹50,000."

    elif "bag" in user_message:

        reply = "🎒 Found trending bags near your location."

    elif "shoe" in user_message:

        reply = "👟 Best sports shoes available with fast delivery."

    elif "cheap" in user_message:

        reply = "🔥 Showing lowest price products near you."

    elif "mobile" in user_message:

        reply = "📱 Latest mobiles available with discount."

    elif "hello" in user_message:

        reply = "👋 Hello! What product are you searching for?"

    elif "nearby" in user_message:

        reply = "📍 Searching nearby shops using smart maps."

    else:

        reply = "🤖 Sorry, I am still learning. Try searching products like bags, shoes, laptops, mobiles."

    return {
        "reply": reply
    }
# ================= LIVE CHAT =================

@app.route("/live_chat")
def live_chat():

    return render_template(
        "live_chat.html",
        current_user=session.get("user", "Guest")
    )


@app.route("/chat_messages")
def chat_messages():

    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, sender, message, created_at
    FROM chats
    ORDER BY id ASC
    """)

    chats = [
        {
            "id": chat["id"],
            "sender": chat["sender"],
            "message": chat["message"],
            "created_at": chat["created_at"] or "",
        }
        for chat in cursor.fetchall()
    ]

    conn.close()

    return {"chats": chats}


# ================= SEND MESSAGE =================

@app.route("/send_message", methods=["POST"])
def send_message():

    sender = request.form.get("sender", "customer").strip().lower()

    message = request.form.get("message", "").strip()

    if sender not in ["customer", "seller"]:
        sender = "customer"

    if not message:
        return {"success": False, "error": "Message is required."}, 400

    conn = sqlite3.connect(DATABASE_PATH)

    cursor = conn.cursor()

    cursor.execute("""

    INSERT INTO chats(

        sender,
        message,
        created_at

    )

    VALUES(?,?,?)

    """, (
        sender,
        message,
        datetime.now().strftime("%d %b %Y, %I:%M %p")
    ))

    conn.commit()

    conn.close()

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return {"success": True}

    return redirect("/live_chat")

# ================= LOGOUT =================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")
# ================= ADMIN PANEL =================

@app.route("/admin")
@role_required("admin")
def admin():

    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    # TOTAL PRODUCTS
    cursor.execute("SELECT COUNT(*) FROM products")
    total_products = cursor.fetchone()[0]

    # TOTAL ORDERS
    cursor.execute("SELECT COUNT(*) FROM orders")
    total_orders = cursor.fetchone()[0]

    # TOTAL USERS
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    # ALL PRODUCTS
    cursor.execute("""
    SELECT * FROM products
    ORDER BY id DESC
    """)

    products = cursor.fetchall()

    # ALL ORDERS
    cursor.execute("""
    SELECT * FROM orders
    ORDER BY id DESC
    """)

    orders = cursor.fetchall()

    conn.close()

    return render_template(
        "admin.html",
        total_products=total_products,
        total_orders=total_orders,
        total_users=total_users,
        products=products,
        orders=orders
    )

# ================= RUN APP =================

if __name__ == "__main__":
   app.run(host="0.0.0.0", port=5000, debug=False)
