# database.py

from pathlib import Path

import sqlite3


BASE_DIR = Path(__file__).resolve().parents[1]
DATABASE_PATH = BASE_DIR / "database.db"


# DATABASE CONNECTION
def get_db():

    conn = sqlite3.connect(DATABASE_PATH)

    conn.row_factory = sqlite3.Row

    return conn


# CREATE TABLES
def create_tables():

    conn = get_db()

    # USERS TABLE
    conn.execute("""

    CREATE TABLE IF NOT EXISTS users(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        username TEXT UNIQUE NOT NULL,

        password TEXT NOT NULL,

        created_at TIMESTAMP
        DEFAULT CURRENT_TIMESTAMP

    )

    """)

    # PRODUCTS TABLE
    conn.execute("""

    CREATE TABLE IF NOT EXISTS products(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        shop_name TEXT NOT NULL,

        location TEXT NOT NULL,

        latitude REAL NOT NULL,

        longitude REAL NOT NULL,

        category TEXT NOT NULL,

        product_name TEXT NOT NULL,

        description TEXT,

        stock INTEGER DEFAULT 0,

        price REAL NOT NULL,

        shop_image TEXT,

        image TEXT,

        created_at TIMESTAMP
        DEFAULT CURRENT_TIMESTAMP

    )

    """)

    # ORDERS TABLE
    conn.execute("""

    CREATE TABLE IF NOT EXISTS orders(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        customer_name TEXT NOT NULL,

        address TEXT NOT NULL,

        product_name TEXT NOT NULL,

        quantity INTEGER DEFAULT 1,

        total_price REAL NOT NULL,

        shop_name TEXT NOT NULL,

        payment_method TEXT,

        status TEXT
        DEFAULT 'Pending',

        created_at TIMESTAMP
        DEFAULT CURRENT_TIMESTAMP

    )

    """)

    # CHAT TABLE
    conn.execute("""

    CREATE TABLE IF NOT EXISTS chats(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        sender TEXT,

        receiver TEXT,

        message TEXT,

        created_at TIMESTAMP
        DEFAULT CURRENT_TIMESTAMP

    )

    """)

    conn.commit()

    conn.close()


create_tables()

print("Database Created Successfully")
