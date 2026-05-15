from pathlib import Path

from flask import Flask, render_template, render_template_string, request, redirect, session, flash, send_from_directory
import base64
from flask_cors import CORS
import sqlite3
import psycopg2
from psycopg2 import extras
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
import cloudinary
import cloudinary.uploader

BASE_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = BASE_DIR / "frontend"
RELEASE_DIR = BASE_DIR / "release"
DATABASE_URL = os.environ.get("DATABASE_URL")
DATABASE_AUTH_TOKEN = os.environ.get("DATABASE_AUTH_TOKEN")
DATABASE_PATH = os.environ.get("DATABASE_PATH", str(BASE_DIR / "database.db"))

class PostgresWrapper:
    def __init__(self, conn):
        self.conn = conn
    def __getattr__(self, name):
        return getattr(self.conn, name)
    def cursor(self):
        return PostgresCursor(self.conn.cursor(cursor_factory=extras.RealDictCursor))
    def __enter__(self): return self
    def __exit__(self, *args): self.conn.close()

class PostgresRow:
    def __init__(self, data):
        self.data = data
    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self.data.values())[key]
        return self.data[key]
    def keys(self):
        return self.data.keys()
    def __iter__(self):
        return iter(self.data.values())
    def __len__(self):
        return len(self.data)

class PostgresCursor:
    def __init__(self, cursor):
        self.cursor = cursor
        self.lastrowid = None
    def __getattr__(self, name):
        return getattr(self.cursor, name)
    def execute(self, sql, params=()):
        # PostgreSQL doesn't have lastrowid, so we append RETURNING id to INSERTS
        is_insert = sql.strip().upper().startswith('INSERT')
        if is_insert and 'RETURNING' not in sql.upper():
            sql = sql.rstrip().rstrip(';') + ' RETURNING id'
            
        sql = sql.replace('?', '%s')
        sql = sql.replace('AUTOINCREMENT', '')
        sql = sql.replace('INTEGER PRIMARY KEY', 'SERIAL PRIMARY KEY')
        sql = re.sub(r'\bLIKE\b', 'ILIKE', sql, flags=re.IGNORECASE)
        
        if params is None: params = ()
        if not isinstance(params, (tuple, list)): params = (params,)
        
        self.cursor.execute(sql, params)
        
        if is_insert:
            try:
                row = self.cursor.fetchone()
                if row:
                    # row is a dict due to RealDictCursor
                    self.lastrowid = list(row.values())[0]
            except Exception:
                pass
                
        return self
    def fetchone(self):
        row = self.cursor.fetchone()
        return PostgresRow(row) if row else None
    def fetchall(self):
        rows = self.cursor.fetchall()
        return [PostgresRow(r) for r in rows]
    def __iter__(self):
        for row in self.cursor:
            yield PostgresRow(row)

def get_db_conn():
    """Returns a database connection. Uses Postgres if DATABASE_URL starts with postgres://, otherwise local SQLite."""
    if DATABASE_URL and (DATABASE_URL.startswith("postgres://") or DATABASE_URL.startswith("postgresql://")):
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        return PostgresWrapper(conn)
    else:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        return DictConnection(conn)

class DictConnection:
    def __init__(self, conn):
        self.conn = conn
    def __getattr__(self, name):
        return getattr(self.conn, name)
    def cursor(self):
        return DictCursor(self.conn.cursor())
    def __enter__(self): return self
    def __exit__(self, *args): self.conn.close()

class DictCursor:
    def __init__(self, cursor):
        self.cursor = cursor
    def __getattr__(self, name):
        return getattr(self.cursor, name)
    def fetchone(self):
        row = self.cursor.fetchone()
        return row
    def fetchall(self):
        return self.cursor.fetchall()
    def __iter__(self):
        return iter(self.cursor)

UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER_PATH", str(FRONTEND_DIR / "static" / "uploads"))

