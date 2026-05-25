# Android Download Options

## Option 1: Install from Chrome

This project is already configured as a Progressive Web App.

Important: Android Chrome only shows **Install app** for secure sites. A local network URL like `http://YOUR-COMPUTER-IP:5000` usually will not show the install option because it is not HTTPS.

1. Start the app on the computer:

   ```powershell
   python app.py
   ```

2. Open the app on Android Chrome using an HTTPS URL.

   For testing, expose your local Flask app with a tunnel such as ngrok or Cloudflare Tunnel, then open the generated `https://...` link on the phone.

   Local HTTP example that may open but normally will not show install:

   ```text
   http://YOUR-COMPUTER-IP:5000
   ```

3. In Chrome, tap **Install App** on the page, or open the Chrome menu and choose **Add to Home screen**.

This creates an Android home-screen app with the app icon, standalone display, and service worker caching.

## Option 2: Build an APK

To create a downloadable `.apk`, use a PWA wrapper service such as PWABuilder or Android Studio Trusted Web Activity.

Requirements:

- The app must be hosted on an HTTPS URL.
- The existing `/manifest.json`, `/service-worker.js`, and `/static/app-icon.svg` files must remain available.
- Use the hosted URL as the Android app start URL.

Recommended route:

1. Deploy this Flask app to a public HTTPS host.
2. Open `https://www.pwabuilder.com/`.
3. Enter the hosted app URL.
4. Generate and download the Android package.

Local `http://127.0.0.1:5000` cannot become a useful Android APK because it only points to the phone itself, not your computer.

## Android download button in this project

The app now has an Android download route:

```text
/download/android
```

If this file exists, the route downloads it:

```text
release/COMPARE2SAVE-Android.apk
```

If the APK is not present, the route opens an Android setup page with HTTPS/PWA instructions.
