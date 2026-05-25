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

core_bp = Blueprint('core', __name__)



@core_bp.context_processor
def inject_current_account():
    return {
        "current_user": session.get("user", "Guest"),
        "current_role": normalize_role(session.get("role")),
        "is_owner_admin": bool(session.get("is_owner_admin")),
    }

@core_bp.route("/manifest.json")
def web_manifest():
    return send_from_directory(app.static_folder, "manifest.json", mimetype="application/manifest+json")

@core_bp.route("/service-worker.js")
def service_worker():
    return send_from_directory(app.static_folder, "service-worker.js", mimetype="application/javascript")

@core_bp.route("/favicon.ico")
def favicon():
    return send_from_directory(app.static_folder, "app-icon.svg", mimetype="image/svg+xml")

@core_bp.route("/download_app")
def download_app():
    windows_zip = RELEASE_DIR / "COMPARE2SAVE-Windows.zip"
    android_apk = RELEASE_DIR / "COMPARE2SAVE-Android.apk"
    return render_template(
        "download_app.html",
        windows_zip_exists=windows_zip.exists(),
        android_apk_exists=android_apk.exists(),
    )

@core_bp.route("/download/windows")
def download_windows():
    windows_zip = RELEASE_DIR / "COMPARE2SAVE-Windows.zip"

    if not windows_zip.exists():
        return "Windows download is not built yet. Run make_downloads.bat first.", 404

    return send_from_directory(RELEASE_DIR, windows_zip.name, as_attachment=True)

@core_bp.route("/download/android")
def download_android():
    android_apk = RELEASE_DIR / "COMPARE2SAVE-Android.apk"

    if android_apk.exists():
        return send_from_directory(RELEASE_DIR, android_apk.name, as_attachment=True)

    return render_template("android_download.html")

@core_bp.route("/")
def index():
    return render_template("login.html")

@core_bp.route("/home")
@role_required("customer", "admin")
def home():
    return render_template("home.html")

@core_bp.route("/role_dashboard")
def role_dashboard():
    return redirect(dashboard_for_role(session.get("role")))

@core_bp.route("/dashboard")
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

@core_bp.route("/product_map/<int:product_id>")
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

@core_bp.route("/product_3d/<int:product_id>")
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

@core_bp.route("/payment_demo")
def payment_demo():

    return render_template(
        "buy.html",
        product_name="Demo Product",
        price="999",
        product_image="/static/demo.jpg"
    )

@core_bp.route("/chatbot")
@role_required("customer", "admin")
def chatbot():
    return render_template("chatbot.html")



@core_bp.route("/invoice/<int:order_id>")
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
                <div class="logo">COMPARE2SAVE</div>
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
                Thank you for shopping locally with COMPARE2SAVE!<br>
                This is a computer-generated invoice.
            </div>
            
            <div style="margin-top: 30px; text-align: center;" class="no-print">
                <button onclick="window.print()" style="padding: 10px 20px; border-radius: 8px; background: #22d3ee; border: none; font-weight: 800; cursor: pointer;">🖨️ Print Invoice</button>
            </div>
        </div>
    </body>
    </html>
    """, order=order)

@core_bp.route("/chat_response", methods=["POST"])
def chat_response():

    raw_message = request.form.get("message", "").strip()

    if not raw_message:
        return {"reply": "Please type a product name or shopping question."}

    products = find_matching_products(raw_message)
    chatgpt_reply = ask_chatgpt(raw_message, products)

    return {
        "reply": chatgpt_reply or local_chatbot_reply(raw_message, products)
    }

@core_bp.route("/live_chat")
def live_chat():

    return render_template(
        "live_chat.html",
        current_user=session.get("user", "Guest")
    )

@core_bp.route("/chat_messages")
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

@core_bp.route("/send_message", methods=["POST"])
def send_message():

    # SECURITY: Use session identity — never trust the client to tell us who they are
    sender = session.get("user", "Guest")
    sender_role = session.get("role", "customer")

    message = request.form.get("message", "").strip()

    if not message:
        return {"success": False, "error": "Message is required."}, 400

    # Limit message length to prevent spam/abuse
    if len(message) > 500:
        message = message[:500]

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

@core_bp.route("/admin/clear_products", methods=["POST"])
@role_required("admin")
def clear_products():
    try:
        conn = get_db_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM products")
        row = cursor.fetchone()
        count = row[0] if row else 0
        cursor.execute("DELETE FROM products")
        conn.commit()
        conn.close()
        return {"success": True, "deleted": count}
    except Exception as e:
        return {"success": False, "error": str(e)}, 500

@core_bp.route("/admin/clear_orders", methods=["POST"])
@role_required("admin")
def clear_orders():
    try:
        conn = get_db_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM orders")
        row = cursor.fetchone()
        count = row[0] if row else 0
        cursor.execute("DELETE FROM orders")
        conn.commit()
        conn.close()
        return {"success": True, "deleted": count}
    except Exception as e:
        return {"success": False, "error": str(e)}, 500

@core_bp.route("/admin")
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