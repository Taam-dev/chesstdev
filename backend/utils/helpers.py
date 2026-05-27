"""
Utility helpers for ChessCoach backend
"""

import logging
import sys
import os
from pathlib import Path
from typing import Optional
import chess


def setup_logging(level: str = "INFO") -> None:
    """Configure logging with colored output"""
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Override with env var
    env_level = os.environ.get("LOG_LEVEL", "").upper()
    if env_level in ("DEBUG", "INFO", "WARNING", "ERROR"):
        log_level = getattr(logging, env_level)

    # Format
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    date_fmt = "%H:%M:%S"

    handlers = [logging.StreamHandler(sys.stdout)]

    # File handler in production
    log_dir = Path.home() / ".chesstdev" / "logs"
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_dir / "backend.log", encoding="utf-8"))
    except Exception:
        pass

    logging.basicConfig(
        level=log_level,
        format=fmt,
        datefmt=date_fmt,
        handlers=handlers,
    )

    # Silence noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("websockets").setLevel(logging.WARNING)


def fen_to_board(fen: str) -> Optional[chess.Board]:
    """
    Safely create a chess.Board from FEN string.

    Returns None if FEN is invalid.
    """
    try:
        board = chess.Board(fen)
        return board
    except ValueError as e:
        logging.getLogger(__name__).error(f"Invalid FEN: {fen} — {e}")
        return None


def is_valid_fen(fen: str) -> bool:
    """Check if a FEN string is valid"""
    try:
        chess.Board(fen)
        return True
    except ValueError:
        return False


def is_valid_move(fen: str, move_uci: str) -> bool:
    """Check if a UCI move is legal in the given position"""
    board = fen_to_board(fen)
    if board is None:
        return False
    try:
        move = chess.Move.from_uci(move_uci)
        return move in board.legal_moves
    except ValueError:
        return False


def uci_to_san(fen: str, uci: str) -> Optional[str]:
    """Convert UCI move to SAN notation"""
    board = fen_to_board(fen)
    if board is None:
        return None
    try:
        move = chess.Move.from_uci(uci)
        return board.san(move)
    except (ValueError, KeyError):
        return None


def san_to_uci(fen: str, san: str) -> Optional[str]:
    """Convert SAN move to UCI notation"""
    board = fen_to_board(fen)
    if board is None:
        return None
    try:
        move = board.parse_san(san)
        return move.uci()
    except ValueError:
        return None


def get_piece_value(piece_type: int) -> int:
    """Get approximate piece value in centipawns"""
    values = {
        chess.PAWN: 100,
        chess.KNIGHT: 320,
        chess.BISHOP: 330,
        chess.ROOK: 500,
        chess.QUEEN: 900,
        chess.KING: 0,
    }
    return values.get(piece_type, 0)


def evaluate_material(board: chess.Board) -> int:
    """
    Simple material count evaluation.

    Returns centipawns from White's perspective.
    Positive = White advantage.
    """
    score = 0
    for piece_type in chess.PIECE_TYPES:
        white_count = len(board.pieces(piece_type, chess.WHITE))
        black_count = len(board.pieces(piece_type, chess.BLACK))
        value = get_piece_value(piece_type)
        score += (white_count - black_count) * value
    return score


def format_evaluation(cp: Optional[int], mate: Optional[int]) -> str:
    """Format evaluation for display"""
    if mate is not None:
        if mate > 0:
            return f"M{mate}"
        else:
            return f"-M{abs(mate)}"
    if cp is None:
        return "0.00"
    pawns = cp / 100.0
    if pawns >= 0:
        return f"+{pawns:.2f}"
    return f"{pawns:.2f}"


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp a value between min and max"""
    return max(min_val, min(max_val, value))


def get_resource_path(relative_path: str) -> Path:
    """
    Get absolute path to resource.
    Works for both development and PyInstaller frozen app.
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = Path(sys._MEIPASS)  # type: ignore
    except AttributeError:
        base_path = Path(__file__).parent.parent.parent

    return base_path / relative_path


def truncate_string(s: str, max_len: int = 100) -> str:
    """Truncate a string for logging"""
    if len(s) <= max_len:
        return s
    return s[:max_len] + "..."
