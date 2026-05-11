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
app.secret_key = os.environ.get("NPF_SECRET_KEY", "nearbypricefinder")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
