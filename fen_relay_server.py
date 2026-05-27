"""
HTTP server nhỏ nhận FEN từ Tampermonkey userscript.

Chạy: python fen_relay_server.py
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import sys
from datetime import datetime

from config import Config

_current_fen = ""
_lock = threading.Lock()
_fen_count = 0


class FENHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == "/fen":
            with _lock:
                fen = _current_fen
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(fen.encode("utf-8"))

        elif self.path == "/status":
            with _lock:
                fen = _current_fen
                count = _fen_count
            status = f"FEN count: {count}\nCurrent: {fen or '(none)'}"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(status.encode("utf-8"))

        else:
            self.send_response(404)
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

            # Log khi FEN thay đổi
            now = datetime.now().strftime("%H:%M:%S")
            if body != old_fen:
                print(f"[{now}] ♟ FEN MỚI #{count}: {body}")
            else:
                print(f"[{now}]   FEN #{count}: (không đổi)")

            # Ghi ra file để backup
            try:
                with open(Config.FEN_FILE, "w") as f:
                    f.write(body)
            except IOError:
                pass

            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(b"OK")
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, format, *args):
        # Tắt log mặc định của HTTPServer (quá nhiều spam)
        pass


def run_server(host=None, port=None):
    host = host or Config.RELAY_HOST
    port = port or Config.RELAY_PORT

    server = HTTPServer((host, port), FENHandler)

    print("=" * 55)
    print("  ♟ FEN Relay Server")
    print("=" * 55)
    print(f"  Địa chỉ:  http://{host}:{port}/fen")
    print(f"  Status:   http://{host}:{port}/status")
    print()
    print("  Đang chờ FEN từ trình duyệt...")
    print("  (Giữ terminal này mở, đừng đóng)")
    print("=" * 55)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[SERVER] Đã tắt.")
        server.server_close()


if __name__ == "__main__":
    run_server()
