"""
Screen Capture - Captures screen/webcam and passes to board detector
"""

import asyncio
import logging
from typing import Optional, Callable
import base64
import io

logger = logging.getLogger(__name__)

try:
    import mss
    import mss.tools

    HAS_MSS = True
except ImportError:
    HAS_MSS = False
    logger.warning("mss not installed - screen capture unavailable")

try:
    import cv2
    import numpy as np

    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    logger.warning("OpenCV not installed - image processing unavailable")

try:
    from PIL import Image

    HAS_PIL = True
except ImportError:
    HAS_PIL = False


class ScreenCapture:
    """
    Handles screen capture and webcam streaming for board detection.
    """

    def __init__(self):
        self._webcam_active = False
        self._webcam_task: Optional[asyncio.Task] = None
        self._cap = None  # cv2.VideoCapture

    # ─── Screen Capture ──────────────────────────────────────────────────────────

    async def capture_and_analyze(self, region: Optional[dict] = None) -> dict:
        """
        Capture screen and detect chess board.

        Args:
            region: Optional dict with x, y, width, height

        Returns:
            RecognitionResult dict
        """
        if not HAS_MSS:
            return self._error_result("mss library not installed")

        try:
            image = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self._capture_screen(region)
            )

            if image is None:
                return self._error_result("Screen capture failed")

            return await self._analyze_image(image, mode="screen")

        except Exception as e:
            logger.error(f"Screen capture error: {e}")
            return self._error_result(str(e))

    def _capture_screen(self, region: Optional[dict] = None):
        """Synchronous screen capture using mss"""
        with mss.mss() as sct:
            if region:
                monitor = {
                    "top": int(region.get("y", 0)),
                    "left": int(region.get("x", 0)),
                    "width": int(region.get("width", 800)),
                    "height": int(region.get("height", 800)),
                }
            else:
                # Full primary monitor
                monitor = sct.monitors[1]

            screenshot = sct.grab(monitor)

            if HAS_PIL:
                img = Image.frombytes(
                    "RGB", screenshot.size, screenshot.bgra, "raw", "BGRX"
                )
                return img

            return None

    # ─── Webcam ──────────────────────────────────────────────────────────────────

    async def start_webcam(
        self, device_index: int = 0, callback: Optional[Callable] = None
    ) -> None:
        """Start webcam capture loop"""
        if not HAS_CV2:
            logger.error("OpenCV required for webcam capture")
            return

        self._webcam_active = True
        self._webcam_task = asyncio.get_event_loop().create_task(
            self._webcam_loop(device_index, callback)
        )

    async def _webcam_loop(
        self, device_index: int, callback: Optional[Callable]
    ) -> None:
        """Main webcam capture loop"""
        loop = asyncio.get_event_loop()

        def open_camera():
            cap = cv2.VideoCapture(device_index)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            return cap

        self._cap = await loop.run_in_executor(None, open_camera)

        if not self._cap.isOpened():
            logger.error(f"Cannot open camera {device_index}")
            self._webcam_active = False
            return

        logger.info(f"Webcam {device_index} started")

        try:
            while self._webcam_active:
                ret, frame = await loop.run_in_executor(None, self._cap.read)

                if not ret:
                    await asyncio.sleep(0.1)
                    continue

                # Analyze every 2 seconds (adjustable)
                result = await self._analyze_cv2_frame(frame)

                if callback and result.get("confidence", 0) > 0.5:
                    await callback(result)

                # 2 fps for board detection
                await asyncio.sleep(0.5)

        finally:
            if self._cap:
                self._cap.release()
                self._cap = None
            logger.info("Webcam stopped")

    def stop_webcam(self) -> None:
        """Stop webcam capture"""
        self._webcam_active = False
        if self._webcam_task:
            self._webcam_task.cancel()
            self._webcam_task = None

    # ─── Image Analysis ───────────────────────────────────────────────────────────

    async def _analyze_image(self, image, mode: str = "screen") -> dict:
        """Analyze PIL image for chess board"""
        try:
            from recognition.board_detector import BoardDetector
            from recognition.fen_generator import FenGenerator

            detector = BoardDetector()
            fen_gen = FenGenerator()

            # Detect board
            board_image, corners = await asyncio.get_event_loop().run_in_executor(
                None, lambda: detector.detect_board(image)
            )

            if board_image is None:
                return self._error_result("No chess board detected", confidence=0.0)

            # Generate FEN
            fen, confidence, squares = await asyncio.get_event_loop().run_in_executor(
                None, lambda: fen_gen.generate_fen(board_image)
            )

            return {
                "fen": fen,
                "confidence": confidence,
                "squares": squares,
                "turn": "w",  # Default; can be improved with side detection
                "mode": mode,
                "timestamp": asyncio.get_event_loop().time(),
            }

        except ImportError:
            logger.error("Board detector modules not available")
            return self._error_result("Board detection modules not installed")
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            return self._error_result(str(e))

    async def _analyze_cv2_frame(self, frame) -> dict:
        """Analyze OpenCV frame"""
        if not HAS_PIL:
            return self._error_result("PIL not available")

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(frame_rgb)
        return await self._analyze_image(pil_image, mode="webcam")

    # ─── Calibration ─────────────────────────────────────────────────────────────

    async def calibrate(self, image_data: str) -> list:
        """
        Calibrate board detection from base64 image.

        Returns:
            List of 4 corner points [[x,y], [x,y], [x,y], [x,y]]
        """
        try:
            # Decode base64 image
            if "," in image_data:
                image_data = image_data.split(",")[1]

            img_bytes = base64.b64decode(image_data)

            if HAS_PIL:
                img = Image.open(io.BytesIO(img_bytes))
            else:
                return []

            from recognition.board_detector import BoardDetector

            detector = BoardDetector()

            corners = await asyncio.get_event_loop().run_in_executor(
                None, lambda: detector.find_board_corners(img)
            )

            return corners or []

        except Exception as e:
            logger.error(f"Calibration error: {e}")
            return []

    # ─── Helpers ─────────────────────────────────────────────────────────────────

    def _error_result(self, message: str, confidence: float = 0.0) -> dict:
        return {
            "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            "confidence": confidence,
            "squares": {},
            "turn": "w",
            "mode": "screen",
            "timestamp": 0,
            "error": message,
        }
