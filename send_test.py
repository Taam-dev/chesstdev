import urllib.request

fen = "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3"

print(f"Dang gui FEN: {fen}")

try:
    req = urllib.request.Request(
        "http://127.0.0.1:5555/fen",
        data=fen.encode("utf-8"),
        method="POST",
        headers={"Content-Type": "text/plain"},
    )
    response = urllib.request.urlopen(req, timeout=3)
    print(f"Gui thanh cong! Server tra ve: {response.read().decode('utf-8')}")
except Exception as e:
    print(f"LOI: {e}")
    print("Kiem tra xem fen_relay_server.py da chay chua?")
