import os
import re

base_dir = r"d:\NearbyPriceFinder"
app_py_path = os.path.join(base_dir, "backend", "app.py")
utils_py_path = os.path.join(base_dir, "backend", "utils.py")

with open(app_py_path, "r", encoding="utf-8") as f:
    app_content = f.read()

# We want to remove all @app.route and @app.context_processor functions from app.py
import ast

tree = ast.parse(app_content)

def get_source_segment(node):
    lines = app_content.splitlines()
    if hasattr(node, 'decorator_list') and node.decorator_list:
        start = node.decorator_list[0].lineno - 1
    else:
        start = node.lineno - 1
    end = node.end_lineno
    return '\n'.join(lines[start:end])

# Identify routes to remove
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
            nodes_to_remove.append(get_source_segment(node))

# Remove them from app_content
new_app_content = app_content
for chunk in nodes_to_remove:
    new_app_content = new_app_content.replace(chunk, "")

# Now new_app_content contains all the setup, database connection, imports, etc.
# We will just append the blueprint registrations at the end of new_app_content!
# This is much safer than splitting everything into utils.py.

blueprint_registration = """

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
"""

# Remove the old if __name__ block if it exists
new_app_content = re.sub(r'if __name__ == "__main__":.*?app\.run\(.*?\)', '', new_app_content, flags=re.DOTALL)

# Append registrations
new_app_content += blueprint_registration

with open(app_py_path, "w", encoding="utf-8") as f:
    f.write(new_app_content)

# But wait, the blueprints import `from backend.utils import *`.
# They need access to `get_db_conn`, `role_required`, etc.
# So we should put `get_db_conn` and other helpers in `utils.py`.
# Actually, the easiest way is to have blueprints `from backend.app import get_db_conn, role_required, ...`
# Let's fix the blueprints to import from backend.app instead of backend.utils!

for bp_name in ['auth', 'customer', 'seller', 'core']:
    bp_path = os.path.join(base_dir, "backend", "routes", f"{bp_name}.py")
    with open(bp_path, "r", encoding="utf-8") as f:
        bp_content = f.read()
    
    # Replace from backend.utils import * with from backend.app import *
    bp_content = bp_content.replace("from backend.utils import *", "from backend.app import *\nfrom backend.utils import *\nfrom backend.app_factory import app\nimport urllib.request\nimport urllib.parse\nimport urllib.error\nimport base64")
    
    # Also add firebase_admin auth import if needed in auth.py
    if bp_name == 'auth':
        bp_content = bp_content.replace("from backend.app import *", "from backend.app import *\nfrom firebase_admin import auth\n")
    
    with open(bp_path, "w", encoding="utf-8") as f:
        f.write(bp_content)

print("Finalized refactoring!")
