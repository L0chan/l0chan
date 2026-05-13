"""
Fix orphan products: products added before the seller_username column existed.
These products have NULL seller_username and appear in customer search
but do NOT belong to any shopkeeper's dashboard.

Run this script to DELETE them from the database.
"""
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "database.db")

conn = sqlite3.connect(DATABASE_PATH)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute("SELECT id, product_name, seller_username FROM products WHERE seller_username IS NULL OR seller_username = ''")
orphans = cursor.fetchall()

if not orphans:
    print("No orphan products found. All products have a seller assigned. ✅")
    conn.close()
else:
    print(f"Found {len(orphans)} orphan product(s) with no owner:")
    for p in orphans:
        print(f"  ID={p['id']}, Name='{p['product_name']}'")

    confirm = input("\nDelete these orphan products? (yes/no): ").strip().lower()
    if confirm == "yes":
        cursor.execute("DELETE FROM products WHERE seller_username IS NULL OR seller_username = ''")
        conn.commit()
        print(f"Deleted {cursor.rowcount} orphan product(s). ✅")
    else:
        print("Skipped deletion. Orphan products remain in the database.")

conn.close()
