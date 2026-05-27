"""
Stockfish Manager - Handles Stockfish process lifecycle and UCI communication
"""

import asyncio
import logging
import os
import platform
import subprocess
from pathlib import Path
from typing import Optional, Callable
import chess
import chess.engine

logger = logging.getLogger(__name__)


class StockfishManager:
    """
    Manages the Stockfish chess engine process.

    Uses python-chess for UCI communication - it handles the protocol
    details so we can focus on analysis logic.
    """

    # Default paths to search for Stockfish
    DEFAULT_PATHS = {
        "windows": [
            "assets/engines/stockfish.exe",
            "stockfish.exe",
            "C:/Program Files/Stockfish/stockfish.exe",
            r"%USERPROFILE%\stockfish\stockfish.exe",
        ],
        "linux": [
            "/usr/bin/stockfish",
            "/usr/local/bin/stockfish",
            "stockfish",
            "assets/engines/stockfish",
        ],
        "darwin": [
            "/opt/homebrew/bin/stockfish",
            "/usr/local/bin/stockfish",
            "stockfish",
        ],
    }

    def __init__(self, engine_path: str = ""):
        self.engine_path = engine_path
        self.engine: Optional[chess.engine.SimpleEngine] = None
        self.is_ready = False
        self.version = "Unknown"
        self._options: dict = {}
        self._lock = asyncio.Lock()

    async def initialize(self) -> bool:
        """Find and start Stockfish engine"""
        # Find engine path
        if not self.engine_path or not Path(self.engine_path).exists():
            self.engine_path = self._find_engine()

        if not self.engine_path:
            logger.error(
                "Stockfish not found! Please install Stockfish or set ENGINE_PATH."
            )
            return False

        logger.info(f"Starting Stockfish: {self.engine_path}")

        try:
            # Start engine in executor (blocking operation)
            loop = asyncio.get_event_loop()
            self.engine = await loop.run_in_executor(
                None, lambda: chess.engine.SimpleEngine.popen_uci(self.engine_path)
            )

            # Get engine version info
            info = self.engine.id
            self.version = info.get("name", "Stockfish")
            logger.info(f"Engine version: {self.version}")

            # Set default options
            await self._configure_defaults()

            self.is_ready = True
            return True

        except FileNotFoundError:
            logger.error(f"Engine file not found: {self.engine_path}")
            return False
        except Exception as e:
            logger.error(f"Failed to start engine: {e}")
            return False

    def _find_engine(self) -> str:
        """Auto-detect Stockfish in common locations"""
        system = platform.system().lower()
        if system == "windows":
            paths = self.DEFAULT_PATHS["windows"]
        elif system == "linux":
            paths = self.DEFAULT_PATHS["linux"]
        elif system == "darwin":
            paths = self.DEFAULT_PATHS["darwin"]
        else:
            paths = self.DEFAULT_PATHS["linux"]

        # Expand environment variables
        for path in paths:
            expanded = os.path.expandvars(os.path.expanduser(path))
            if Path(expanded).exists():
                logger.info(f"Found Stockfish at: {expanded}")
                return expanded

        # Try PATH
        try:
            result = subprocess.run(
                (
                    ["which", "stockfish"]
                    if platform.system() != "Windows"
                    else ["where", "stockfish"]
                ),
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                path = result.stdout.strip().split("\n")[0]
                if path:
                    return path
        except Exception:
            pass

        return ""

    async def _configure_defaults(self):
        """Configure optimal default engine options"""
        import os

        cpu_count = os.cpu_count() or 2
        threads = max(1, min(cpu_count - 1, 4))  # Leave one core for UI

        defaults = {
            "Threads": threads,
            "Hash": 256,  # MB
            "MultiPV": 3,
            "Use NNUE": True,
            "Move Overhead": 10,
        }

        for option, value in defaults.items():
            try:
                if option in self.engine.options:
                    self.engine.configure({option: value})
                    self._options[option] = value
            except Exception as e:
                logger.debug(f"Option '{option}' not available: {e}")

    async def set_option(self, option: str, value) -> bool:
        """Update engine option"""
        if not self.engine or not self.is_ready:
            return False
        try:
            async with self._lock:
                self.engine.configure({option: value})
                self._options[option] = value
                logger.debug(f"Set option {option} = {value}")
            return True
        except Exception as e:
            logger.error(f"Failed to set option {option}: {e}")
            return False

    def get_options(self) -> dict:
        """Get current engine options"""
        if not self.engine:
            return {}
        return {
            name: str(opt)
            for name, opt in self.engine.options.items()
            if not name.startswith("_")
        }

    async def analyze(
        self,
        board: chess.Board,
        depth: int = 20,
        multi_pv: int = 3,
        callback: Optional[Callable] = None,
    ) -> Optional[dict]:
        """
        Analyze a position with Stockfish.

        Args:
            board: Chess board position
            depth: Analysis depth (higher = stronger but slower)
            multi_pv: Number of principal variations to calculate
            callback: Called with each engine update

        Returns:
            Final analysis result
        """
        if not self.engine or not self.is_ready:
            raise RuntimeError("Engine not ready")

        async with self._lock:
            # Configure MultiPV
            self.engine.configure({"MultiPV": multi_pv})

            result_data = {
                "fen": board.fen(),
                "depth": 0,
                "evaluation": 0,
                "mate": None,
                "bestMove": "",
                "bestMoveSAN": "",
                "principalVariation": [],
                "lines": [],
                "nodes": 0,
                "nps": 0,
                "time": 0,
                "isAnalyzing": True,
            }

            try:
                loop = asyncio.get_event_loop()

                with self.engine.analysis(
                    board,
                    chess.engine.Limit(depth=depth),
                    multipv=multi_pv,
                ) as analysis:
                    async for info in self._async_analysis(analysis):
                        # Parse info
                        updated = self._parse_info(info, board, multi_pv)
                        if updated:
                            result_data.update(updated)
                            result_data["isAnalyzing"] = True

                            if callback:
                                await callback(result_data.copy())

                result_data["isAnalyzing"] = False
                return result_data

            except chess.engine.AnalysisComplete:
                result_data["isAnalyzing"] = False
                return result_data
            except Exception as e:
                logger.error(f"Analysis error: {e}")
                raise

    async def _async_analysis(self, analysis):
        """Convert synchronous analysis iterator to async generator"""
        loop = asyncio.get_event_loop()
        while True:
            info = await loop.run_in_executor(None, next, iter(analysis), None)
            if info is None:
                break
            yield info

    def _parse_info(
        self, info: chess.engine.Info, board: chess.Board, multi_pv: int
    ) -> dict:
        """Parse Stockfish info into our format"""
        result = {}

        depth = info.get("depth", 0)
        if not depth:
            return {}

        result["depth"] = depth
        result["nodes"] = info.get("nodes", 0)
        result["nps"] = info.get("nps", 0)
        result["time"] = info.get("time", 0)

        # Evaluation
        score = info.get("score")
        if score:
            pov_score = score.pov(board.turn)
            if pov_score.is_mate():
                mate_in = pov_score.mate()
                result["mate"] = mate_in
                result["evaluation"] = 30000 if mate_in > 0 else -30000
            else:
                cp = pov_score.score(mate_score=30000)
                # Convert to white's perspective
                if board.turn == chess.BLACK:
                    cp = -cp
                result["evaluation"] = cp
                result["mate"] = None

        # Principal variation
        pv = info.get("pv", [])
        if pv and len(pv) > 0:
            best_move = pv[0]
            result["bestMove"] = best_move.uci()

            # Convert to SAN
            try:
                san_moves = []
                temp_board = board.copy()
                for move in pv[:10]:
                    san = temp_board.san(move)
                    san_moves.append(san)
                    temp_board.push(move)
                result["principalVariation"] = san_moves
                result["bestMoveSAN"] = san_moves[0] if san_moves else ""
            except Exception:
                result["bestMoveSAN"] = best_move.uci()

        # MultiPV lines (accumulated)
        multipv_idx = info.get("multipv", 1) - 1

        # Lines are built from multiple info updates
        line_eval = 0
        line_mate = None

        if score := info.get("score"):
            pov = score.pov(board.turn)
            if pov.is_mate():
                line_mate = pov.mate()
            else:
                cp = pov.score(mate_score=30000) or 0
                if board.turn == chess.BLACK:
                    cp = -cp
                line_eval = cp

        if pv:
            try:
                san_moves = []
                temp = board.copy()
                for move in pv[:10]:
                    san_moves.append(temp.san(move))
                    temp.push(move)

                line = {
                    "moves": san_moves,
                    "evaluation": line_eval,
                    "mate": line_mate,
                    "depth": depth,
                    "multiPV": multipv_idx + 1,
                }
                result["_line_update"] = {"index": multipv_idx, "line": line}
            except Exception:
                pass

        return result

    async def stop_analysis(self):
        """Stop ongoing analysis"""
        # python-chess analysis stops when context manager exits
        pass

    async def benchmark(self) -> dict:
        """Run engine benchmark"""
        if not self.engine or not self.is_ready:
            return {"error": "Engine not ready"}

        board = chess.Board()
        import time

        start = time.time()
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self.engine.play(
                board,
                chess.engine.Limit(time=1.0),
            ),
        )
        elapsed = time.time() - start

        return {
            "move": result.move.uci() if result.move else "",
            "time": elapsed,
            "nps": result.info.get("nps", 0) if result.info else 0,
        }

    async def shutdown(self):
        """Cleanly shut down the engine"""
        if self.engine:
            try:
                self.engine.quit()
                logger.info("Stockfish engine shut down")
            except Exception as e:
                logger.error(f"Error shutting down engine: {e}")
            finally:
                self.engine = None
                self.is_ready = False
