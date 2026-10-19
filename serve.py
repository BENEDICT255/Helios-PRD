"""
Lightweight local HTTP server for serving the dummy Helios PRD web app.
"""
import http.server
import socketserver
import os
import sys
from pathlib import Path

DEFAULT_PORT = 8000
WEB_DIR = Path(__file__).parent / "web"

class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def log_message(self, format, *args):
        # Suppress noisy standard requests, only log errors or startup
        pass

def start_server(port: int = DEFAULT_PORT):
    os.chdir(WEB_DIR)
    with socketserver.TCPServer(("", port), QuietHandler) as httpd:
        print(f"[DEMO SERVER] Serving local dummy app at http://localhost:{port}/index.html")
        print("[DEMO SERVER] Press Ctrl+C to terminate.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[DEMO SERVER] Server stopped.")

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PORT
    start_server(port)
