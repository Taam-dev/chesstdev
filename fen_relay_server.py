"""
FEN Relay Server - Nhan FEN tu browser gui ve cho Chess Assistant.
Co CORS headers day du de browser khong chan.

Chay: python fen_relay_server.py
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from datetime import datetime

_current_fen = ""
_lock = threading.Lock()
_fen_count = 0
FEN_FILE = "current_fen.txt"

# Danh sach origin duoc phep
ALLOWED_ORIGINS = [
    "https://www.chess.com",
    "https://chess.com",
    "http://www.chess.com",
    "http://chess.com",
    "null",  # cho local file
]


class FENHandler(BaseHTTPRequestHandler):

    def _send_cors_headers(self):
        """Gui CORS headers cho MOI response."""
        origin = self.headers.get("Origin", "*")
        # Cho phep tat ca origin (de don gian)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, OPTIONS")
        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type, Accept, Origin, X-Requested-With",
        )
        self.send_header("Access-Control-Max-Age", "86400")

    def do_OPTIONS(self):
        """CORS preflight - PHAI co cai nay."""
        self.send_response(200)
        self._send_cors_headers()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        if self.path == "/fen":
            with _lock:
                fen = _current_fen
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(fen.encode("utf-8"))

        elif self.path == "/status":
            with _lock:
                fen = _current_fen
                count = _fen_count
            status = f"FEN count: {count}\nCurrent: {fen or '(none)'}"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(status.encode("utf-8"))

        elif self.path == "/ping":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(b"pong")

        else:
            self.send_response(404)
            self._send_cors_headers()
            self.end_headers()

    def do_POST(self):
        if self.path == "/fen":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8").strip()

            global _current_fen, _fen_count
            with _lock:
                old_fen = _current_fen
                _current_fen = body
                _fen_count += 1
                count = _fen_count

            now = datetime.now().strftime("%H:%M:%S")
            if body != old_fen:
                print(f"[{now}] FEN MOI #{count}: {body}")
            else:
                print(f"[{now}]   FEN #{count}: (khong doi)")

            try:
                with open(FEN_FILE, "w") as f:
                    f.write(body)
            except IOError as e:
                print(f"[WARNING] Khong ghi duoc file: {e}")

            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(b"OK")
        else:
            self.send_response(404)
            self._send_cors_headers()
            self.end_headers()

    def log_message(self, format, *args):
        """Tat log mac dinh."""
        pass


def run_server():
    host = "127.0.0.1"
    port = 5555

    server = HTTPServer((host, port), FENHandler)

    print("=" * 55)
    print("  FEN Relay Server v2 (CORS Fixed)")
    print("=" * 55)
    print(f"  FEN:     http://{host}:{port}/fen")
    print(f"  Status:  http://{host}:{port}/status")
    print(f"  Ping:    http://{host}:{port}/ping")
    print()
    print("  Dang cho FEN tu trinh duyet...")
    print("  (Giu terminal nay mo)")
    print("=" * 55)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[SERVER] Da tat.")
        server.server_close()


if __name__ == "__main__":
    run_server()
