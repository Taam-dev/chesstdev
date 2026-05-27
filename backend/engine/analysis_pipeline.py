"""
Analysis Pipeline - Manages continuous position analysis with callbacks
"""

import asyncio
import logging
import chess
from typing import Optional, Callable
from .stockfish_manager import StockfishManager

logger = logging.getLogger(__name__)


class AnalysisPipeline:
    """
    Manages the analysis workflow:
    1. Receives FEN positions
    2. Sends to Stockfish
    3. Processes updates in real-time
    4. Broadcasts to WebSocket clients
    """

    def __init__(self, stockfish: StockfishManager):
        self.stockfish = stockfish
        self._current_task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
        self._current_fen = ""
        self._lines_buffer: list = []  # Accumulates MultiPV lines

    async def analyze(
        self,
        fen: str,
        depth: int = 20,
        multi_pv: int = 3,
        callback: Optional[Callable] = None,
    ) -> Optional[dict]:
        """
        Start analysis of a position.
        Cancels any previous analysis automatically.
        """
        # Cancel previous analysis
        await self.stop()

        self._current_fen = fen
        self._stop_event.clear()
        self._lines_buffer = [{} for _ in range(multi_pv)]

        try:
            board = chess.Board(fen)
        except ValueError as e:
            logger.error(f"Invalid FEN: {e}")
            return None

        if board.is_game_over():
            return self._game_over_result(board)

        # Wrap callback to accumulate lines
        async def enriched_callback(data: dict):
            line_update = data.pop("_line_update", None)
            if line_update:
                idx = line_update["index"]
                line = line_update["line"]
                if idx < len(self._lines_buffer):
                    self._lines_buffer[idx] = line

            # Add accumulated lines to response
            valid_lines = [l for l in self._lines_buffer if l]
            data["lines"] = valid_lines

            if callback:
                await callback(data)

        try:
            result = await self.stockfish.analyze(
                board=board,
                depth=depth,
                multi_pv=multi_pv,
                callback=enriched_callback,
            )

            if result:
                result["lines"] = [l for l in self._lines_buffer if l]

            return result

        except asyncio.CancelledError:
            logger.debug("Analysis cancelled")
            return None
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            raise

    async def stop(self):
        """Stop current analysis"""
        if self._current_task and not self._current_task.done():
            self._current_task.cancel()
            try:
                await self._current_task
            except asyncio.CancelledError:
                pass
        self._stop_event.set()
        await self.stockfish.stop_analysis()

    def _game_over_result(self, board: chess.Board) -> dict:
        """Return result for game over positions"""
        result = {
            "fen": board.fen(),
            "depth": 0,
            "evaluation": 0,
            "mate": 0,
            "bestMove": "",
            "bestMoveSAN": "",
            "principalVariation": [],
            "lines": [],
            "nodes": 0,
            "nps": 0,
            "time": 0,
            "isAnalyzing": False,
            "gameOver": True,
        }

        if board.is_checkmate():
            result["mate"] = 0
            result["evaluation"] = -30000 if board.turn == chess.WHITE else 30000
        elif board.is_stalemate():
            result["gameOver"] = "stalemate"
        elif board.is_insufficient_material():
            result["gameOver"] = "draw"

        return result
