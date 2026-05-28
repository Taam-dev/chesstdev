"""
Manage Stockfish UCI engine.
"""

from __future__ import annotations

import time as time_mod
from dataclasses import dataclass, field

import chess
import chess.engine

from config import Config


@dataclass
class AnalysisResult:
    """Analysis result from the engine."""

    best_move: chess.Move | None = None
    best_move_san: str = "—"
    best_move_uci: str = "—"
    best_move_desc: str = ""
    score_cp: int | None = None
    score_mate: int | None = None
    depth: int = 0
    pv: list = field(default_factory=list)
    evaluation_text: str = "Unknown"
    thinking_time: float = 0.0

    @property
    def score_display(self) -> str:
        if self.score_mate is not None:
            sign = "+" if self.score_mate > 0 else ""
            return f"#{sign}{self.score_mate}"
        if self.score_cp is not None:
            val = self.score_cp / 100.0
            sign = "+" if val > 0 else ""
            return f"{sign}{val:.2f}"
        return "?"


class EngineManager:
    """Wrapper for Stockfish."""

    def __init__(self, stockfish_path: str | None = None):
        self.path = stockfish_path or Config.STOCKFISH_PATH
        self._engine: chess.engine.SimpleEngine | None = None

    def start(self):
        """Start the engine."""
        if self._engine is not None:
            return

        if not self.path:
            raise FileNotFoundError("Stockfish path is not configured!")

        from pathlib import Path

        p = Path(self.path)
        if not p.exists():
            raise FileNotFoundError(
                f"Stockfish not found at: {self.path}\n"
                f"Download from https://stockfishchess.org/download/"
            )

        print(f"[ENGINE] Starting Stockfish: {self.path}")
        self._engine = chess.engine.SimpleEngine.popen_uci(str(p))
        self._engine.configure(
            {
                "Threads": Config.ENGINE_THREADS,
                "Hash": Config.ENGINE_HASH_MB,
            }
        )
        print("[ENGINE] Stockfish ready ✓")

    def stop(self):
        """Stop the engine."""
        if self._engine:
            try:
                self._engine.quit()
            except Exception:
                pass
            self._engine = None
            print("[ENGINE] Stockfish stopped")

    def analyze(
        self, fen: str, depth: int | None = None, time_limit: float | None = None
    ) -> AnalysisResult:
        """Analyze position, returning best move + evaluation."""
        if not self._engine:
            self.start()

        board = chess.Board(fen)

        # Check if game is over
        if board.is_game_over():
            return AnalysisResult(evaluation_text=self._game_over_text(board))

        _depth = depth or Config.ENGINE_DEPTH
        _time = time_limit or Config.ENGINE_TIME_LIMIT

        limit = chess.engine.Limit(depth=_depth, time=_time)

        t0 = time_mod.perf_counter()
        result = self._engine.analyse(board, limit, info=chess.engine.INFO_ALL)
        elapsed = time_mod.perf_counter() - t0

        return self._parse_result(board, result, _depth, elapsed)

    def get_top_moves(
        self, fen: str, count: int = 3, depth: int | None = None
    ) -> list[AnalysisResult]:
        """Return top N moves."""
        if not self._engine:
            self.start()

        board = chess.Board(fen)

        if board.is_game_over():
            return [AnalysisResult(evaluation_text=self._game_over_text(board))]

        _depth = depth or Config.ENGINE_DEPTH
        limit = chess.engine.Limit(depth=_depth, time=Config.ENGINE_TIME_LIMIT)

        t0 = time_mod.perf_counter()
        infos = self._engine.analyse(board, limit, multipv=count)
        elapsed = time_mod.perf_counter() - t0

        results = []
        for info in infos:
            results.append(self._parse_result(board, info, _depth, elapsed))

        return results

    def _parse_result(
        self, board: chess.Board, info: dict, depth: int, elapsed: float
    ) -> AnalysisResult:
        """Parse engine analysis results."""
        pv_moves = info.get("pv", [])
        best_move = pv_moves[0] if pv_moves else None

        score = info.get("score")
        score_cp = None
        score_mate = None
        eval_text = "?"

        if score:
            pov = score.relative
            if pov.is_mate():
                score_mate = pov.mate()
                if score_mate > 0:
                    eval_text = f"Winning — Mate in {score_mate} moves"
                elif score_mate < 0:
                    eval_text = f"Losing — Mated in {abs(score_mate)} moves"
                else:
                    eval_text = "Checkmate"
            else:
                score_cp = pov.score()
                if score_cp is not None:
                    cp = score_cp / 100.0
                    if abs(cp) < 0.3:
                        eval_text = "Balanced"
                    elif cp > 3.0:
                        eval_text = f"Large advantage (+{cp:.2f})"
                    elif cp > 1.0:
                        eval_text = f"Advantage (+{cp:.2f})"
                    elif cp > 0:
                        eval_text = f"Slight advantage (+{cp:.2f})"
                    elif cp < -3.0:
                        eval_text = f"Large disadvantage ({cp:.2f})"
                    elif cp < -1.0:
                        eval_text = f"Disadvantage ({cp:.2f})"
                    else:
                        eval_text = f"Slight disadvantage ({cp:.2f})"

        # Principal variation in SAN format
        pv_san = []
        temp_board = board.copy()
        for mv in pv_moves[:8]:
            try:
                pv_san.append(temp_board.san(mv))
                temp_board.push(mv)
            except Exception:
                break

        best_san = board.san(best_move) if best_move else "—"
        best_uci = best_move.uci() if best_move else "—"

        best_desc = ""
        if best_move:
            best_desc = self._get_move_description(board, best_move)

        return AnalysisResult(
            best_move=best_move,
            best_move_san=best_san,
            best_move_uci=best_uci,
            best_move_desc=best_desc,
            score_cp=score_cp,
            score_mate=score_mate,
            depth=info.get("depth", depth),
            pv=pv_san,
            evaluation_text=eval_text,
            thinking_time=round(elapsed, 2),
        )

    def _get_move_description(self, board: chess.Board, move: chess.Move) -> str:
        """Provide a detailed, beginner-friendly explanation of a chess move."""
        if not move:
            return ""

        # Check castling
        if board.is_kingside_castling(move):
            return "Kingside castle"
        if board.is_queenside_castling(move):
            return "Queenside castle"

        piece = board.piece_at(move.from_square)
        if not piece:
            return ""

        piece_names = {
            chess.PAWN: "Pawn",
            chess.KNIGHT: "Knight",
            chess.BISHOP: "Bishop",
            chess.ROOK: "Rook",
            chess.QUEEN: "Queen",
            chess.KING: "King"
        }
        piece_name = piece_names.get(piece.piece_type, "Piece")
        to_square_name = chess.square_name(move.to_square)

        is_capture = board.is_capture(move)

        promotion_name = ""
        if move.promotion:
            prom_names = {
                chess.KNIGHT: "Knight",
                chess.BISHOP: "Bishop",
                chess.ROOK: "Rook",
                chess.QUEEN: "Queen"
            }
            promotion_name = f", promoting to {prom_names.get(move.promotion, 'Queen')}"

        # Copy board to check if the move results in check or checkmate
        board_copy = board.copy()
        try:
            board_copy.push(move)
            if board_copy.is_checkmate():
                status = " (checkmate)"
            elif board_copy.is_check():
                status = " (check)"
            else:
                status = ""
        except Exception:
            status = ""

        if is_capture:
            captured_piece = board.piece_at(move.to_square)
            if captured_piece:
                captured_name = piece_names.get(captured_piece.piece_type, "piece").lower()
                return f"{piece_name} takes {captured_name} on {to_square_name}{promotion_name}{status}"
            elif board.is_en_passant(move):
                return f"{piece_name} takes Pawn en passant on {to_square_name}{promotion_name}{status}"
            else:
                return f"{piece_name} takes on {to_square_name}{promotion_name}{status}"
        else:
            return f"{piece_name} to {to_square_name}{promotion_name}{status}"

    def _game_over_text(self, board: chess.Board) -> str:
        """Describe the game over condition."""
        if board.is_checkmate():
            winner = "Black" if board.turn else "White"
            return f"Checkmate! {winner} wins"
        if board.is_stalemate():
            return "Stalemate — Draw"
        if board.is_insufficient_material():
            return "Insufficient material — Draw"
        if board.is_fifty_moves():
            return "50-move rule — Draw"
        if board.is_repetition():
            return "Threefold repetition — Draw"
        return "Game over"

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()

    def __del__(self):
        self.stop()
