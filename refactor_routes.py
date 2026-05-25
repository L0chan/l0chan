import ast
import os
import re

base_dir = r"d:\NearbyPriceFinder"
app_py_path = os.path.join(base_dir, "backend", "app.py")

with open(app_py_path, "r", encoding="utf-8") as f:
    source_code = f.read()

tree = ast.parse(source_code)

# Classify routes
routes = {
    'auth': ['login', 'api_login', 'otp_login', 'verify_otp_page', 'firebase_login', 'register', 'register_user', 'logout'],
    'customer': ['customer', 'search', 'place_order', 'online_payment', 'cash_on_delivery', 'track_order', 'track_status', 'leave_review', 'submit_review', 'leave_review_page', 'buy', 'view_cart', 'add_to_cart', 'remove_from_cart', 'update_cart', 'checkout', 'api_nearby_products', 'api_all_products', 'api_orders', 'api_product_reviews'],
    'seller': ['shopkeeper', 'add_product', 'shopkeeper_dashboard', 'shopkeeper_analytics', 'export_orders_csv', 'delete_product', 'edit_product', 'update_product', 'shopkeeper_orders', 'update_status', 'delete_order', 'seller_dashboard', 'seller_products', 'seller_orders', 'seller_maps', 'seller_settings', 'seller_stats', 'seller_notifications', 'update_order_status', 'confirm_delivery'],
    'core': ['index', 'home', 'role_dashboard', 'web_manifest', 'service_worker', 'favicon', 'download_app', 'download_windows', 'download_android', 'dashboard', 'admin', 'product_map', 'product_3d', 'payment_demo', 'chatbot', 'chat_response', 'live_chat', 'chat_messages', 'send_message', 'generate_invoice', 'inject_current_account']
}

blueprints_code = {k: [f"from flask import Blueprint, render_template, request, redirect, session, flash, send_from_directory, render_template_string\nimport json, os, secrets\nfrom datetime import datetime, timedelta\nfrom werkzeug.security import check_password_hash, generate_password_hash\n\nfrom backend.utils import *\n\n{k}_bp = Blueprint('{k}', __name__)\n\n"] for k in routes}

core_helpers = ""

def get_source_segment(node):
    lines = source_code.splitlines()
    if hasattr(node, 'decorator_list') and node.decorator_list:
        start = node.decorator_list[0].lineno - 1
    else:
        start = node.lineno - 1
    end = node.end_lineno
    return '\n'.join(lines[start:end])

nodes_to_remove = []

for node in tree.body:
    if isinstance(node, ast.FunctionDef):
        is_route = any(
            isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute) and d.func.attr == 'route'
            for d in node.decorator_list
        ) or any(
            isinstance(d, ast.Attribute) and d.attr == 'context_processor'
            for d in node.decorator_list
        )
        
        if is_route:
            assigned = False
            for bp_name, func_names in routes.items():
                if node.name in func_names:
                    func_code = get_source_segment(node)
                    # Replace @app.route with @bp.route
                    func_code = re.sub(r'@app\.route', f'@{bp_name}_bp.route', func_code)
                    func_code = re.sub(r'@app\.context_processor', f'@{bp_name}_bp.context_processor', func_code)
                    
                    blueprints_code[bp_name].append(func_code)
                    nodes_to_remove.append(node)
                    assigned = True
                    break
            
            if not assigned:
                print(f"Warning: Route {node.name} not assigned to any blueprint!")
                func_code = get_source_segment(node)
                func_code = re.sub(r'@app\.route', f'@core_bp.route', func_code)
                blueprints_code['core'].append(func_code)
                nodes_to_remove.append(node)

print(f"Found {len(nodes_to_remove)} route functions to extract.")

# Now we need to create the files
os.makedirs(os.path.join(base_dir, "backend", "routes"), exist_ok=True)
for bp_name, code_blocks in blueprints_code.items():
    bp_path = os.path.join(base_dir, "backend", "routes", f"{bp_name}.py")
    with open(bp_path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(code_blocks))
    print(f"Created {bp_path}")

# Note: Updating app.py to remove these functions and register blueprints is complex automatically.
# We will just write a new simplified app.py and move helper functions to utils.py
