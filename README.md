# Nearby Price Finder

Nearby Price Finder is a Flask app for local product discovery, seller inventory management, checkout, order tracking, live chat, and an AI shopping assistant.

## Run the app

```powershell
python -m pip install -r requirements.txt
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

Download page:

```text
http://127.0.0.1:5000/download_app
```

Default owner admin login:

```text
username: admin
password: admin@123
```

You can override those values with `NPF_ADMIN_USERNAME` and `NPF_ADMIN_PASSWORD`.

## Install as an app

The project includes a web manifest and service worker. Run the Flask server, open the site in Chrome or Edge, then use the browser install option to add it to your desktop or mobile home screen.

## Create Windows download

Run:

```powershell
.\make_downloads.bat
```

The Windows package is created at:

```text
release\NearbyPriceFinder-Windows.zip
```

Share that zip file. On another Windows computer, extract it and run:

```text
NearbyPriceFinder.exe
```

## Android download

Android can install this project as a PWA from Chrome. See `ANDROID_DOWNLOAD.md`.

For a real `.apk`, deploy the app to HTTPS and wrap it with PWABuilder or Android Studio Trusted Web Activity.

## No-server Android/iOS app

The `mobile_app` folder contains a separate offline-first mobile version that does not run Flask, Python, SQLite, or any server process. It stores products, orders, seller inventory, chat, and demo account state on the device with `localStorage`.

Open directly:

```text
mobile_app\www\index.html
```

Generate native Android/iOS wrappers with Capacitor after installing Node.js LTS:

```powershell
cd mobile_app
npm install
npm run android:add
npm run sync
npm run open:android
```

iOS builds require macOS and Xcode:

```bash
cd mobile_app
npm install
npm run ios:add
npm run sync
npm run open:ios
```

You can also start from the project root:

```powershell
.\build_mobile.ps1
```

Note: because this version is truly no-server, data is local to each device. A shared live marketplace across many customers and sellers still needs a hosted backend or cloud database.

## Optional environment variables

```text
NPF_SECRET_KEY=change-this-for-production
NPF_ADMIN_USERNAME=admin
NPF_ADMIN_PASSWORD=admin@123
OPENAI_API_KEY=your-openai-key
OPENAI_MODEL=gpt-5.4-mini
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_FROM_NUMBER=your-twilio-phone-number
```
