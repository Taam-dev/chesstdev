"""
Central configuration for Chess Assistant.
Modify Stockfish path and parameters here.
"""

import platform
import shutil
from pathlib import Path


def _find_stockfish() -> str:
    """Automatically find Stockfish binary."""
    system = platform.system()

    candidates = []

    if system == "Windows":
        # Add all common filenames
        stockfish_names = [
            "stockfish.exe",
            "stockfish-windows-x86-64-avx2.exe",
            "stockfish-windows-x86-64-sse41-popcnt.exe",
            "stockfish-windows-x86-64.exe",
            "stockfish-windows.exe",
        ]
        stockfish_dirs = [
            Path(r"C:\stockfish"),
            Path(r"C:\Program Files\Stockfish"),
            Path(r"C:\Program Files (x86)\Stockfish"),
            Path.home() / "stockfish",
            Path.home() / "Desktop" / "stockfish",
            Path.home() / "Downloads" / "stockfish",
            Path.home() / "Downloads",
            Path("."),  # Current directory
        ]
        for d in stockfish_dirs:
            for name in stockfish_names:
                candidates.append(d / name)

        # Find any file containing "stockfish" in the directories
        for d in stockfish_dirs:
            try:
                if d.exists() and d.is_dir():
                    for f in d.iterdir():
                        if (
                            f.is_file()
                            and "stockfish" in f.name.lower()
                            and f.suffix == ".exe"
                        ):
                            candidates.append(f)
            except (OSError, PermissionError):
                continue

    elif system == "Darwin":  # macOS
        candidates = [
            Path("/usr/local/bin/stockfish"),
            Path("/opt/homebrew/bin/stockfish"),
        ]
    else:  # Linux
        candidates = [
            Path("/usr/bin/stockfish"),
            Path("/usr/games/stockfish"),
            Path("/usr/local/bin/stockfish"),
            Path("/snap/bin/stockfish"),
        ]

    # Check each path
    for path in candidates:
        try:
            if path.exists() and path.is_file():
                return str(path.resolve())
        except (OSError, PermissionError):
            continue

    # Search in PATH
    found = shutil.which("stockfish")
    if found:
        return found

    return ""


class Config:
    """Main configuration."""

    # --- Stockfish ---
    STOCKFISH_PATH: str = _find_stockfish()
    ENGINE_DEPTH: int = 18
    ENGINE_TIME_LIMIT: float = 2.0
    ENGINE_THREADS: int = 2
    ENGINE_HASH_MB: int = 128

    # --- Relay Server ---
    RELAY_HOST: str = "127.0.0.1"
    RELAY_PORT: int = 5555

    # --- Overlay GUI ---
    OVERLAY_WIDTH: int = 420
    OVERLAY_HEIGHT: int = 500
    OVERLAY_ALPHA: float = 0.95
    REFRESH_INTERVAL_MS: int = 1500  # Auto-refresh interval

    # --- FEN File ---
    FEN_FILE: str = "current_fen.txt"

    @classmethod
    def validate(cls) -> list:
        """Returns a list of configuration issues."""
        problems = []
        if not cls.STOCKFISH_PATH:
            problems.append(
                "Stockfish not found!\n"
                "  → Download from: https://stockfishchess.org/download/\n"
                "  → Then update Config.STOCKFISH_PATH in config.py\n"
                '  → Or run: python main.py --stockfish "path/to/stockfish.exe"'
            )
        else:
            p = Path(cls.STOCKFISH_PATH)
            if not p.exists():
                problems.append(f"Stockfish file does not exist: {cls.STOCKFISH_PATH}")
        return problems
