from flask import Blueprint, render_template, request, redirect, session, flash, send_from_directory, render_template_string
import json, os, secrets
from datetime import datetime, timedelta
from werkzeug.security import check_password_hash, generate_password_hash

from backend.app import *
from firebase_admin import auth

from backend.utils import *
from backend.app_factory import app
import urllib.request
import urllib.parse
import urllib.error
import base64

auth_bp = Blueprint('auth', __name__)



@auth_bp.route("/login", methods=["POST"])
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
        # SECURITY: Only accept properly hashed passwords
        if db_password.startswith("scrypt:") or db_password.startswith("pbkdf2:"):
            is_valid = check_password_hash(db_password, password)
        # Plain-text fallback intentionally removed — use hashed passwords only

    if is_valid:
        session["user"] = username
        role = normalize_role(user["role"])
        session["role"] = role if role != "admin" else "customer"
        session["is_owner_admin"] = False
        return redirect(dashboard_for_role(session["role"]))
    else:
        flash("Invalid username or password.")
        return redirect("/")

@auth_bp.route("/api/login", methods=["POST"])
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
        session["role"] = normalize_role(user["role"])
        return {"success": True, "user": username, "role": session["role"]}
    
    return {"success": False, "message": "Invalid credentials"}, 401

@auth_bp.route("/api/register", methods=["POST"])
def api_register():
    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    role = normalize_public_role(data.get("role"))

    if not username or not password:
        return {"success": False, "message": "Username and password are required."}, 400

    if len(username) < 3 or len(username) > 30:
        return {"success": False, "message": "Username must be between 3 and 30 characters."}, 400

    if len(password) < 6:
        return {"success": False, "message": "Password must be at least 6 characters."}, 400

    conn = get_db_conn()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE username=?", (username,))
    if cursor.fetchone():
        conn.close()
        return {"success": False, "message": "Username already taken."}, 400

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
    session["is_owner_admin"] = False

    return {"success": True, "user": username, "role": role}

@auth_bp.route("/otp_login")
def otp_login():
    return render_template("otp_login.html")

@auth_bp.route("/verify_otp_page")
def verify_otp_page():
    return render_template("verify_otp.html")

@auth_bp.route("/firebase_login", methods=["POST"])
def firebase_login():
    data = request.json
    id_token = data.get("id_token")

    try:
        # Verify the ID token sent from the client
        decoded_token = auth.verify_id_token(id_token)
        phone_number = decoded_token.get("phone_number")
        
        # Log the user in
        session["user"] = phone_number
        session["role"] = "customer" # Default role for phone login
        session["is_owner_admin"] = False
        
        return {"success": True, "redirect": dashboard_for_role("customer")}
    except Exception as e:
        print(f"Firebase Auth Error: {str(e)}")
        return {"success": False, "message": "Invalid authentication token"}, 401

@auth_bp.route("/register")
def register():
    return render_template("register.html")

@auth_bp.route("/register_user", methods=["POST"])
def register_user():

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()
    role = normalize_public_role(request.form.get("role"))

    # --- Input Validation ---
    if not username or not password:
        flash("Username and password are required.")
        return redirect("/register")

    if len(username) < 3 or len(username) > 30:
        flash("Username must be between 3 and 30 characters.")
        return redirect("/register")

    if len(password) < 6:
        flash("Password must be at least 6 characters.")
        return redirect("/register")

    conn = get_db_conn()
    cursor = conn.cursor()

    # --- Duplicate username check ---
    cursor.execute("SELECT id FROM users WHERE username=?", (username,))
    if cursor.fetchone():
        conn.close()
        flash("Username already taken. Please choose another.")
        return redirect("/register")

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
    session["is_owner_admin"] = False

    return redirect(dashboard_for_role(role))

@auth_bp.route("/logout")
def logout():

    session.clear()

    return redirect("/")