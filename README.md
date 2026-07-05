<div align="center">

# 🛒 COMPARE2SAVE

### Smart Local Shopping Platform

**Discover nearby products · Compare prices · Track orders live · AI-powered shopping assistant**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.x-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![SQLite](https://img.shields.io/badge/SQLite-Local_DB-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Production-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)
[![PWA](https://img.shields.io/badge/PWA-Installable-5A0FC8?style=for-the-badge&logo=googlechrome&logoColor=white)](https://web.dev/progressive-web-apps)
[![Three.js](https://img.shields.io/badge/Three.js-3D_Viewer-000000?style=for-the-badge&logo=threedotjs&logoColor=white)](https://threejs.org)
[![OpenAI](https://img.shields.io/badge/OpenAI-AI_Assistant-412991?style=for-the-badge&logo=openai&logoColor=white)](https://openai.com)
[![Twilio](https://img.shields.io/badge/Twilio-OTP_Auth-F22F46?style=for-the-badge&logo=twilio&logoColor=white)](https://twilio.com)

</div>

---

## ✨ Features

| Feature | Description |
|---|---|
| 🗺️ **Nearby Product Discovery** | Find products around your location using interactive Leaflet.js maps |
| 🤖 **AI Shopping Assistant** | OpenAI-powered chatbot for product discovery and price queries |
| 📦 **3D Product Viewer** | Inspect products in a 360° interactive Three.js environment |
| 🔐 **OTP Authentication** | Secure phone number verification via Twilio SMS |
| 🔄 **Live Order Tracking** | Real-time order status with live map delivery updates |
| 👥 **Role-Based Dashboards** | Dedicated panels for Customers, Shopkeepers, and Admins |
| 💳 **Flexible Payments** | Cash-on-delivery + UPI QR code payment support |
| 📱 **Progressive Web App** | Install on any device directly from the browser |
| 🏪 **Seller Management** | Full inventory, order, and analytics dashboard for shopkeepers |
| 💬 **Live Chat** | Real-time buyer-seller messaging |

---

## 🛠️ Tech Stack

### Backend
**Python 3.11+** · **Flask 3.x** · **Flask-SQLAlchemy** · **Flask-Login** · **Gunicorn**

### Frontend
**HTML5** · **Vanilla CSS** (Glassmorphism dark theme) · **JavaScript ES6+**  
**React 18** (home page, CDN) · **Jinja2** (server-side templating)

### APIs & Libraries

| Library | Purpose |
|---|---|
| [Three.js](https://threejs.org) | 3D product viewer |
| [Leaflet.js](https://leafletjs.com) | Interactive maps & geolocation |
| [Twilio API](https://twilio.com) | SMS OTP authentication |
| [OpenAI API](https://openai.com) | AI shopping assistant |
| [Cloudinary](https://cloudinary.com) | Cloud image upload & delivery |
| [Lottie Web](https://airbnb.io/lottie) | Animated SVG illustrations |

---

## 📁 Project Structure

```
COMPARE2SAVE/
│
├── backend/                    # Core application logic
│   ├── routes/
│   │   ├── auth.py             # Login, register, OTP flows
│   │   ├── core.py             # Home, search, AI chat routes
│   │   ├── customer.py         # Customer dashboard & orders
│   │   └── seller.py           # Shopkeeper inventory & analytics
│   ├── app.py                  # Flask app with all routes
│   ├── app_factory.py          # Application factory pattern
│   ├── models.py               # SQLAlchemy ORM models
│   ├── database_setup.py       # DB initialization script
│   └── utils.py                # Shared helpers
│
├── frontend/
│   ├── static/
│   │   ├── home.css            # Landing page design system
│   │   ├── global.css          # Shared styles (all pages)
│   │   ├── home.js             # React-powered landing page
│   │   ├── animations.js       # Scroll & entrance animations
│   │   ├── pwa.js              # PWA install prompt logic
│   │   └── service-worker.js   # Offline caching
│   └── templates/              # Jinja2 HTML templates (27 pages)
│       ├── home.html           # Landing page
│       ├── customer.html       # Customer marketplace
│       ├── shopkeeper.html     # Seller product management
│       ├── dashboard.html      # Analytics dashboard
│       ├── track.html          # Live order tracking with maps
│       └── ...
│
├── docs/
│   └── banner.png
│
├── app.py                      # Entry point (ProxyFix for HTTPS)
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variable template
└── .gitignore
```

---

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/COMPARE2SAVE.git
cd COMPARE2SAVE
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Fill in your API keys (see Environment Variables section)
```

### 4. Run the server

```bash
python app.py
```

### 5. Open in browser

```
http://127.0.0.1:5000
```

### Default Admin Login

```
Username: admin
Password: admin@123
```

> Override with `C2S_ADMIN_USERNAME` and `C2S_ADMIN_PASSWORD` environment variables.

---

## ⚙️ Environment Variables

Create a `.env` file (copy from `.env.example`):

```env
# App Security
C2S_SECRET_KEY=change-this-in-production
C2S_ADMIN_USERNAME=admin
C2S_ADMIN_PASSWORD=admin@123

# OpenAI — AI Shopping Assistant
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4o-mini

# Twilio — OTP Authentication
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
TWILIO_FROM_NUMBER=+1234567890

# Database — PostgreSQL for production (SQLite used locally if not set)
DATABASE_URL=postgresql://user:password@host/dbname

# Cloudinary — Image uploads
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
```

---

## 🏗️ Architecture

```
Browser / PWA Client
        │
        │  HTTP / REST API
        ▼
┌───────────────────┐
│   Flask (app.py)  │  ← ProxyFix middleware for HTTPS in production
│   Gunicorn WSGI   │
└────────┬──────────┘
         │
   ┌─────┴──────────────────────────────┐
   │          Route Blueprints           │
   │  auth · core · customer · seller   │
   └─────┬──────────────────────────────┘
         │
   ┌─────┴──────────────┐
   │  SQLAlchemy ORM    │
   └──────┬──────┬──────┘
          │      │
      SQLite  PostgreSQL
      (local) (production)
```

---

## 📱 Install as PWA

1. Start the Flask server
2. Open in **Chrome** or **Edge**
3. Click the **install icon** (⊕) in the address bar

The app installs to your desktop or mobile home screen for a native-like experience — no app store required.

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit changes: `git commit -m 'feat: add your feature'`
4. Push: `git push origin feature/your-feature`
5. Open a Pull Request

---

## 📄 License

Open source. Use freely for learning, personal projects, or as a foundation for your own marketplace.

---

<div align="center">
  <p>Built with ❤️ using Python, Flask, and modern web technologies.</p>
  <strong>⭐ Star this repo if you found it useful!</strong>
</div>
