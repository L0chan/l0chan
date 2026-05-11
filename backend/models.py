# pyrefly: ignore [missing-import]
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=True)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='customer')

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    shop_name = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    product_name = db.Column(db.String(150), nullable=False)
    price = db.Column(db.String(50), nullable=False)
    stock = db.Column(db.String(50), nullable=True)
    product_image = db.Column(db.String(255), nullable=False)
    shop_image = db.Column(db.String(255), nullable=False)
    latitude = db.Column(db.String(50), nullable=True)
    longitude = db.Column(db.String(50), nullable=True)

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_name = db.Column(db.String(100), nullable=False)
    product_name = db.Column(db.String(150), nullable=False)
    price = db.Column(db.String(50), nullable=False)
    product_image = db.Column(db.String(255), nullable=True)
    address = db.Column(db.String(255), nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), default='Order Confirmed')
    rider_name = db.Column(db.String(100), nullable=True)
    rider_phone = db.Column(db.String(20), nullable=True)
    delivery_otp = db.Column(db.String(10), nullable=True)
    otp_verified = db.Column(db.String(10), default='No')

class Chat(db.Model):
    __tablename__ = 'chats'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sender = db.Column(db.String(50), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.String(100), nullable=True)
