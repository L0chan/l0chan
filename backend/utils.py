import secrets
import os

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
