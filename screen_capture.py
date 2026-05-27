"""
High-performance screen capture using mss.
Falls back to pyautogui if mss is unavailable.
"""

from __future__ import annotations

import numpy as np
from PIL import Image

try:
    import mss
    import mss.tools

    _USE_MSS = True
except ImportError:
    _USE_MSS = False
    import pyautogui


class ScreenCapture:
    """Captures screenshots of the entire screen or a specific region."""

    def __init__(self):
        self._sct = mss.mss() if _USE_MSS else None

    def grab_full_screen(self, monitor_index: int = 1) -> np.ndarray:
        """Return the full screen as a BGR numpy array (OpenCV format)."""
        if self._sct:
            monitor = self._sct.monitors[monitor_index]
            sct_img = self._sct.grab(monitor)
            frame = np.array(sct_img)
            # mss gives BGRA, convert to BGR
            return frame[:, :, :3]
        else:
            img = pyautogui.screenshot()
            frame = np.array(img)
            # pyautogui gives RGB, convert to BGR
            return frame[:, :, ::-1]

    def grab_region(self, x: int, y: int, w: int, h: int) -> np.ndarray:
        """Capture a specific screen region, return BGR numpy array."""
        if self._sct:
            region = {"left": x, "top": y, "width": w, "height": h}
            sct_img = self._sct.grab(region)
            frame = np.array(sct_img)
            return frame[:, :, :3]
        else:
            img = pyautogui.screenshot(region=(x, y, w, h))
            frame = np.array(img)
            return frame[:, :, ::-1]

    def close(self):
        if self._sct:
            self._sct.close()
