"""
Quản lý Stockfish UCI engine.
"""

from __future__ import annotations

import time as time_mod
from dataclasses import dataclass, field

import chess
import chess.engine

from config import Config


@dataclass
class AnalysisResult:
    """Kết quả phân tích từ engine."""

    best_move: chess.Move | None = None
    best_move_san: str = "—"
    best_move_uci: str = "—"
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
    """Wrapper cho Stockfish."""

    def __init__(self, stockfish_path: str | None = None):
        self.path = stockfish_path or Config.STOCKFISH_PATH
        self._engine: chess.engine.SimpleEngine | None = None

    def start(self):
        """Khởi động engine."""
        if self._engine is not None:
            return

        if not self.path:
            raise FileNotFoundError("Chưa cấu hình đường dẫn Stockfish!")

        from pathlib import Path

        p = Path(self.path)
        if not p.exists():
            raise FileNotFoundError(
                f"Không tìm thấy Stockfish tại: {self.path}\n"
                f"Tải từ https://stockfishchess.org/download/"
            )

        print(f"[ENGINE] Đang khởi động Stockfish: {self.path}")
        self._engine = chess.engine.SimpleEngine.popen_uci(str(p))
        self._engine.configure(
            {
                "Threads": Config.ENGINE_THREADS,
                "Hash": Config.ENGINE_HASH_MB,
            }
        )
        print("[ENGINE] Stockfish sẵn sàng ✓")

    def stop(self):
        """Tắt engine."""
        if self._engine:
            try:
                self._engine.quit()
            except Exception:
                pass
            self._engine = None
            print("[ENGINE] Stockfish đã tắt")

    def analyze(
        self, fen: str, depth: int | None = None, time_limit: float | None = None
    ) -> AnalysisResult:
        """Phân tích vị trí, trả về nước đi tốt nhất + đánh giá."""
        if not self._engine:
            self.start()

        board = chess.Board(fen)

        # Kiểm tra game đã kết thúc chưa
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
        """Trả về top N nước đi."""
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
        """Parse kết quả từ engine."""
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
                    eval_text = f"Thắng — Chiếu hết trong {score_mate} nước"
                elif score_mate < 0:
                    eval_text = f"Thua — Bị chiếu hết trong {abs(score_mate)} nước"
                else:
                    eval_text = "Chiếu hết"
            else:
                score_cp = pov.score()
                if score_cp is not None:
                    cp = score_cp / 100.0
                    if abs(cp) < 0.3:
                        eval_text = "Cân bằng"
                    elif cp > 3.0:
                        eval_text = f"Ưu thế lớn (+{cp:.2f})"
                    elif cp > 1.0:
                        eval_text = f"Ưu thế (+{cp:.2f})"
                    elif cp > 0:
                        eval_text = f"Hơi hơn (+{cp:.2f})"
                    elif cp < -3.0:
                        eval_text = f"Bất lợi lớn ({cp:.2f})"
                    elif cp < -1.0:
                        eval_text = f"Bất lợi ({cp:.2f})"
                    else:
                        eval_text = f"Hơi kém ({cp:.2f})"

        # Principal variation dạng SAN
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

        return AnalysisResult(
            best_move=best_move,
            best_move_san=best_san,
            best_move_uci=best_uci,
            score_cp=score_cp,
            score_mate=score_mate,
            depth=info.get("depth", depth),
            pv=pv_san,
            evaluation_text=eval_text,
            thinking_time=round(elapsed, 2),
        )

    def _game_over_text(self, board: chess.Board) -> str:
        """Mô tả kết thúc ván."""
        if board.is_checkmate():
            winner = "Đen" if board.turn else "Trắng"
            return f"Chiếu hết! {winner} thắng"
        if board.is_stalemate():
            return "Hết nước (Stalemate) — Hòa"
        if board.is_insufficient_material():
            return "Không đủ quân — Hòa"
        if board.is_fifty_moves():
            return "Luật 50 nước — Hòa"
        if board.is_repetition():
            return "Lặp thế 3 lần — Hòa"
        return "Ván đã kết thúc"

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()

    def __del__(self):
        self.stop()
