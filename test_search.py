import sqlite3
import os

DATABASE_PATH = 'database.db'

def test_search():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Add dummy data
    cursor.execute("INSERT INTO products (product_name, shop_name, location, price, product_image, shop_image, seller_username) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                   ('Eggs', 'Shop A', 'Loc A', '10', 'img1.jpg', 'img2.jpg', 'seller1'))
    conn.commit()
    
    # Test search
    search_term = 'egg'
    cursor.execute("SELECT * FROM products WHERE product_name LIKE ?", ('%' + search_term + '%',))
    results = cursor.fetchall()
    print(f"Search for '{search_term}': {len(results)} results found.")
    for r in results:
        print(r)
        
    # Clean up
    cursor.execute("DELETE FROM products WHERE product_name='Eggs'")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    test_search()
