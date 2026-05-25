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
import firebase_admin
from firebase_admin import credentials, auth

# --- FIREBASE ADMIN INITIALIZATION ---
firebase_cert_path = os.environ.get("FIREBASE_SERVICE_ACCOUNT_PATH")
if firebase_cert_path and os.path.exists(firebase_cert_path):
    cred = credentials.Certificate(firebase_cert_path)
    firebase_admin.initialize_app(cred)
else:
    # Fallback for dev or if env var is missing
    print("WARNING: Firebase Admin not initialized. Set FIREBASE_SERVICE_ACCOUNT_PATH.")

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
OWNER_ADMIN_USERNAME = os.environ.get("C2S_ADMIN_USERNAME", "admin")
OWNER_ADMIN_PASSWORD = os.environ.get("C2S_ADMIN_PASSWORD", "admin@123")
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
        seller_username TEXT,
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
    _safe_alter(cursor, "reviews",  "seller_username", "TEXT")

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






















# ================= HOME =================



# ================= NORMAL LOGIN =================





# ================= OTP LOGIN PAGE =================




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

    message = f"Your COMPARE2SAVE login OTP is {otp}. It expires in {OTP_EXPIRY_MINUTES} minutes."
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






# ================= REGISTER PAGE =================



# ================= REGISTER USER =================



# ================= HOME PAGE =================






# ================= SHOPKEEPER PAGE =================



# ================= ADD MULTIPLE PRODUCTS =================



# ================= CUSTOMER PAGE =================



# ================= SEARCH PRODUCTS =================



# ================= PLACE ORDER =================










# ================= TRACK ORDER =================






# ================= REVIEWS =================





# ================= SHOPKEEPER DASHBOARD =================



# ================= SHOPKEEPER ANALYTICS & EXPORT =================






# ================= DELETE PRODUCT =================



# ================= EDIT PRODUCT =================



# ================= UPDATE PRODUCT =================



# ================= UPDATE ORDER STATUS =================






# ================= SHOPKEEPER ORDERS =================



# ================= UPDATE STATUS =================



# ================= DELETE ORDER =================



# ================= ANALYTICS DASHBOARD =================


# ================= BUY PAGE =================


# ================= SELLER DASHBOARD =================



# ================= PRODUCTS PANEL =================



# ================= ORDERS PANEL =================



# ================= MAPS PANEL =================



# ================= PRODUCT MAP =================




# ================= 3D PRODUCT VIEWER =================



# ================= SETTINGS PANEL =================




# ================= AI CHATBOT =================







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




# ================= REAL-TIME NOTIFICATIONS =================




# ================= INVOICE GENERATOR =================




def ask_chatgpt(user_message, products):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    model = os.getenv("OPENAI_MODEL", "gpt-5.4-mini")
    payload = {
        "model": model,
        "instructions": (
            "You are the AI shopping assistant for COMPARE2SAVE. "
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


# ================= LIVE CHAT =================







# ================= SEND MESSAGE =================



# ================= LOGOUT =================


# ================= ADMIN PANEL =================



# ================= SHOPPING CART =================
















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











# ================= PRODUCT REVIEWS =================










# ================= RUN APP =================





# ================= REGISTER BLUEPRINTS =================
from backend.routes.auth import auth_bp
from backend.routes.customer import customer_bp
from backend.routes.seller import seller_bp
from backend.routes.core import core_bp

app.register_blueprint(auth_bp)
app.register_blueprint(customer_bp)
app.register_blueprint(seller_bp)
app.register_blueprint(core_bp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
