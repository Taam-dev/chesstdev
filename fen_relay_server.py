"""
FEN Relay Server v4 - Receives FEN from browser, serves FEN, and relays best moves.
Run: python fen_relay_server.py
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote
import threading
from datetime import datetime

_current_fen = ""
_best_move = ""
_lock = threading.Lock()
_fen_count = 0
FEN_FILE = "current_fen.txt"


class FENHandler(BaseHTTPRequestHandler):

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        global _current_fen, _best_move
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        # GET /fen - Return current FEN
        if parsed.path == "/fen":
            with _lock:
                fen = _current_fen
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self._cors()
            self.end_headers()
            self.wfile.write(fen.encode("utf-8"))

        # GET /set?fen=... - Set FEN via query string
        elif parsed.path == "/set":
            fen_value = params.get("fen", [""])[0]
            fen_value = unquote(fen_value).strip()

            if fen_value:
                self._save_fen(fen_value)
                with _lock:
                    _best_move = ""  # Clear old best move on new position

            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self._cors()
            self.end_headers()
            self.wfile.write(b"OK")

        # GET /bestmove - Get current best move
        elif parsed.path == "/bestmove":
            with _lock:
                move = _best_move
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self._cors()
            self.end_headers()
            self.wfile.write(move.encode("utf-8"))

        # GET /set_bestmove?move=... - Set best move from engine
        elif parsed.path == "/set_bestmove":
            move_value = params.get("move", [""])[0]
            move_value = unquote(move_value).strip()
            with _lock:
                _best_move = move_value
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self._cors()
            self.end_headers()
            self.wfile.write(b"OK")

        elif parsed.path == "/status":
            with _lock:
                fen = _current_fen
                move = _best_move
                count = _fen_count
            status = f"FEN count: {count}\nCurrent FEN: {fen or '(none)'}\nBest Move: {move or '(none)'}"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self._cors()
            self.end_headers()
            self.wfile.write(status.encode("utf-8"))

        elif parsed.path == "/ping":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self._cors()
            self.end_headers()
            self.wfile.write(b"pong")

        else:
            self.send_response(404)
            self._cors()
            self.end_headers()

    def do_POST(self):
        global _best_move
        if self.path.startswith("/fen"):
            content_length = int(self.headers.get("Content-Length", 0))
            body = ""
            if content_length > 0:
                body = self.rfile.read(content_length).decode("utf-8").strip()

            if body:
                self._save_fen(body)
                with _lock:
                    _best_move = ""  # Clear old best move on new position

            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self._cors()
            self.end_headers()
            self.wfile.write(b"OK")
        else:
            self.send_response(404)
            self._cors()
            self.end_headers()

    def _save_fen(self, fen):
        global _current_fen, _fen_count
        with _lock:
            old = _current_fen
            _current_fen = fen
            _fen_count += 1
            count = _fen_count

        now = datetime.now().strftime("%H:%M:%S")
        if fen != old:
            print(f"[{now}] NEW FEN #{count}: {fen}")
        else:
            print(f"[{now}]   FEN #{count}: (unchanged)")

        try:
            with open(FEN_FILE, "w") as f:
                f.write(fen)
        except IOError:
            pass

    def log_message(self, format, *args):
        pass


def run_server():
    host = "127.0.0.1"
    port = 5555

    server = HTTPServer((host, port), FENHandler)

    print("=" * 55)
    print("  FEN Relay Server v4")
    print("=" * 55)
    print(f"  Get FEN:      http://{host}:{port}/fen")
    print(f"  Send FEN:     http://{host}:{port}/set?fen=...")
    print(f"  Get Best Move:http://{host}:{port}/bestmove")
    print(f"  Set Best Move:http://{host}:{port}/set_bestmove?move=...")
    print(f"  Status:       http://{host}:{port}/status")
    print(f"  Ping:         http://{host}:{port}/ping")
    print()
    print("  Waiting for FEN from browser...")
    print("=" * 55)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[SERVER] Server stopped.")
        server.server_close()


if __name__ == "__main__":
    run_server()