from backend.app_factory import app
CORS(app, supports_credentials=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

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

# ================= DATABASE SETUP =================

def _setup_database():
    """Create all tables with full columns on first run.
    ALTER TABLE is used only to add genuinely new columns to existing DBs."""
    conn = get_db_conn()
    cursor = conn.cursor()

    # USERS TABLE — full schema
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT    NOT NULL,
        email    TEXT,
        password TEXT    NOT NULL,
        role     TEXT    DEFAULT 'customer'
    )
    """)

    # PRODUCTS TABLE — full schema
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products(
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        shop_name     TEXT,
        location      TEXT,
        product_name  TEXT,
        price         TEXT,
        stock         TEXT,
        product_image TEXT,
        shop_image    TEXT,
        latitude      TEXT,
        longitude     TEXT,
        unit          TEXT
    )
    """)

    # ORDERS TABLE — full schema
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders(
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name  TEXT,
        customer_phone TEXT,
        product_name   TEXT,
        price          TEXT,
        product_image  TEXT,
        address        TEXT,
        payment_method TEXT,
        status         TEXT DEFAULT 'Order Confirmed',
        rider_name     TEXT,
        rider_phone    TEXT,
        delivery_otp   TEXT,
        otp_verified   TEXT DEFAULT 'No',
        created_at     TEXT
    )
    """)

    # CHATS TABLE — full schema
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chats(
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        sender     TEXT,
        message    TEXT,
        created_at TEXT
    )
    """)

    # CART TABLE — new feature
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cart(
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT NOT NULL,
        product_id    INTEGER NOT NULL,
        product_name  TEXT,
        price         TEXT,
        product_image TEXT,
        shop_name     TEXT,
        quantity      INTEGER DEFAULT 1,
        unit          TEXT,
        added_at      TEXT
    )
    """)

    # REVIEWS TABLE — for ratings & reviews
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reviews(
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id      INTEGER,
        customer_name TEXT,
        product_name  TEXT,
        rating        INTEGER DEFAULT 5,
        review_text   TEXT,
        created_at    TEXT
    )
    """)

    # Migrate older DBs: add any columns that didn't exist before
    _safe_alter(cursor, "users",    "email",        "TEXT")
    _safe_alter(cursor, "users",    "role",         "TEXT DEFAULT 'customer'")
    _safe_alter(cursor, "products", "latitude",     "TEXT")
    _safe_alter(cursor, "products", "longitude",    "TEXT")
    _safe_alter(cursor, "products", "unit",         "TEXT")
    _safe_alter(cursor, "chats",    "created_at",   "TEXT")
    _safe_alter(cursor, "orders",   "rider_name",   "TEXT")
    _safe_alter(cursor, "orders",   "rider_phone",  "TEXT")
    _safe_alter(cursor, "orders",   "delivery_otp", "TEXT")
    _safe_alter(cursor, "orders",   "otp_verified", "TEXT DEFAULT 'No'")
    _safe_alter(cursor, "orders",   "product_image","TEXT")
    _safe_alter(cursor, "orders",   "address",      "TEXT")
    _safe_alter(cursor, "orders",   "payment_method","TEXT")
    _safe_alter(cursor, "orders",   "status",        "TEXT DEFAULT 'Order Confirmed'")
    _safe_alter(cursor, "orders",   "product_name",  "TEXT")
    _safe_alter(cursor, "orders",   "price",         "TEXT")
    _safe_alter(cursor, "orders",   "customer_name", "TEXT")
    _safe_alter(cursor, "orders",   "created_at",    "TEXT")
    _safe_alter(cursor, "orders",   "customer_phone","TEXT")
    _safe_alter(cursor, "cart",     "unit",          "TEXT")
    _safe_alter(cursor, "products", "seller_username", "TEXT")
    _safe_alter(cursor, "orders",   "seller_username", "TEXT")

    conn.commit()
    conn.close()


def _safe_alter(cursor, table, column, definition):
    """Add a column to an existing table; silently skip if already present."""
    try:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
    except Exception:
        # Ignore errors (like 'duplicate column') to allow smooth startup on both SQLite and Turso
        pass


_setup_database()


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


