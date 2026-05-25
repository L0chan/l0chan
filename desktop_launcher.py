import os
import threading
import webbrowser

from backend.app_factory import app


HOST = os.environ.get("C2S_HOST", "127.0.0.1")
PORT = int(os.environ.get("C2S_PORT", "5000"))


def open_app():
    webbrowser.open(f"http://{HOST}:{PORT}")


if __name__ == "__main__":
    threading.Timer(1.2, open_app).start()
    app.run(host=HOST, port=PORT, debug=False, use_reloader=False)
