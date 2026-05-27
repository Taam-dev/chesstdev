"""
Move Classifier - Classifies moves into quality categories
brilliant / great / best / good / inaccuracy / mistake / blunder
"""

import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class MoveClassification:
    label: str  # brilliant, great, best, good, inaccuracy, mistake, blunder
    symbol: str  # !!, !, □, , ?!, ?, ??
    color: str  # hex color
    description: str
    score_diff: float  # centipawns lost vs best move (negative = worse)

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "symbol": self.symbol,
            "color": self.color,
            "description": self.description,
            "scoreDiff": self.score_diff,
        }


# ─── Thresholds (centipawns) ──────────────────────────────────────────────────

THRESHOLDS = {
    "best": 0,  # = best move evaluation
    "good": -10,  # within 10 cp
    "inaccuracy": -50,  # 10–50 cp worse
    "mistake": -150,  # 50–150 cp worse
    "blunder": -300,  # > 150 cp worse
}

CLASSIFICATIONS = {
    "brilliant": MoveClassification(
        label="brilliant",
        symbol="!!",
        color="#00d4ff",
        description="Brilliant! A stunning move that was extremely hard to find.",
        score_diff=0,
    ),
    "great": MoveClassification(
        label="great",
        symbol="!",
        color="#50fa7b",
        description="Great move! Significantly better than obvious alternatives.",
        score_diff=0,
    ),
    "best": MoveClassification(
        label="best",
        symbol="□",
        color="#50fa7b",
        description="Best move. The computer's top choice.",
        score_diff=0,
    ),
    "good": MoveClassification(
        label="good",
        symbol="",
        color="#8be9fd",
        description="Good move. Maintains a solid position.",
        score_diff=0,
    ),
    "inaccuracy": MoveClassification(
        label="inaccuracy",
        symbol="?!",
        color="#ffb86c",
        description="Inaccuracy. A slight mistake, but not immediately losing.",
        score_diff=0,
    ),
    "mistake": MoveClassification(
        label="mistake",
        symbol="?",
        color="#ff9800",
        description="Mistake. A significant error that weakens your position.",
        score_diff=0,
    ),
    "blunder": MoveClassification(
        label="blunder",
        symbol="??",
        color="#ff5555",
        description="Blunder! A serious error that loses material or the game.",
        score_diff=0,
    ),
    "miss": MoveClassification(
        label="miss",
        symbol="??",
        color="#ff5555",
        description="Missed a winning opportunity.",
        score_diff=0,
    ),
}


