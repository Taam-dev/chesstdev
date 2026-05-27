"""
Tactics Detector - Identifies tactical patterns in chess positions
"""

import chess
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


class TacticsDetector:
    """
    Detects tactical patterns:
    - Forks
    - Pins
    - Skewers
    - Discovered attacks
    - Mating nets
    - Hanging pieces
    - Passed pawns
    - Weak squares
    - Open files
    """

    PIECE_VALUES = {
        chess.PAWN: 100,
        chess.KNIGHT: 320,
        chess.BISHOP: 330,
        chess.ROOK: 500,
        chess.QUEEN: 900,
        chess.KING: 20000,
    }

    async def detect(self, fen: str, analysis: dict = None) -> List[dict]:
        """Detect all tactical patterns in a position"""
        try:
            board = chess.Board(fen)
        except ValueError:
            return []

        tactics = []

        # Run all detectors
        tactics.extend(self._detect_hanging_pieces(board))
        tactics.extend(self._detect_forks(board))
        tactics.extend(self._detect_pins(board))
        tactics.extend(self._detect_skewers(board))
        tactics.extend(self._detect_passed_pawns(board))
        tactics.extend(self._detect_weak_squares(board))
        tactics.extend(self._detect_open_files(board))
        tactics.extend(self._detect_back_rank_threats(board))
        tactics.extend(self._detect_discovered_attacks(board))

        # Sort by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        tactics.sort(key=lambda t: severity_order.get(t.get("severity", "low"), 4))

        return tactics[:10]  # Return top 10 most important

    def _detect_hanging_pieces(self, board: chess.Board) -> List[dict]:
        """Find pieces that are undefended and can be captured"""
        tactics = []

        for color in [chess.WHITE, chess.BLACK]:
            opponent = not color

            for sq in chess.SQUARES:
                piece = board.piece_at(sq)
                if not piece or piece.color != color:
                    continue
                if piece.piece_type == chess.KING:
                    continue

                # Is this piece attacked by opponent?
                if not board.is_attacked_by(opponent, sq):
                    continue

                # Is it defended?
                if not board.is_attacked_by(color, sq):
                    piece_name = chess.piece_name(piece.piece_type)
                    value = self.PIECE_VALUES.get(piece.piece_type, 0)
                    severity = (
                        "critical"
                        if value >= 500
                        else "high" if value >= 300 else "medium"
                    )

                    tactics.append(
                        {
                            "type": "hanging_piece",
                            "description": f"{'White' if color == chess.WHITE else 'Black'}'s {piece_name} on {chess.square_name(sq)} is hanging (undefended and attacked)",
                            "squares": [chess.square_name(sq)],
                            "severity": severity,
                            "forColor": "white" if color == chess.WHITE else "black",
                        }
                    )

        return tactics

    def _detect_forks(self, board: chess.Board) -> List[dict]:
        """Find fork opportunities (one piece attacking multiple opponent pieces)"""
        tactics = []

        for color in [chess.WHITE, chess.BLACK]:
            opponent = not color

            for sq in chess.SQUARES:
                piece = board.piece_at(sq)
                if not piece or piece.color != color:
                    continue

                # Get all squares this piece attacks
                attacked_squares = list(board.attacks(sq))

                # Find valuable opponent pieces on attacked squares
                valuable_targets = []
                for attacked_sq in attacked_squares:
                    target = board.piece_at(attacked_sq)
                    if target and target.color == opponent:
                        if target.piece_type != chess.PAWN:  # Focus on piece forks
                            valuable_targets.append((attacked_sq, target))

                if len(valuable_targets) >= 2:
                    total_value = sum(
                        self.PIECE_VALUES.get(t.piece_type, 0)
                        for _, t in valuable_targets
                    )
                    piece_name = chess.piece_name(piece.piece_type)
                    target_names = [
                        chess.piece_name(t.piece_type) for _, t in valuable_targets
                    ]

                    tactics.append(
                        {
                            "type": "fork",
                            "description": f"{'White' if color == chess.WHITE else 'Black'}'s {piece_name} on {chess.square_name(sq)} forks {' and '.join(target_names[:2])}",
                            "squares": [chess.square_name(sq)]
                            + [chess.square_name(s) for s, _ in valuable_targets[:2]],
                            "severity": "critical" if total_value >= 1400 else "high",
                            "forColor": "white" if color == chess.WHITE else "black",
                        }
                    )

        return tactics

    def _detect_pins(self, board: chess.Board) -> List[dict]:
        """Find absolute and relative pins"""
        tactics = []

        for color in [chess.WHITE, chess.BLACK]:
            opponent = not color

            # Check for pins against king
            king_sq = board.king(color)
            if not king_sq:
                continue

            for pinning_sq in chess.SQUARES:
                pinning_piece = board.piece_at(pinning_sq)
                if not pinning_piece or pinning_piece.color != opponent:
                    continue
                if pinning_piece.piece_type not in [
                    chess.BISHOP,
                    chess.ROOK,
                    chess.QUEEN,
                ]:
                    continue

                # Check if there's a friendly piece between king and this piece
                between = chess.SquareSet(chess.between(king_sq, pinning_sq))
                pinned_squares = [
                    sq
                    for sq in between
                    if board.piece_at(sq) and board.piece_at(sq).color == color
                ]

                if len(pinned_squares) == 1:
                    pinned_sq = pinned_squares[0]
                    pinned = board.piece_at(pinned_sq)
                    pinned_name = chess.piece_name(pinned.piece_type)
                    pinner_name = chess.piece_name(pinning_piece.piece_type)

                    tactics.append(
                        {
                            "type": "pin",
                            "description": f"{'White' if color == chess.WHITE else 'Black'}'s {pinned_name} on {chess.square_name(pinned_sq)} is pinned by opponent's {pinner_name}",
                            "squares": [
                                chess.square_name(pinned_sq),
                                chess.square_name(pinning_sq),
                            ],
                            "severity": (
                                "high"
                                if pinned.piece_type in [chess.QUEEN, chess.ROOK]
                                else "medium"
                            ),
                            "forColor": "white" if color == chess.WHITE else "black",
                        }
                    )

        return tactics

    def _detect_skewers(self, board: chess.Board) -> List[dict]:
        """Find skewer opportunities (attack valuable piece through to another)"""
        tactics = []

        for color in [chess.WHITE, chess.BLACK]:
            opponent = not color

            for sq in chess.SQUARES:
                piece = board.piece_at(sq)
                if not piece or piece.color != color:
                    continue
                if piece.piece_type not in [chess.BISHOP, chess.ROOK, chess.QUEEN]:
                    continue

                # Check all rays from this piece
                rays = chess.SquareSet(board.attacks(sq))
                for attacked_sq in rays:
                    front_piece = board.piece_at(attacked_sq)
                    if not front_piece or front_piece.color != opponent:
                        continue

                    # Is there another opponent piece behind?
                    direction = self._get_direction(sq, attacked_sq)
                    if direction:
                        behind_sq = attacked_sq + direction
                        if chess.is_valid_square(behind_sq):
                            behind = board.piece_at(behind_sq)
                            if behind and behind.color == opponent:
                                front_val = self.PIECE_VALUES.get(
                                    front_piece.piece_type, 0
                                )
                                behind_val = self.PIECE_VALUES.get(behind.piece_type, 0)

                                if front_val >= behind_val and front_val >= 500:
                                    tactics.append(
                                        {
                                            "type": "skewer",
                                            "description": f"Skewer: {chess.piece_name(piece.piece_type)} attacks valuable {chess.piece_name(front_piece.piece_type)}, forcing it to move and exposing {chess.piece_name(behind.piece_type)}",
                                            "squares": [
                                                chess.square_name(sq),
                                                chess.square_name(attacked_sq),
                                                chess.square_name(behind_sq),
                                            ],
                                            "severity": "high",
                                            "forColor": (
                                                "white"
                                                if color == chess.WHITE
                                                else "black"
                                            ),
                                        }
                                    )

        return tactics[:3]  # Limit skewers

    def _detect_passed_pawns(self, board: chess.Board) -> List[dict]:
        """Find passed pawns"""
        tactics = []

        for color in [chess.WHITE, chess.BLACK]:
            opponent = not color
            our_pawns = board.pieces(chess.PAWN, color)

            for sq in our_pawns:
                file_idx = chess.square_file(sq)
                rank = chess.square_rank(sq)

                is_passed = True
                opponent_pawns = board.pieces(chess.PAWN, opponent)

                for opp_sq in opponent_pawns:
                    opp_file = chess.square_file(opp_sq)
                    opp_rank = chess.square_rank(opp_sq)

                    if abs(opp_file - file_idx) <= 1:
                        if color == chess.WHITE and opp_rank > rank:
                            is_passed = False
                            break
                        elif color == chess.BLACK and opp_rank < rank:
                            is_passed = False
                            break

                if is_passed:
                    # How advanced is it?
                    advancement = rank if color == chess.WHITE else 7 - rank
                    severity = (
                        "critical"
                        if advancement >= 6
                        else "high" if advancement >= 4 else "medium"
                    )

                    tactics.append(
                        {
                            "type": "passed_pawn",
                            "description": f"{'White' if color == chess.WHITE else 'Black'} has a passed pawn on {chess.square_name(sq)} with no opposing pawns blocking promotion",
                            "squares": [chess.square_name(sq)],
                            "severity": severity,
                            "forColor": "white" if color == chess.WHITE else "black",
                        }
                    )

        return tactics

    def _detect_weak_squares(self, board: chess.Board) -> List[dict]:
        """Find weak squares (no pawn protection and occupied by opponent)"""
        tactics = []
        key_squares = [
            chess.D5,
            chess.E5,
            chess.D4,
            chess.E4,  # Center
            chess.F5,
            chess.C5,
            chess.F4,
            chess.C4,  # Extended center
        ]

        for sq in key_squares:
            for color in [chess.WHITE, chess.BLACK]:
                opponent = not color

                # Is this square occupied by opponent piece?
                piece = board.piece_at(sq)
                if not piece or piece.color != opponent:
                    continue

                # Can we attack or control it?
                if board.is_attacked_by(color, sq) and not board.is_attacked_by(
                    opponent, sq
                ):
                    tactics.append(
                        {
                            "type": "weak_square",
                            "description": f"Weak square on {chess.square_name(sq)} — opponent's {chess.piece_name(piece.piece_type)} occupies it without adequate protection",
                            "squares": [chess.square_name(sq)],
                            "severity": "medium",
                            "forColor": "white" if color == chess.WHITE else "black",
                        }
                    )

        return tactics[:2]

    def _detect_open_files(self, board: chess.Board) -> List[dict]:
        """Find open and semi-open files for rook activity"""
        tactics = []

        for file_idx in range(8):
            file_letter = chr(ord("a") + file_idx)
            white_pawns = len(
                [
                    sq
                    for sq in board.pieces(chess.PAWN, chess.WHITE)
                    if chess.square_file(sq) == file_idx
                ]
            )
            black_pawns = len(
                [
                    sq
                    for sq in board.pieces(chess.PAWN, chess.BLACK)
                    if chess.square_file(sq) == file_idx
                ]
            )

            if white_pawns == 0 and black_pawns == 0:
                # Open file - check if rook on or near this file
                for color in [chess.WHITE, chess.BLACK]:
                    rooks = board.pieces(chess.ROOK, color)
                    for rook_sq in rooks:
                        if chess.square_file(rook_sq) == file_idx:
                            tactics.append(
                                {
                                    "type": "open_file",
                                    "description": f"{'White' if color == chess.WHITE else 'Black'} rook controls open {file_letter.upper()}-file",
                                    "squares": [chess.square_name(rook_sq)],
                                    "severity": "low",
                                    "forColor": (
                                        "white" if color == chess.WHITE else "black"
                                    ),
                                }
                            )

        return tactics[:3]

    def _detect_back_rank_threats(self, board: chess.Board) -> List[dict]:
        """Detect back-rank checkmate threats"""
        tactics = []

        for color in [chess.WHITE, chess.BLACK]:
            opponent = not color
            back_rank = 0 if color == chess.WHITE else 7
            king_sq = board.king(color)

            if not king_sq:
                continue

            if chess.square_rank(king_sq) != back_rank:
                continue

            # Check if king has escape squares blocked by own pawns
            escape_squares = [
                sq
                for sq in chess.SquareSet(board.attacks(king_sq))
                if not board.piece_at(sq) or board.piece_at(sq).color != color
            ]

            # Check if opponent rook/queen threatens back rank
            for piece_type in [chess.ROOK, chess.QUEEN]:
                for opp_sq in board.pieces(piece_type, opponent):
                    if chess.square_rank(opp_sq) == back_rank:
                        if len(escape_squares) == 0:
                            tactics.append(
                                {
                                    "type": "back_rank",
                                    "description": f"{'White' if color == chess.WHITE else 'Black'} is vulnerable to back-rank checkmate! King trapped on {chess.square_name(king_sq)}",
                                    "squares": [
                                        chess.square_name(king_sq),
                                        chess.square_name(opp_sq),
                                    ],
                                    "severity": "critical",
                                    "forColor": (
                                        "white" if color == chess.WHITE else "black"
                                    ),
                                }
                            )
                            break

        return tactics

    def _detect_discovered_attacks(self, board: chess.Board) -> List[dict]:
        """Detect potential discovered attack opportunities"""
        tactics = []

        for color in [chess.WHITE, chess.BLACK]:
            opponent = not color

            for sq in chess.SQUARES:
                piece = board.piece_at(sq)
                if not piece or piece.color != color:
                    continue
                if piece.piece_type not in [chess.BISHOP, chess.ROOK, chess.QUEEN]:
                    continue

                # Look for friendly pieces blocking the ray
                rays = board.attacks(sq)
                for blocked_sq in chess.SQUARES:
                    blocking = board.piece_at(blocked_sq)
                    if not blocking or blocking.color != color:
                        continue
                    if blocked_sq not in rays:
                        continue

                    # If blocker moves, what does the piece behind attack?
                    for move_sq in chess.SQUARES:
                        if board.is_attacked_by(color, move_sq):
                            target = board.piece_at(move_sq)
                            if (
                                target
                                and target.color == opponent
                                and target.piece_type in [chess.QUEEN, chess.ROOK]
                            ):
                                tactics.append(
                                    {
                                        "type": "discovered_attack",
                                        "description": f"Moving {chess.piece_name(blocking.piece_type)} from {chess.square_name(blocked_sq)} discovers an attack on opponent's {chess.piece_name(target.piece_type)}",
                                        "squares": [
                                            chess.square_name(sq),
                                            chess.square_name(blocked_sq),
                                        ],
                                        "severity": "high",
                                        "forColor": (
                                            "white" if color == chess.WHITE else "black"
                                        ),
                                    }
                                )
                                break

        return tactics[:2]

    def _get_direction(self, from_sq: int, to_sq: int) -> int:
        """Get direction vector from one square to another"""
        rank_diff = chess.square_rank(to_sq) - chess.square_rank(from_sq)
        file_diff = chess.square_file(to_sq) - chess.square_file(from_sq)

        if rank_diff == 0:
            return 1 if file_diff > 0 else -1
        elif file_diff == 0:
            return 8 if rank_diff > 0 else -8
        elif rank_diff == file_diff:
            return 9 if rank_diff > 0 else -9
        elif rank_diff == -file_diff:
            return 7 if rank_diff > 0 else -7
        return 0

    def _is_valid_square(self, sq: int) -> bool:
        return 0 <= sq < 64
