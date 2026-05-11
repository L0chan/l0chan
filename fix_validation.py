import re
from pathlib import Path

app_path = Path("backend/app.py")
content = app_path.read_text(encoding="utf-8")

# Add allowed_file function after UPLOAD_FOLDER def
if "def allowed_file(" not in content:
    content = content.replace('app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER',
'''app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
''')

# Add validation to add_product for shop image
target_shop = """    if not shop_images or not shop_images[0] or not shop_images[0].filename:
        return "Shop image is required.", 400"""

replacement_shop = """    if not shop_images or not shop_images[0] or not shop_images[0].filename:
        return "Shop image is required.", 400
    if not allowed_file(shop_images[0].filename):
        return "Invalid shop image format.", 400"""

content = content.replace(target_shop, replacement_shop)

# Add validation to add_product for product image
target_product = """        if not product_image or not product_image.filename:
            conn.close()
            return "Product image is required.", 400"""

replacement_product = """        if not product_image or not product_image.filename:
            conn.close()
            return "Product image is required.", 400
        if not allowed_file(product_image.filename):
            conn.close()
            return "Invalid product image format.", 400"""

content = content.replace(target_product, replacement_product)

app_path.write_text(content, encoding="utf-8")
print("Done validating")
