import re
from pathlib import Path

app_path = Path("backend/app.py")
content = app_path.read_text(encoding="utf-8")

# Extract auth related imports and setup for auth.py
auth_py = """from flask import Blueprint, render_template, request, redirect, session, flash
import sqlite3
import os
import re
import secrets
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import urllib.request
import urllib.parse
import urllib.error
import base64

auth_bp = Blueprint('auth', __name__)
"""

# We'll also need to get some constants from app.py, but for now we'll import them or redefine them in app.py
# Actually, the safest way to refactor without circular imports is to import app.py constants inside the functions, or put them in utils.
# Let's create a utils.py first.

content_utils = """import secrets
import os

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
"""
Path("backend/utils.py").write_text(content_utils, encoding="utf-8")

print("Created utils.py")
