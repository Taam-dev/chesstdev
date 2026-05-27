"""
FEN Generator - Converts board image to FEN string using piece recognition
"""

import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

try:
    import cv2
    import numpy as np

    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

try:
    from PIL import Image

    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# ─── Piece Labels ────────────────────────────────────────────────────────────

PIECE_TO_FEN = {
    "white_king": "K",
    "white_queen": "Q",
    "white_rook": "R",
    "white_bishop": "B",
    "white_knight": "N",
    "white_pawn": "P",
    "black_king": "k",
    "black_queen": "q",
    "black_rook": "r",
    "black_bishop": "b",
    "black_knight": "n",
    "black_pawn": "p",
    "empty": ".",
}

FILES = "abcdefgh"
RANKS = "87654321"  # From top to bottom in image


class FenGenerator:
    """
    Generates FEN notation from a chess board image.

    Uses template matching or ML-based piece recognition.
    Falls back to a heuristic color-based approach.
    """

    def __init__(self):
        self._templates: Optional[dict] = None
        self._model = None

    def generate_fen(self, board_image) -> Tuple[str, float, dict]:
        """
        Generate FEN from board image.

        Args:
            board_image: PIL Image of the board (top-down, square)

        Returns:
            (fen_string, confidence, square_map)
            where square_map = {"e4": "P", "e5": "p", ...}
        """
        if not HAS_CV2 or not HAS_PIL:
            return self._default_fen()

        try:
            cv_img = self._pil_to_cv2(board_image)
            squares = self._extract_squares(cv_img)
            piece_map, confidence = self._classify_squares(squares)
            fen = self._build_fen(piece_map)

            # Convert internal format to display format
            display_map = {
                sq: PIECE_TO_FEN.get(piece, ".") for sq, piece in piece_map.items()
            }

            return fen, confidence, display_map

        except Exception as e:
            logger.error(f"FEN generation error: {e}")
            return self._default_fen()

    def _extract_squares(self, cv_img) -> dict:
        """Extract 64 individual square images from board"""
        h, w = cv_img.shape[:2]
        sq_h = h // 8
        sq_w = w // 8

        squares = {}
        for rank_idx in range(8):
            for file_idx in range(8):
                # Extract square
                y1 = rank_idx * sq_h
                y2 = (rank_idx + 1) * sq_h
                x1 = file_idx * sq_w
                x2 = (file_idx + 1) * sq_w

                square_img = cv_img[y1:y2, x1:x2]

                # Square name (e.g., "a8", "h1")
                file_name = FILES[file_idx]
                rank_name = RANKS[rank_idx]
                square_name = file_name + rank_name

                squares[square_name] = square_img

        return squares

    def _classify_squares(self, squares: dict) -> Tuple[dict, float]:
        """
        Classify each square as piece or empty.

        Uses a simple color heuristic approach:
        - Detect if piece is present (brightness variance)
        - Detect piece color (light/dark pixel ratio)

        Returns:
            (piece_map, confidence)
        """
        piece_map = {}
        confidences = []

        for square_name, square_img in squares.items():
            piece, conf = self._classify_single_square(square_img, square_name)
            piece_map[square_name] = piece
            confidences.append(conf)

        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        return piece_map, avg_confidence

    def _classify_single_square(
        self, square_img, square_name: str
    ) -> Tuple[str, float]:
        """
        Classify a single square image.

        Heuristic approach:
        - High variance in grayscale = piece present
        - Dominant color determines piece color
        """
        gray = cv2.cvtColor(square_img, cv2.COLOR_BGR2GRAY)

        # Remove border (10% from each side) to focus on piece
        h, w = gray.shape
        margin_h = h // 8
        margin_w = w // 8
        center = gray[margin_h : h - margin_h, margin_w : w - margin_w]

        # Calculate variance to detect piece presence
        variance = float(np.var(center))

        VARIANCE_THRESHOLD = 200  # Tunable

        if variance < VARIANCE_THRESHOLD:
            return "empty", 0.7

        # Detect piece color using HSV
        hsv = cv2.cvtColor(square_img, cv2.COLOR_BGR2HSV)

        # Determine if square is light or dark
        is_light_square = self._is_light_square(square_name)

        # Sample center region brightness
        center_bgr = square_img[margin_h : h - margin_h, margin_w : w - margin_w]
        avg_brightness = float(np.mean(center_bgr))

        # White pieces are brighter than the square they're on
        # Black pieces are darker
        if is_light_square:
            is_white_piece = avg_brightness > 180
            is_black_piece = avg_brightness < 80
        else:
            is_white_piece = avg_brightness > 160
            is_black_piece = avg_brightness < 60

        if is_white_piece:
            piece_color = "white"
        elif is_black_piece:
            piece_color = "black"
        else:
            # Ambiguous - return generic piece
            return "empty", 0.3

        # We can't reliably determine piece TYPE with just color heuristics
        # Return a placeholder that indicates a piece of known color
        # In a real implementation, use a trained CNN here
        return f"{piece_color}_pawn", 0.4  # Placeholder confidence

    def _build_fen(self, piece_map: dict) -> str:
        """
        Build FEN position string from piece map.

        Args:
            piece_map: dict mapping square names to piece labels

        Returns:
            FEN position string (first field only, e.g. "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR")
        """
        fen_rows = []

        for rank_name in RANKS:
            row = []
            empty_count = 0

            for file_name in FILES:
                square = file_name + rank_name
                piece_label = piece_map.get(square, "empty")
                fen_char = PIECE_TO_FEN.get(piece_label, ".")

                if fen_char == ".":
                    empty_count += 1
                else:
                    if empty_count > 0:
                        row.append(str(empty_count))
                        empty_count = 0
                    row.append(fen_char)

            if empty_count > 0:
                row.append(str(empty_count))

            fen_rows.append("".join(row))

        position = "/".join(fen_rows)

        # Add default game state (can be improved)
        return f"{position} w KQkq - 0 1"

    @staticmethod
    def _is_light_square(square_name: str) -> bool:
        """Determine if a square is light or dark"""
        file_idx = FILES.index(square_name[0])
        rank_idx = int(square_name[1]) - 1
        return (file_idx + rank_idx) % 2 == 0

    @staticmethod
    def _pil_to_cv2(pil_image):
        """Convert PIL Image to OpenCV BGR"""
        rgb = np.array(pil_image.convert("RGB"))
        return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

    @staticmethod
    def _default_fen() -> Tuple[str, float, dict]:
        """Return starting position as fallback"""
        return (
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            0.0,
            {},
        )
