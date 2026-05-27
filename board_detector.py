"""
Detects the chessboard region on screen, segments it into an 8x8 grid,
and classifies each square to produce a FEN string.

Strategy:
  1. Capture the full screen.
  2. Find the largest square-ish region whose colors match Chess.com's
     board theme (green default).
  3. Divide into 64 squares.
  4. Classify each square as empty, white piece, or black piece using
     contour area + brightness analysis.
  5. Attempt to identify piece types via template matching or
     heuristic contour analysis.

NOTE: Reliable pixel-perfect piece recognition is *hard* without
pre-rendered templates for every piece set / size. This module uses a
heuristic approach that works well for the default Chess.com piece set
at common board sizes. For maximum reliability, consider the
browser-console / extension approach described in fen_parser.py.
"""

from __future__ import annotations

import cv2
import numpy as np

from config import Config
from screen_capture import ScreenCapture


class BoardDetector:
    """Finds the chessboard on screen and returns square occupancy."""

    def __init__(self, screen: ScreenCapture | None = None):
        self.screen = screen or ScreenCapture()
        self._board_rect: tuple[int, int, int, int] | None = None  # x,y,w,h cache

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def find_board(
        self, frame: np.ndarray | None = None
    ) -> tuple[int, int, int, int] | None:
        """
        Locate the chessboard in *frame* (BGR).
        Returns (x, y, w, h) in screen coordinates, or None.
        """
        if frame is None:
            frame = self.screen.grab_full_screen()

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Build a mask for BOTH light and dark squares
        mask_light = cv2.inRange(
            frame,
            np.array(Config.DARK_SQUARE_LOWER, dtype=np.uint8),
            np.array(Config.DARK_SQUARE_UPPER, dtype=np.uint8),
        )
        mask_dark = cv2.inRange(
            frame,
            np.array(Config.LIGHT_SQUARE_LOWER, dtype=np.uint8),
            np.array(Config.LIGHT_SQUARE_UPPER, dtype=np.uint8),
        )
        combined = cv2.bitwise_or(mask_light, mask_dark)

        # Morphological close to merge adjacent squares into one blob
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
        combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel, iterations=3)

        contours, _ = cv2.findContours(
            combined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        best = None
        best_area = 0

        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            # Board should be roughly square
            aspect = w / h if h > 0 else 0
            if 0.85 < aspect < 1.15 and w >= Config.MIN_BOARD_SIZE:
                area = w * h
                if area > best_area:
                    best_area = area
                    best = (x, y, w, h)

        if best:
            self._board_rect = best
        return best

    def get_squares(
        self,
        frame: np.ndarray,
        board_rect: tuple[int, int, int, int],
        flipped: bool = False,
    ) -> list[list[np.ndarray]]:
        """
        Slice the board region into an 8x8 grid of sub-images.
        Returns rows top-to-bottom (rank 8 down to rank 1 for white perspective).
        If *flipped* is True, the board is viewed from Black's side.
        """
        x, y, w, h = board_rect
        board_img = frame[y : y + h, x : x + w]
        sq_w = w // 8
        sq_h = h // 8

        rows: list[list[np.ndarray]] = []
        for r in range(8):
            row = []
            for c in range(8):
                sx = c * sq_w
                sy = r * sq_h
                square_img = board_img[sy : sy + sq_h, sx : sx + sq_w]
                row.append(square_img)
            rows.append(row)

        if flipped:
            # Reverse both rows and columns
            rows = [list(reversed(row)) for row in reversed(rows)]

        return rows

    def classify_square(self, square_img: np.ndarray) -> str:
        """
        Classify a single square image.
        Returns:
          '.' for empty
          'W' for white piece
          'B' for black piece
        """
        gray = cv2.cvtColor(square_img, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape

        # Look at the center region (ignore edges – that's the square color)
        margin = int(min(h, w) * 0.2)
        center = gray[margin : h - margin, margin : w - margin]

        if center.size == 0:
            return "."

        # Edge detection to find piece contours
        edges = cv2.Canny(center, 50, 150)
        edge_density = np.count_nonzero(edges) / edges.size

        if edge_density < 0.02:
            return "."  # No significant edges → empty square

        # Compute mean brightness of the center to distinguish piece color
        # We need to isolate the piece from the square background.
        # Use adaptive thresholding to find the piece silhouette.
        _, binary = cv2.threshold(center, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        contours, _ = cv2.findContours(
            binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        if not contours:
            return "."

        largest = max(contours, key=cv2.contourArea)
        area_ratio = cv2.contourArea(largest) / (center.shape[0] * center.shape[1])
        if area_ratio < 0.05:
            return "."

        # Create mask from the contour and compute mean brightness
        mask = np.zeros_like(center)
        cv2.drawContours(mask, [largest], -1, 255, -1)
        mean_val = cv2.mean(center, mask=mask)[0]

        if mean_val > Config.WHITE_PIECE_THRESHOLD:
            return "W"
        elif mean_val < Config.BLACK_PIECE_THRESHOLD:
            return "B"
        else:
            # Ambiguous – use a secondary heuristic
            overall_mean = np.mean(center)
            return "W" if overall_mean > 128 else "B"

    def detect_occupancy(
        self, frame: np.ndarray | None = None, flipped: bool = False
    ) -> list[list[str]] | None:
        """
        Full pipeline: find board → classify all squares.
        Returns 8×8 list of '.' / 'W' / 'B', or None if board not found.
        """
        if frame is None:
            frame = self.screen.grab_full_screen()

        rect = self.find_board(frame)
        if not rect:
            return None

        squares = self.get_squares(frame, rect, flipped=flipped)
        occupancy = []
        for row in squares:
            occ_row = []
            for sq_img in row:
                occ_row.append(self.classify_square(sq_img))
            occupancy.append(occ_row)

        return occupancy

    @property
    def last_board_rect(self):
        return self._board_rect
