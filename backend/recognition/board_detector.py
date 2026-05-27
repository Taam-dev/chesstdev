"""
Board Detector - Locates and extracts chess board from images
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


class BoardDetector:
    """
    Detects and extracts chess board from an image.

    Strategy:
    1. Convert to grayscale
    2. Edge detection (Canny)
    3. Find contours
    4. Identify the largest square contour (the board)
    5. Perspective transform to get a top-down view
    """

    BOARD_SIZE = 800  # Output size for extracted board

    def detect_board(self, image) -> Tuple[Optional[object], Optional[list]]:
        """
        Detect and extract chess board from image.

        Args:
            image: PIL Image

        Returns:
            (board_image, corners) or (None, None)
        """
        if not HAS_CV2 or not HAS_PIL:
            logger.error("OpenCV and PIL required for board detection")
            return None, None

        try:
            # Convert PIL to OpenCV
            cv_img = self._pil_to_cv2(image)

            # Find board corners
            corners = self._find_corners(cv_img)

            if corners is None:
                logger.warning("Board corners not found, trying full image")
                # Use full image as fallback
                h, w = cv_img.shape[:2]
                board_pil = image.resize(
                    (self.BOARD_SIZE, self.BOARD_SIZE), Image.LANCZOS
                )
                return board_pil, None

            # Perspective transform
            board_cv = self._perspective_transform(cv_img, corners)

            # Convert back to PIL
            board_pil = Image.fromarray(cv2.cvtColor(board_cv, cv2.COLOR_BGR2RGB))

            return board_pil, corners.tolist()

        except Exception as e:
            logger.error(f"Board detection error: {e}")
            return None, None

    def find_board_corners(self, image) -> Optional[list]:
        """Find board corners for calibration"""
        if not HAS_CV2:
            return None

        cv_img = self._pil_to_cv2(image)
        corners = self._find_corners(cv_img)

        if corners is not None:
            return corners.tolist()
        return None

    def _find_corners(self, cv_img) -> Optional[object]:
        """Find the 4 corners of the chess board"""
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)

        # Blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Edge detection
        edges = cv2.Canny(blurred, 50, 150)

        # Dilate edges
        kernel = np.ones((3, 3), np.uint8)
        dilated = cv2.dilate(edges, kernel, iterations=2)

        # Find contours
        contours, _ = cv2.findContours(
            dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        if not contours:
            return None

        # Find largest quadrilateral
        image_area = cv_img.shape[0] * cv_img.shape[1]

        best_contour = None
        best_area = 0

        for contour in contours:
            area = cv2.contourArea(contour)

            # Skip too small or too large
            if area < image_area * 0.05 or area > image_area * 0.98:
                continue

            # Approximate polygon
            perimeter = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)

            # We want a quadrilateral
            if len(approx) == 4 and area > best_area:
                best_area = area
                best_contour = approx

        if best_contour is None:
            return None

        return self._order_corners(best_contour.reshape(4, 2).astype(np.float32))

    def _order_corners(self, corners) -> object:
        """
        Order corners: [top-left, top-right, bottom-right, bottom-left]
        """
        rect = np.zeros((4, 2), dtype=np.float32)

        # Sum and difference for ordering
        s = corners.sum(axis=1)
        diff = np.diff(corners, axis=1)

        rect[0] = corners[np.argmin(s)]  # Top-left: smallest sum
        rect[2] = corners[np.argmax(s)]  # Bottom-right: largest sum
        rect[1] = corners[np.argmin(diff)]  # Top-right: smallest diff
        rect[3] = corners[np.argmax(diff)]  # Bottom-left: largest diff

        return rect

    def _perspective_transform(self, cv_img, corners) -> object:
        """Apply perspective transform to get top-down board view"""
        dst = np.array(
            [
                [0, 0],
                [self.BOARD_SIZE - 1, 0],
                [self.BOARD_SIZE - 1, self.BOARD_SIZE - 1],
                [0, self.BOARD_SIZE - 1],
            ],
            dtype=np.float32,
        )

        M = cv2.getPerspectiveTransform(corners, dst)
        warped = cv2.warpPerspective(cv_img, M, (self.BOARD_SIZE, self.BOARD_SIZE))

        return warped

    def _pil_to_cv2(self, pil_image):
        """Convert PIL Image to OpenCV BGR"""
        import numpy as np

        rgb = np.array(pil_image.convert("RGB"))
        return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
