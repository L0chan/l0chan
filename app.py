from backend.app_factory import app
import backend.app
from werkzeug.middleware.proxy_fix import ProxyFix
import os

# --- PROXY FIX FOR PRODUCTION ---
# Ensures that url_for and redirects use the correct protocol (HTTPS) when behind a proxy like Render.
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
app.config['PREFERRED_URL_SCHEME'] = 'https'

if __name__ == "__main__":

    app.run(host="0.0.0.0", port=5000, debug=False)



