from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import webbrowser


APP_DIR = Path(__file__).resolve().parent
WEB_DIR = APP_DIR / "www"
HOST = "127.0.0.1"
PORT = 5173


class MobileAppHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


if __name__ == "__main__":
    if not WEB_DIR.exists():
        raise SystemExit("The www folder was not found.")

    server = None
    port = PORT

    for candidate in range(PORT, PORT + 20):
        try:
            server = ThreadingHTTPServer((HOST, candidate), MobileAppHandler)
            port = candidate
            break
        except OSError:
            continue

    if server is None:
        raise SystemExit("Could not start the preview server. Ports 5173-5192 are busy.")

    url = f"http://{HOST}:{port}/index.html"

    print(f"Nearby Price Finder mobile preview running at {url}")
    print("Press Ctrl+C to stop.")
    webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