class MoveClassifier:
    """
    Classifies chess moves by comparing evaluation before/after.

    Usage:
        classifier = MoveClassifier()
        result = classifier.classify(
            eval_before=100,      # evaluation before move (from current player's POV)
            eval_after=-80,       # evaluation after move (from current player's POV, negated)
            best_eval=100,        # best possible evaluation
            is_sacrifice=False,
            is_only_move=False,
        )
    """

    def classify(
        self,
        eval_best: float,  # Best move evaluation (centipawns, from mover's POV)
        eval_played: float,  # Played move evaluation (centipawns, from mover's POV)
        position_eval_before: float = 0,  # Position eval before (for context)
        is_sacrifice: bool = False,  # Material sacrifice detected
        winning_before: bool = False,  # Was player winning before?
        is_forced: bool = False,  # Only legal move?
    ) -> MoveClassification:
        """
        Classify a move based on evaluation delta.

        Args:
            eval_best: Engine's best eval for this position (centipawns)
            eval_played: Eval after the played move (centipawns)
            position_eval_before: Evaluation before the move
            is_sacrifice: Was material sacrificed?
            winning_before: Was the player winning before?
            is_forced: Was this the only legal move?

        Returns:
            MoveClassification with label, symbol, color, description
        """
        score_diff = eval_played - eval_best  # Negative = worse than best

        # Make a copy to set the score_diff
        classification = self._get_base_classification(
            score_diff=score_diff,
            eval_best=eval_best,
            eval_played=eval_played,
            is_sacrifice=is_sacrifice,
            winning_before=winning_before,
            is_forced=is_forced,
        )

        # Return copy with actual score diff
        import copy

        result = copy.copy(classification)
        result.score_diff = score_diff
        return result

    def _get_base_classification(
        self,
        score_diff: float,
        eval_best: float,
        eval_played: float,
        is_sacrifice: bool,
        winning_before: bool,
        is_forced: bool,
    ) -> MoveClassification:
        """Internal classification logic"""

        # Check for brilliant: sacrifice that is best/near-best move
        if (
            is_sacrifice
            and score_diff >= THRESHOLDS["good"]  # Within 10 cp of best
            and eval_best > 100  # Was already winning
        ):
            return CLASSIFICATIONS["brilliant"]

        # Check for great: significantly better than non-obvious alternatives
        # (simplified: near-best in winning position)
        if score_diff >= THRESHOLDS["good"] and is_sacrifice and eval_best > 50:
            return CLASSIFICATIONS["great"]

        # Best move
        if score_diff >= THRESHOLDS["best"]:
            return CLASSIFICATIONS["best"]

        # Good move (within 10 cp)
        if score_diff >= THRESHOLDS["good"]:
            return CLASSIFICATIONS["good"]

        # Inaccuracy (10-50 cp worse)
        if score_diff >= THRESHOLDS["inaccuracy"]:
            return CLASSIFICATIONS["inaccuracy"]

        # Mistake (50-150 cp worse)
        if score_diff >= THRESHOLDS["mistake"]:
            return CLASSIFICATIONS["mistake"]

        # Blunder / Miss
        if winning_before and eval_played < -50:
            # Had winning position but threw it away
            return CLASSIFICATIONS["miss"]

        return CLASSIFICATIONS["blunder"]

    def classify_from_analysis(
        self,
        best_move_eval: float,
        played_move_eval: float,
        played_move_uci: str,
        best_move_uci: str,
        captures_material: bool = False,
        position_eval: float = 0,
    ) -> MoveClassification:
        """
        Convenience method: classify directly from analysis data.

        Args:
            best_move_eval: Engine's evaluation of best move (centipawns, white POV)
            played_move_eval: Evaluation after played move (centipawns, white POV)
            played_move_uci: The move played (e.g. "e2e4")
            best_move_uci: Engine's best move (e.g. "d2d4")
            captures_material: Does the played move capture a piece?
            position_eval: Position evaluation before the move

        Returns:
            MoveClassification
        """
        is_best = played_move_uci == best_move_uci
        is_sacrifice = captures_material and (played_move_eval < position_eval - 100)
        winning_before = abs(position_eval) > 150 and position_eval > 0

        return self.classify(
            eval_best=best_move_eval,
            eval_played=played_move_eval,
            position_eval_before=position_eval,
            is_sacrifice=is_sacrifice,
            winning_before=winning_before,
        )

    def batch_classify(self, moves_data: list[dict]) -> list[MoveClassification]:
        """
        Classify a list of moves from a game.

        Each item in moves_data should have:
            - best_eval: float
            - played_eval: float
            - best_move: str (UCI)
            - played_move: str (UCI)
            - position_eval: float (optional)

        Returns:
            List of MoveClassification
        """
        results = []
        for move_data in moves_data:
            try:
                result = self.classify_from_analysis(
                    best_move_eval=move_data.get("best_eval", 0),
                    played_move_eval=move_data.get("played_eval", 0),
                    played_move_uci=move_data.get("played_move", ""),
                    best_move_uci=move_data.get("best_move", ""),
                    captures_material=move_data.get("captures", False),
                    position_eval=move_data.get("position_eval", 0),
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Classification error: {e}")
                results.append(CLASSIFICATIONS["good"])

        return results

    def get_accuracy_score(self, classifications: list[MoveClassification]) -> float:
        """
        Calculate overall accuracy score (0-100) from a list of classifications.
        Similar to Chess.com's accuracy metric.
        """
        if not classifications:
            return 100.0

        score_map = {
            "brilliant": 100,
            "great": 100,
            "best": 100,
            "good": 90,
            "inaccuracy": 70,
            "mistake": 40,
            "blunder": 0,
            "miss": 10,
        }

        total = sum(score_map.get(c.label, 50) for c in classifications)
        return round(total / len(classifications), 1)
