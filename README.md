# COMPARE2SAVE

COMPARE2SAVE is a comprehensive, full-stack marketplace and local product discovery application. It connects customers with local shopkeepers, enabling seamless inventory management, geographical product tracking, secure authentication, and a modern shopping experience.

## ✨ Key Features

*   **Role-Based Access Control (RBAC):** Secure, dedicated dashboards for `Customers`, `Shopkeepers`, and `Owner Admins`. Strict routing prevents unauthorized access to restricted panels.
*   **Twilio OTP Authentication:** Phone number verification and secure login flows using SMS-based One-Time Passwords.
*   **Interactive 3D Product Viewer:** Customers can view products in a fully interactive 360-degree 3D environment built with `Three.js`.
*   **Geolocation & Live Maps:** Interactive maps to track order delivery status and find nearby seller locations.
*   **AI Shopping Assistant:** Integrated OpenAI-powered chatbot to assist customers with product discovery and queries.
*   **Clean Dark Theme UI:** A professional, fully responsive, "man-made" dark theme, offering an impressive and structured aesthetic across all devices.
*   **Live Chat:** Real-time messaging system allowing direct communication between buyers and sellers.
*   **Progressive Web App (PWA):** Installable on desktops and mobile devices directly from the browser for a native-like experience.

## 🛠️ Technology Stack

*   **Backend:** Python, Flask, Flask-SQLAlchemy (ORM), Flask-Login
*   **Database:** SQLite (Local development)
*   **Frontend:** HTML5, Vanilla CSS (Clean Dark Theme), JavaScript (ES6)
*   **Libraries & APIs:** Three.js (3D Rendering), Twilio API (SMS Auth), OpenAI API (Chatbot), Leaflet.js (Maps)

## 📁 Project Structure

```text
COMPARE2SAVE/
├── backend/                  # Flask application factory, routes, and models
│   ├── auth/                 # Authentication & OTP logic
│   ├── shopkeeper/           # Seller inventory and dashboard logic
│   └── models.py             # SQLAlchemy database models
├── frontend/                 # Static assets and templates
│   ├── static/               # CSS themes, JavaScript, and uploaded images
│   └── templates/            # Jinja2 HTML templates
├── mobile_app/               # Capacitor/offline-first mobile wrapper
├── app.py                    # Main application entry point
├── database.db               # SQLite Database
└── requirements.txt          # Python dependencies
```

## 🚀 Run the Web App Locally

1. **Install dependencies:**
```powershell
python -m pip install -r requirements.txt
```

2. **Run the server:**
```powershell
python app.py
```

3. **Open in browser:**
Navigate to `http://127.0.0.1:5000`

### Default Admin Login
```text
username: admin
password: admin@123
```
*(You can override these values using the `C2S_ADMIN_USERNAME` and `C2S_ADMIN_PASSWORD` environment variables.)*

## ⚙️ Environment Variables

For production or full feature functionality, set the following environment variables (e.g., in a `.env` file):

```text
C2S_SECRET_KEY=change-this-for-production
C2S_ADMIN_USERNAME=admin
C2S_ADMIN_PASSWORD=admin@123
OPENAI_API_KEY=your-openai-key
OPENAI_MODEL=gpt-4o-mini
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_FROM_NUMBER=your-twilio-phone-number
DATABASE_URL=postgres://user:password@host/dbname # (Optional) Use for production PostgreSQL, otherwise uses local SQLite
```

## 📱 Desktop & Mobile Installation

### Install as a PWA
The project includes a web manifest and service worker. Run the Flask server, open the site in Chrome or Edge, and click the "Install App" icon in the URL bar to add it to your desktop or mobile home screen.

### Create Windows Executable (.exe)
To package the web application into a standalone Windows app:
```powershell
.\make_downloads.bat
```
The Windows package is created at `release\COMPARE2SAVE-Windows.zip`. Extract it and run `COMPARE2SAVE.exe`.

### Offline-First Mobile App (iOS / Android)
The `mobile_app` folder contains a separate offline-first mobile version that uses `localStorage` instead of a Python backend. 

To generate native wrappers using Capacitor (requires Node.js):
```powershell
cd mobile_app
npm install
npm run android:add
npm run sync
npm run open:android
```
*(For iOS, replace `android` with `ios`. macOS and Xcode are required.)*

*Note: The Capacitor build is a no-server client. To connect a mobile app to a shared live marketplace, you must point the mobile frontend API calls to your hosted Flask backend URL.*
