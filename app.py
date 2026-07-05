"""
COMPARE2SAVE — Application Entry Point
"""
from backend.app_factory import app
import backend.app  # noqa: F401 — registers all routes
from werkzeug.middleware.proxy_fix import ProxyFix

# ProxyFix ensures correct HTTPS URLs when deployed behind a reverse proxy (e.g. Render, Nginx)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
app.config['PREFERRED_URL_SCHEME'] = 'https'

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
