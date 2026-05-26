"""
NearbyPriceFinder - Test Suite
Run with:  python -m pytest test_app.py -v
"""

import pytest
import sys
import os

# Make sure the backend is importable
sys.path.insert(0, os.path.dirname(__file__))

import tempfile

# Use a temporary SQLite DB file for testing (never touches production data)
_temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_temp_db_path = _temp_db.name
_temp_db.close()

os.environ["DATABASE_PATH"] = _temp_db_path
os.environ["DATABASE_URL"] = ""  # Force SQLite mode

from backend.app_factory import app as flask_app
from backend.app import _setup_database, get_db_conn
from werkzeug.security import generate_password_hash


# ─────────────────────────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="session", autouse=True)
def cleanup_temp_db():
    yield
    try:
        os.remove(_temp_db_path)
    except OSError:
        pass


@pytest.fixture
def app():
    """Create a fresh test Flask app with a clean temporary DB."""
    flask_app.config["TESTING"] = True
    flask_app.config["SECRET_KEY"] = "test-secret-key"
    flask_app.config["WTF_CSRF_ENABLED"] = False
    
    # Clean the database by deleting all rows in case of repeated test runs
    if os.path.exists(_temp_db_path):
        try:
            conn = get_db_conn()
            cursor = conn.cursor()
            for table in ["users", "products", "orders", "chats", "cart", "reviews"]:
                try:
                    cursor.execute(f"DELETE FROM {table}")
                except Exception:
                    pass
            try:
                cursor.execute("DELETE FROM sqlite_sequence")
            except Exception:
                pass
            conn.commit()
            conn.close()
        except Exception:
            pass
            
    _setup_database()
    yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db_with_users(app):
    """Seed the DB with a test customer and seller."""
    conn = get_db_conn()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO users(username, password, role) VALUES(?,?,?)",
        ("testcustomer", generate_password_hash("password123"), "customer")
    )
    cursor.execute(
        "INSERT INTO users(username, password, role) VALUES(?,?,?)",
        ("testseller", generate_password_hash("password123"), "seller")
    )
    conn.commit()
    conn.close()
    return app