def upload_to_cloudinary(file_storage):
    """Uploads a FileStorage object to Cloudinary and returns the secure URL."""
    if not file_storage or not file_storage.filename:
        return None
    try:
        upload_result = cloudinary.uploader.upload(file_storage)
        return upload_result.get("secure_url")
    except Exception as e:
        print(f"Cloudinary Upload Error: {str(e)}")
        return None


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

            if session.get("is_owner_admin"):
                return view_func(*args, **kwargs)


            if current_role in allowed_roles:
                return view_func(*args, **kwargs)

            # Fail-safe: Avoid infinite redirect loop
            target = dashboard_for_role(current_role)
            if target == request.path:
                # If we are already on the dashboard but unauthorized, something is wrong with the session.
                # Clear session and redirect to login to break the loop.
                session.clear()
                flash("Session error or unauthorized access. Please login again.")
                return redirect("/")

            return redirect(target)




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

    conn = get_db_conn()
    cursor = conn.cursor()

    # conn.row_factory handled in get_db_conn()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, username, password, role FROM users
    WHERE username=?
    """, (username,))

    user = cursor.fetchone()

    conn.close()

    from werkzeug.security import check_password_hash

    is_valid = False
    if user:
        db_password = user["password"]
        if db_password.startswith("scrypt:") or db_password.startswith("pbkdf2:"):
            is_valid = check_password_hash(db_password, password)
        else:
            is_valid = (db_password == password)

    if is_valid:

        session["user"] = username
        role = normalize_role(user["role"])
        session["role"] = role if role != "admin" else "customer"
        session["is_owner_admin"] = False

        return redirect(dashboard_for_role(session["role"]))

    else:

        return "Invalid Username or Password"

@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    
    conn = get_db_conn()
    # conn.row_factory handled in get_db_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    user = cursor.fetchone()
    conn.close()
    
    if user and user["password"] == password: # Simple check for now
        session["user"] = username
        session["role"] = normalize_role(user["role"])
        return {"success": True, "user": username, "role": session["role"]}
    
    return {"success": False, "message": "Invalid credentials"}, 401

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
        print(f"DEVELOPMENT MODE: SMS to {phone} - OTP is {otp}")
        return False

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
        sent_real = send_sms_otp(normalized_phone, otp)
    except RuntimeError as exc:
        flash(str(exc))
        return redirect("/otp_login")

    session["otp"] = otp
    session["otp_expires_at"] = (datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES)).isoformat()
    session["phone"] = normalized_phone

    if sent_real is False:
        flash(f"DEV MODE: Your OTP is {otp}")
    else:
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

    conn = get_db_conn()
    cursor = conn.cursor()

    from werkzeug.security import generate_password_hash
    hashed_password = generate_password_hash(password)

    cursor.execute("""
    INSERT INTO users(username,password,role)
    VALUES(?,?,?)
    """, (username, hashed_password, role))

    conn.commit()
    conn.close()

    session["user"] = username
    session["role"] = role

    return redirect(dashboard_for_role(role))

# ================= HOME PAGE =================

@app.route("/home")
@role_required("customer", "admin")
def home():
    return render_template("home.html")


@app.route("/role_dashboard")
def role_dashboard():
    return redirect(dashboard_for_role(session.get("role")))

# ================= SHOPKEEPER PAGE =================

@app.route("/shopkeeper")
@role_required("seller")
def shopkeeper():
    return render_template("shopkeeper.html")

# ================= ADD MULTIPLE PRODUCTS =================

@app.route("/add_product", methods=["POST"])
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

    # Upload shop image once (since it's the same for all products in this batch)
    shop_image_url = upload_to_cloudinary(shop_images[0])
    if not shop_image_url:
        conn.close()
        return "Failed to upload shop image to the cloud.", 500

    for i in product_rows:
        # UPLOAD PRODUCT IMAGE TO CLOUDINARY
        product_image_url = upload_to_cloudinary(product_images[i])

        if not product_image_url:
            conn.close()
            return f"Failed to upload image for {product_names[i]} to the cloud.", 500

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

# ================= CUSTOMER PAGE =================

@app.route("/customer")
@role_required("customer", "admin")
def customer():
    user_lat = request.args.get("lat")
    user_lng = request.args.get("lng")

    conn = get_db_conn()
    cursor = conn.cursor()
    
    # Fetch all products to sort them by distance
    cursor.execute("SELECT * FROM products")
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

# ================= SEARCH PRODUCTS =================

@app.route("/search", methods=["GET", "POST"])
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

# ================= PLACE ORDER =================

@app.route("/place_order", methods=["POST"])
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


@app.route("/online_payment/<int:product_id>", methods=["POST"])
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


@app.route("/cash_on_delivery/<int:product_id>", methods=["POST"])
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


# ================= TRACK ORDER =================

@app.route("/track/<int:order_id>")
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


@app.route("/track_status/<int:order_id>")
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

# ================= DELETE PRODUCT =================

@app.route("/delete_product/<int:id>")
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

# ================= EDIT PRODUCT =================

@app.route("/edit_product/<int:id>")
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

# ================= UPDATE PRODUCT =================

@app.route("/update_product/<int:id>", methods=["POST"])
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

# ================= UPDATE ORDER STATUS =================

@app.route("/update_order_status/<int:id>", methods=["POST"])
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


@app.route("/confirm_delivery/<int:id>", methods=["POST"])
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

# ================= SHOPKEEPER ORDERS =================

@app.route("/shopkeeper_orders")
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

    cursor.execute("""
    SELECT COUNT(*) FROM orders WHERE seller_username=?
    """, (seller,))

    total_orders = cursor.fetchone()[0]

    cursor.execute("""
    SELECT SUM(price) FROM orders WHERE seller_username=?
    """, (seller,))

    revenue = cursor.fetchone()[0]

    if revenue is None:
        revenue = 0

    cursor.execute("""
    SELECT COUNT(*) FROM orders
    WHERE status='Delivered' AND seller_username=?
    """, (seller,))

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

# ================= DELETE ORDER =================

@app.route("/delete_order/<int:order_id>", methods=["POST"])
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

# ================= ANALYTICS DASHBOARD =================

@app.route("/dashboard")
@role_required("seller", "admin")
def dashboard():

    conn = get_db_conn()
    # conn.row_factory handled in get_db_conn()
    cursor = conn.cursor()

    seller = session.get("user")
    is_owner = session.get("is_owner_admin", False)

    if is_owner:
        # Owner/admin sees global stats
        cursor.execute("SELECT COUNT(*) FROM products")
        total_products = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM orders")
        total_orders = cursor.fetchone()[0]
    else:
        # Sellers see only their own stats
        cursor.execute("SELECT COUNT(*) FROM products WHERE seller_username=?", (seller,))
        total_products = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]  # total platform users is fine to show
        cursor.execute("SELECT COUNT(*) FROM orders WHERE seller_username=?", (seller,))
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
# ================= SELLER DASHBOARD =================

@app.route("/seller_dashboard")
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

    cursor.execute("SELECT SUM(CAST(price AS FLOAT)) FROM orders WHERE seller_username=?", (seller,))
    revenue = cursor.fetchone()[0]

    if revenue is None:
        revenue = 0

    conn.close()

    return render_template(
        "shopkeeper_dashboard.html",
        products=products,
        orders=orders,
        total_products=total_products,
        total_orders=total_orders,
        revenue=revenue
    )

# ================= PRODUCTS PANEL =================

@app.route("/seller_products")
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

# ================= ORDERS PANEL =================

@app.route("/seller_orders")
@role_required("seller")
def seller_orders():
    return redirect("/shopkeeper_orders")

# ================= MAPS PANEL =================

@app.route("/seller_maps")
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

# ================= PRODUCT MAP =================

@app.route("/product_map/<int:product_id>")
@role_required("customer", "seller", "admin")
def product_map(product_id):

    conn = get_db_conn()
    # conn.row_factory handled in get_db_conn()

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
@role_required("customer", "seller", "admin")
def product_3d(product_id):

    conn = get_db_conn()
    # conn.row_factory handled in get_db_conn()

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
@role_required("seller")
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
@role_required("customer", "admin")
def chatbot():
    return render_template("chatbot.html")


@app.route("/chat_response", methods=["POST"])
def chat_response():
    user_message = request.form.get("message", "").strip()
    if not user_message:
        return {"reply": "Please say something!"}

    # Find relevant products from the DB
    matching_products = find_matching_products(user_message)
    
    # Generate a smart reply
    reply = local_chatbot_reply(user_message, matching_products)
    
    return {"reply": reply}


def find_matching_products(user_message):
    ignored_words = {
        "show", "find", "near", "nearby", "cheap", "cheapest", "price",
        "product", "products", "available", "with", "under", "want", "need",
        "please", "best", "lowest", "local", "shop", "shops", "give", "me"
    }
    searchable_words = [
        word for word in user_message.lower().replace(",", " ").replace(".", " ").split()
        if len(word) > 2 and word not in ignored_words
    ]

    if not searchable_words:
        return []

    conn = get_db_conn()
    cursor = conn.cursor()

    products = []
    seen_products = set()

    for word in searchable_words[:3]:
        cursor.execute("""
        SELECT product_name, price, shop_name, location, stock
        FROM products
        WHERE lower(product_name) LIKE ?
        ORDER BY CAST(price AS INTEGER) ASC
        LIMIT 3
        """, (f"%{word}%",))

        for product in cursor.fetchall():
            key = (product["product_name"], product["shop_name"], product["price"])
            if key not in seen_products:
                products.append(dict(product))
                seen_products.add(key)

    conn.close()
    return products[:6]


def local_chatbot_reply(user_message, products):
    clean_message = user_message.lower()

    if products:
        reply = "I found some great options nearby for you! 🛍️<br><br>"
        for p in products[:3]:
            stock_info = f" (Only {p['stock']} left!)" if p.get('stock') and int(p['stock']) < 10 else ""
            reply += f"🔹 <b>{p['product_name']}</b> - ₹{p['price']} at <i>{p['shop_name']}</i> ({p['location']}){stock_info}<br>"
        
        reply += "<br>Would you like to see more details or should I find something else?"
        return reply

    if any(word in clean_message for word in ["hello", "hi", "hey", "greetings"]):
        return "👋 Hello! I am your AI Shopping Assistant. I can help you find products, compare prices, and track your orders. What are you looking for today?"

    if any(word in clean_message for word in ["status", "track", "where is my", "order"]):
        return "📦 You can track your active orders by clicking 'Track Order' on your dashboard. If you give me an Order ID, I can tell you where to look!"

    if any(word in clean_message for word in ["cheap", "lowest", "best price", "discount"]):
        return "💰 I always look for the lowest prices! Try searching for a specific item like 'milk' or 'rice', and I'll rank them by price and distance for you."

    if any(word in clean_message for word in ["location", "gps", "near me", "map"]):
        return "📍 To find shops near you, make sure to allow location access. You can also use the 'Map View' on the home page to see all nearby stores visually."

    if any(word in clean_message for word in ["thank", "thanks", "awesome", "great"]):
        return "You're very welcome! I'm here to help. Anything else you need?"

    return "🤔 I'm not quite sure about that yet. Could you try searching for a specific product name? (e.g., 'Do you have fresh milk?')"


# ================= SELLER STATS API =================

@app.route("/api/seller_stats")
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


# ================= REAL-TIME NOTIFICATIONS =================

@app.route("/api/seller_notifications")
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


# ================= INVOICE GENERATOR =================

@app.route("/invoice/<int:order_id>")
@role_required("customer", "seller", "admin")
def generate_invoice(order_id):
    conn = get_db_conn()
    # conn.row_factory handled in get_db_conn()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM orders WHERE id=?", (order_id,))
    order = cursor.fetchone()
    conn.close()

    if not order:
        return "Order not found", 404

    # Security check: Ensure the user is authorized to view this invoice
    current_user = session.get("user")
    current_role = session.get("role")
    
    is_owner = (
        current_role == "admin" or 
        (order['customer_name'] and order['customer_name'] == current_user) or
        (order['seller_username'] and order['seller_username'] == current_user)
    )

    if not is_owner:
        # Special case: If order has no names (legacy/broken data), we allow viewing if they have the link
        if order['customer_name'] or order['seller_username']:
            flash("You are not authorized to view this invoice.")
            return redirect("/")


    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Invoice #{{ order.id }}</title>
        <style>
            body { font-family: 'Inter', sans-serif; padding: 40px; color: #333; }
            .invoice-box { max-width: 800px; margin: auto; border: 1px solid #eee; padding: 30px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.05); }
            .header { display: flex; justify-content: space-between; margin-bottom: 40px; border-bottom: 2px solid #22d3ee; padding-bottom: 20px; }
            .logo { font-size: 24px; font-weight: 800; color: #07111f; }
            .invoice-info { text-align: right; }
            .details { display: grid; grid-template-columns: 1fr 1fr; gap: 40px; margin-bottom: 40px; }
            .details h4 { margin-bottom: 10px; color: #888; text-transform: uppercase; font-size: 12px; }
            table { width: 100%; border-collapse: collapse; margin-bottom: 40px; }
            th { text-align: left; background: #f9f9f9; padding: 15px; border-bottom: 2px solid #eee; }
            td { padding: 15px; border-bottom: 1px solid #eee; }
            .total { text-align: right; font-size: 20px; font-weight: 800; }
            .footer { margin-top: 40px; text-align: center; color: #888; font-size: 12px; }
            @media print { .no-print { display: none; } }
        </style>
    </head>
    <body>
        <div class="invoice-box">
            <div class="header">
                <div class="logo">Nearby Price Finder</div>
                <div class="invoice-info">
                    <h2 style="margin:0">INVOICE</h2>
                    <p style="margin:5px 0">#INV-{{ order.id }}</p>
                    <p style="margin:0; font-size:12px">{{ order.created_at }}</p>
                </div>
            </div>

            <div class="details">
                <div>
                    <h4>Billed To:</h4>
                    <strong>{{ order.customer_name }}</strong><br>
                    {{ order.address }}
                </div>
                <div style="text-align: right;">
                    <h4>Payment Method:</h4>
                    {{ order.payment_method }}
                </div>
            </div>

            <table>
                <thead>
                    <tr>
                        <th>Description</th>
                        <th>Status</th>
                        <th style="text-align: right;">Amount</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>{{ order.product_name }}</td>
                        <td>{{ order.status }}</td>
                        <td style="text-align: right;">₹{{ order.price }}</td>
                    </tr>
                </tbody>
            </table>

            <div class="total">
                Total Amount: ₹{{ order.price }}
            </div>

            <div class="footer">
                Thank you for shopping locally with Nearby Price Finder!<br>
                This is a computer-generated invoice.
            </div>
            
            <div style="margin-top: 30px; text-align: center;" class="no-print">
                <button onclick="window.print()" style="padding: 10px 20px; border-radius: 8px; background: #22d3ee; border: none; font-weight: 800; cursor: pointer;">🖨️ Print Invoice</button>
            </div>
        </div>
    </body>
    </html>
    """, order=order)


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
# ================= LIVE CHAT =================

