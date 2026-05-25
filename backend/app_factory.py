from flask import Flask
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = BASE_DIR / "frontend"
UPLOAD_FOLDER = str(FRONTEND_DIR / "static" / "uploads")

app = Flask(
    __name__,
    template_folder=str(FRONTEND_DIR / "templates"),
    static_folder=str(FRONTEND_DIR / "static"),
    static_url_path="/static",
)
app.secret_key = os.environ.get("C2S_SECRET_KEY", "compare2save")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# --- SESSION CONFIG FOR PRODUCTION ---
# Ensures cookies work correctly behind proxies like Render
if os.environ.get("RENDER") or not os.environ.get("C2S_DEV"):
    app.config.update(
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
    )

import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url

# --- CLOUDINARY CONFIGURATION ---
cloudinary.config(
    cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key = os.environ.get("CLOUDINARY_API_KEY"),
    api_secret = os.environ.get("CLOUDINARY_API_SECRET"),
    secure = True
)