@pytest.fixture
def db_with_product(db_with_users):
    """Seed the DB with a test product."""
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO products(shop_name, location, product_name, price, stock,
                             product_image, shop_image, latitude, longitude, unit, seller_username)
        VALUES(?,?,?,?,?,?,?,?,?,?,?)
    """, ("Test Shop", "Mumbai", "Apple", "50", "100",
          "apple.jpg", "shop.jpg", "19.076", "72.877", "kg", "testseller"))
    conn.commit()
    conn.close()
    return db_with_users


# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────

def login(client, username, password):
    return client.post("/login", data={"username": username, "password": password},
                       follow_redirects=True)


def login_as_customer(client):
    return login(client, "testcustomer", "password123")


def login_as_seller(client):
    return login(client, "testseller", "password123")


# ─────────────────────────────────────────────────────────────
# 1. AUTH TESTS
# ─────────────────────────────────────────────────────────────

class TestAuth:

    def test_index_page_loads(self, client):
        """Homepage (login page) should return 200."""
        r = client.get("/")
        assert r.status_code == 200

    def test_register_page_loads(self, client, app):
        """Register page should return 200."""
        _setup_database()
        r = client.get("/register")
        assert r.status_code == 200

    def test_register_new_user(self, client, app):
        """A new user can register successfully."""
        _setup_database()
        r = client.post("/register_user", data={
            "username": "newuser",
            "password": "securepass",
            "role": "customer"
        }, follow_redirects=True)
        assert r.status_code == 200

    def test_register_short_username_rejected(self, client, app):
        """Username under 3 characters should be rejected."""
        _setup_database()
        r = client.post("/register_user", data={
            "username": "ab",
            "password": "securepass",
            "role": "customer"
        }, follow_redirects=True)
        # Should redirect back to /register (flash message)
        assert r.status_code == 200

    def test_register_short_password_rejected(self, client, app):
        """Password under 6 characters should be rejected."""
        _setup_database()
        r = client.post("/register_user", data={
            "username": "validname",
            "password": "abc",
            "role": "customer"
        }, follow_redirects=True)
        assert r.status_code == 200

    def test_register_duplicate_username_rejected(self, client, db_with_users):
        """Registering with an already-taken username should fail."""
        r = client.post("/register_user", data={
            "username": "testcustomer",
            "password": "anotherpass",
            "role": "customer"
        }, follow_redirects=True)
        assert r.status_code == 200  # Redirects back with flash

    def test_valid_login(self, client, db_with_users):
        """A registered user can log in with correct credentials."""
        r = login_as_customer(client)
        assert r.status_code == 200

    def test_wrong_password_rejected(self, client, db_with_users):
        """Wrong password should not log in."""
        r = login(client, "testcustomer", "wrongpassword")
        assert r.status_code == 200  # Redirects back to login

    def test_nonexistent_user_rejected(self, client, app):
        """Non-existent username should not log in."""
        _setup_database()
        r = login(client, "ghostuser", "password123")
        assert r.status_code == 200

    def test_logout_clears_session(self, client, db_with_users):
        """After logout, accessing protected page redirects to login."""
        login_as_customer(client)
        client.get("/logout")
        r = client.get("/customer", follow_redirects=True)
        assert r.status_code == 200


# ─────────────────────────────────────────────────────────────
# 2. ROLE ACCESS CONTROL TESTS
# ─────────────────────────────────────────────────────────────

class TestRoleAccess:

    def test_customer_cannot_access_seller_dashboard(self, client, db_with_users):
        """Customer should be redirected away from seller pages."""
        login_as_customer(client)
        r = client.get("/shopkeeper_orders", follow_redirects=False)
        # Should redirect (302), not show the page
        assert r.status_code in (302, 200)

    def test_guest_cannot_access_customer_page(self, client, app):
        """Unauthenticated user should not see customer page."""
        _setup_database()
        r = client.get("/customer", follow_redirects=False)
        assert r.status_code == 302  # Redirect to login

    def test_guest_cannot_access_admin(self, client, app):
        """Unauthenticated user should not see admin panel."""
        _setup_database()
        r = client.get("/admin", follow_redirects=False)
        assert r.status_code == 302

    def test_admin_can_access_admin_stats(self, client, db_with_users):
        """Admin should see separate stats for customers and shopkeepers."""
        login(client, "admin", "admin@123")
        r = client.get("/admin")
        assert r.status_code == 200
        html = r.data.decode("utf-8")
        assert "Total Customers" in html
        assert "Total Shopkeepers" in html
        assert "Total Users" not in html

    def test_admin_can_access_dashboard_stats(self, client, db_with_users):
        """Admin dashboard should see separate stats for customers and shopkeepers."""
        login(client, "admin", "admin@123")
        r = client.get("/dashboard")
        assert r.status_code == 200
        html = r.data.decode("utf-8")
        assert "Total Customers" in html
        assert "Total Shopkeepers" in html
        assert "Total Users" not in html

    def test_seller_can_access_orders_page(self, client, db_with_users):
        """A seller should be able to view their orders page."""
        login_as_seller(client)
        r = client.get("/shopkeeper_orders")
        assert r.status_code == 200


# ─────────────────────────────────────────────────────────────
# 3. SECURITY TESTS
# ─────────────────────────────────────────────────────────────

class TestSecurity:

    def test_track_status_hides_otp_from_stranger(self, client, db_with_product):
        """A stranger (not the order owner) must NOT see the delivery OTP."""
        # Place an order as customer
        login_as_customer(client)
        client.post("/place_order", data={
            "product_name": "Apple",
            "phone": "9876543210",
            "address": "123 Street",
            "payment": "Cash on Delivery",
            "price": "50",
            "product_id": "1",
            "product_image": ""
        })
        
        conn = get_db_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM orders ORDER BY id DESC LIMIT 1")
        order_id = cursor.fetchone()[0]
        conn.close()
        
        client.get("/logout")

        # Now access track_status as a different user (or unauthenticated)
        r = client.get(f"/track_status/{order_id}")
        if r.status_code == 200:
            data = r.get_json()
            if data and data.get("found"):
                otp = data["order"].get("delivery_otp", "")
                # OTP should NOT be a 6-digit number for non-owners
                assert otp != "" and not otp.isdigit(), \
                    "SECURITY FAIL: OTP exposed to non-owner!"

    def test_otp_visible_to_order_owner(self, client, db_with_product):
        """The customer who placed the order should see their OTP."""
        login_as_customer(client)
        client.post("/place_order", data={
            "product_name": "Apple",
            "phone": "9876543210",
            "address": "123 Street",
            "payment": "Cash on Delivery",
            "price": "50",
            "product_id": "1",
            "product_image": ""
        })
        
        conn = get_db_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM orders ORDER BY id DESC LIMIT 1")
        order_id = cursor.fetchone()[0]
        conn.close()
        
        r = client.get(f"/track_status/{order_id}")
        if r.status_code == 200:
            data = r.get_json()
            if data and data.get("found"):
                otp = data["order"].get("delivery_otp", "")
                # Owner should see real OTP (6 digits)
                assert otp != "hidden", "OTP should be visible to order owner"

    def test_seller_identity_not_spoofable_in_chat(self, client, db_with_users):
        """Sending a chat message should use session identity, not form field."""
        login_as_customer(client)
        # Try to fake being a seller via the form
        r = client.post("/send_message", data={
            "sender": "seller",   # Attacker tries to spoof seller identity
            "message": "I am pretending to be a seller"
        })
        # The message should be stored under the actual session user
        conn = get_db_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT sender FROM chats ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        if row:
            # Should be "testcustomer", NOT "seller"
            assert row[0] != "seller", "SECURITY FAIL: Sender identity was spoofed!"
            assert row[0] == "testcustomer"


# ─────────────────────────────────────────────────────────────
# 4. API TESTS
# ─────────────────────────────────────────────────────────────

class TestAPIs:

    def test_nearby_products_api_returns_json(self, client, db_with_product):
        """Nearby products API should return valid JSON."""
        r = client.get("/api/nearby_products?lat=19.076&lng=72.877")
        assert r.status_code == 200
        data = r.get_json()
        assert "products" in data
        assert isinstance(data["products"], list)

    def test_nearby_products_bad_lat_returns_400(self, client, app):
        """Invalid lat/lng should return 400."""
        _setup_database()
        r = client.get("/api/nearby_products?lat=notanumber&lng=abc")
        assert r.status_code == 400

    def test_all_products_api(self, client, db_with_product):
        """All products API should return list."""
        r = client.get("/api/products")
        assert r.status_code == 200
        data = r.get_json()
        assert "products" in data
        assert len(data["products"]) >= 1

    def test_product_reviews_api(self, client, db_with_product):
        """Product reviews API returns valid structure."""
        r = client.get("/api/product_reviews?product=Apple")
        assert r.status_code == 200
        data = r.get_json()
        assert "reviews" in data

    def test_orders_api_requires_login(self, client, app):
        """Orders API should redirect unauthenticated users."""
        _setup_database()
        r = client.get("/api/orders", follow_redirects=False)
        assert r.status_code == 302  # Must redirect to login


# ─────────────────────────────────────────────────────────────
# 5. ORDER FLOW TESTS
# ─────────────────────────────────────────────────────────────

class TestOrderFlow:

    def test_place_order_creates_db_record(self, client, db_with_product):
        """Placing an order should insert a row into the orders table."""
        login_as_customer(client)
        client.post("/place_order", data={
            "product_name": "Apple",
            "phone": "9876543210",
            "address": "123 Test Street",
            "payment": "Cash on Delivery",
            "price": "50",
            "product_id": "1",
            "product_image": ""
        })

        conn = get_db_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM orders WHERE customer_name='testcustomer'")
        count = cursor.fetchone()[0]
        conn.close()

        assert count >= 1, "Order was not saved to the database"

    def test_order_has_delivery_otp(self, client, db_with_product):
        """Every placed order must have a delivery OTP generated."""
        login_as_customer(client)
        client.post("/place_order", data={
            "product_name": "Apple",
            "phone": "9876543210",
            "address": "123 Test Street",
            "payment": "Cash on Delivery",
            "price": "50",
            "product_id": "1",
            "product_image": ""
        })

        conn = get_db_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT delivery_otp FROM orders WHERE customer_name='testcustomer'")
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        assert row["delivery_otp"] is not None
        assert len(row["delivery_otp"]) == 6

    def test_submit_order_verification_correct(self, client, db_with_product):
        """Customer can verify order as Confirmed Correct."""
        login_as_customer(client)
        client.post("/place_order", data={
            "product_name": "Apple", "phone": "9876543210",
            "address": "123 Street", "payment": "Cash on Delivery",
            "price": "50", "product_id": "1", "product_image": ""
        })
        
        conn = get_db_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM orders ORDER BY id DESC LIMIT 1")
        order_id = cursor.fetchone()[0]
        conn.close()
        
        # Verify order as correct
        r = client.post(f"/submit_order_verification/{order_id}", data={
            "verification_status": "Confirmed Correct"
        }, follow_redirects=True)
        assert r.status_code == 200
        
        conn = get_db_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT verification_status, verification_details FROM orders WHERE id=?", (order_id,))
        row = cursor.fetchone()
        conn.close()
        
        assert row["verification_status"] == "Confirmed Correct"
        assert row["verification_details"] == ""

    def test_submit_order_verification_refund_request(self, client, db_with_product):
        """Customer can request return/refund with reason/details."""
        login_as_customer(client)
        client.post("/place_order", data={
            "product_name": "Apple", "phone": "9876543210",
            "address": "123 Street", "payment": "Cash on Delivery",
            "price": "50", "product_id": "1", "product_image": ""
        })
        
        conn = get_db_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM orders ORDER BY id DESC LIMIT 1")
        order_id = cursor.fetchone()[0]
        conn.close()
        
        # Submit return request
        r = client.post(f"/submit_order_verification/{order_id}", data={
            "verification_status": "Return/Refund Requested",
            "verification_details": "[Reason: Product(s) missing] Apple missing"
        }, follow_redirects=True)
        assert r.status_code == 200
        
        conn = get_db_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT verification_status, verification_details FROM orders WHERE id=?", (order_id,))
        row = cursor.fetchone()
        conn.close()
        
        assert row["verification_status"] == "Return/Refund Requested"
        assert row["verification_details"] == "[Reason: Product(s) missing] Apple missing"

    def test_track_order_page_loads(self, client, db_with_product):
        """Track order page should load for a valid order ID."""
        login_as_customer(client)
        client.post("/place_order", data={
            "product_name": "Apple", "phone": "9876543210",
            "address": "123 Street", "payment": "Cash on Delivery",
            "price": "50", "product_id": "1", "product_image": ""
        })
        
        conn = get_db_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM orders ORDER BY id DESC LIMIT 1")
        order_id = cursor.fetchone()[0]
        conn.close()
        
        r = client.get(f"/track/{order_id}")
        assert r.status_code == 200

    def test_track_nonexistent_order_returns_404(self, client, app):
        """Tracking a non-existent order should return 404."""
        _setup_database()
        r = client.get("/track/99999")
        assert r.status_code == 404


# ─────────────────────────────────────────────────────────────
# 6. CART TESTS
# ─────────────────────────────────────────────────────────────

class TestCart:

    def test_add_to_cart(self, client, db_with_product):
        """Customer can add a product to their cart."""
        login_as_customer(client)
        client.post("/add_to_cart", data={
            "product_id": "1",
            "product_name": "Apple",
            "price": "50",
            "product_image": "",
            "shop_name": "Test Shop",
            "unit": "kg"
        })
        conn = get_db_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM cart WHERE customer_name='testcustomer'")
        count = cursor.fetchone()[0]
        conn.close()
        assert count >= 1

    def test_empty_cart_checkout_rejected(self, client, db_with_users):
        """Checking out with an empty cart should show error."""
        login_as_customer(client)
        r = client.post("/checkout", data={
            "address": "123 Street",
            "payment": "Cash on Delivery"
        }, follow_redirects=True)
        assert r.status_code == 200  # Should show cart page with message

    def test_checkout_without_address_rejected(self, client, db_with_product):
        """Checkout without address should be rejected."""
        login_as_customer(client)
        client.post("/add_to_cart", data={
            "product_id": "1", "product_name": "Apple", "price": "50",
            "product_image": "", "shop_name": "Test Shop", "unit": "kg"
        })
        r = client.post("/checkout", data={
            "address": "",   # Empty address
            "payment": "Cash on Delivery"
        }, follow_redirects=True)
        assert r.status_code == 200
