"""
Retrieve FEN from various sources.
"""

from __future__ import annotations

import urllib.request
import chess

from config import Config


class FENProvider:
    """Provides FEN from relay server, file, or manual input."""

    def __init__(self):
        self._last_fen: str | None = None
        self._manual_fen: str | None = None

    def set_manual_fen(self, fen: str) -> bool:
        """Set FEN manually."""
        validated = self._validate(fen)
        if validated:
            self._manual_fen = validated
            self._last_fen = validated
            return True
        return False

    def get_fen(self) -> str | None:
        """Retrieve FEN in priority order: relay server -> file -> manual."""

        # 1. Relay server
        fen = self._from_relay_server()
        if fen:
            self._last_fen = fen
            return fen

        # 2. File
        fen = self._from_file()
        if fen:
            self._last_fen = fen
            return fen

        # 3. Manual
        if self._manual_fen:
            return self._manual_fen

        return self._last_fen

    def _from_relay_server(self) -> str | None:
        """Fetch FEN from http://127.0.0.1:5555/fen"""
        try:
            url = f"http://{Config.RELAY_HOST}:{Config.RELAY_PORT}/fen"
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=0.5) as resp:
                raw = resp.read().decode("utf-8").strip()
                if raw:
                    return self._validate(raw)
        except Exception:
            pass
        return None

    def _from_file(self) -> str | None:
        """Read FEN from file."""
        try:
            with open(Config.FEN_FILE, "r") as f:
                raw = f.read().strip()
                if raw:
                    return self._validate(raw)
        except (FileNotFoundError, IOError):
            pass
        return None

    def _validate(self, fen: str) -> str | None:
        """Validate FEN string."""
        try:
            fen = fen.strip()
            board = chess.Board(fen)
            return board.fen()
        except (ValueError, Exception):
            return None

    @property
    def last_fen(self):
        return self._last_fen