@app.route("/live_chat")
def live_chat():

    return render_template(
        "live_chat.html",
        current_user=session.get("user", "Guest")
    )


@app.route("/chat_messages")
def chat_messages():

    conn = get_db_conn()
    # conn.row_factory handled in get_db_conn()
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

    conn = get_db_conn()

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

    conn = get_db_conn()
    # conn.row_factory handled in get_db_conn()

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

# ================= SHOPPING CART =================

@app.route("/cart")
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


@app.route("/add_to_cart", methods=["POST"])
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


@app.route("/remove_from_cart/<int:item_id>", methods=["POST"])
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


@app.route("/update_cart/<int:item_id>", methods=["POST"])
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


@app.route("/checkout", methods=["POST"])
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


# ================= NEARBY PRODUCTS API =================

import math

def haversine_km(lat1, lon1, lat2, lon2):
    """Return distance in km between two GPS points."""
    R = 6371.0
    try:
        lat1, lon1, lat2, lon2 = map(math.radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
    except (TypeError, ValueError):
        return float("inf")
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


@app.route("/api/nearby_products")
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


@app.route("/api/products")
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


@app.route("/api/orders")
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


# ================= PRODUCT REVIEWS =================

@app.route("/leave_review/<int:order_id>")
@role_required("customer", "admin")
def leave_review_page(order_id):
    conn = get_db_conn()
    # conn.row_factory handled in get_db_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE id=?", (order_id,))
    order = cursor.fetchone()
    conn.close()

    if order is None:
        flash("Order not found.")
        return redirect("/home")

    if (order["status"] or "").lower() != "delivered":
        flash("You can only review delivered orders.")
        return redirect("/home")

    return render_template("leave_review.html", order=order)


@app.route("/submit_review/<int:order_id>", methods=["POST"])
@role_required("customer", "admin")
def submit_review(order_id):
    customer    = session.get("user", "Guest")
    rating      = int(request.form.get("rating", 5))
    review_text = request.form.get("review_text", "").strip()

    conn = get_db_conn()
    # conn.row_factory handled in get_db_conn()
    cursor = conn.cursor()

    cursor.execute("SELECT product_name FROM orders WHERE id=?", (order_id,))
    order = cursor.fetchone()

    if order:
        cursor.execute("""
        INSERT INTO reviews(order_id, customer_name, product_name, rating, review_text, created_at)
        VALUES(?,?,?,?,?,?)
        """, (
            order_id, customer, order["product_name"],
            max(1, min(5, rating)), review_text,
            datetime.now().strftime("%d %b %Y, %I:%M %p")
        ))
        conn.commit()
        flash("Thank you for your review! ⭐")

    conn.close()
    return redirect("/home")


@app.route("/api/product_reviews")
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


# ================= RUN APP =================

if __name__ == "__main__":
   app.run(host="0.0.0.0", port=5000, debug=False)

