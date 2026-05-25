# COMPARE2SAVE Mobile

This is the no-server Android/iOS version of COMPARE2SAVE.

The original Flask app needs a Python server, SQLite database, sessions, and backend routes. This mobile version runs completely on the device from static files. Products, users, orders, chats, and settings are stored in browser/WebView `localStorage`.

## Run locally without a server

Open `www/index.html` in a browser. Most features work directly from the file system.

## Build native Android/iOS wrappers

Install Node.js LTS first.

```powershell
cd mobile_app
npm install
npm run android:add
npm run sync
npm run open:android
```

For iOS, run on macOS with Xcode installed:

```bash
cd mobile_app
npm install
npm run ios:add
npm run sync
npm run open:ios
```

## Important differences from the Flask version

- No Python or Flask server runs inside the app.
- No shared central database is used; data stays on each device.
- OTP/SMS and OpenAI chatbot calls are replaced with local demo behavior.
- Seller uploads are saved as local image data in the app storage.
- To share live inventory between many customers and sellers, you will still need a hosted backend or cloud database.
