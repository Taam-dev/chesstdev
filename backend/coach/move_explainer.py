"""
Move Explainer - Generates human-language explanations for chess moves.
This is the "coaching" brain of ChessCoach Local.
"""

import logging
import chess
import chess.pgn
from typing import Optional

logger = logging.getLogger(__name__)


class MoveExplainer:
    """
    Generates comprehensive human-language explanations for chess moves.

    The explanation covers:
    - Tactical purpose (what the move attacks/defends)
    - Strategic ideas (long-term plan)
    - Positional impact (pawn structure, piece activity)
    - Threats created
    - Consequences if ignored
    """

    # Piece names for human-readable output
    PIECE_NAMES = {
        chess.PAWN: "pawn",
        chess.KNIGHT: "knight",
        chess.BISHOP: "bishop",
        chess.ROOK: "rook",
        chess.QUEEN: "queen",
        chess.KING: "king",
    }

    PIECE_VALUES = {
        chess.PAWN: 1,
        chess.KNIGHT: 3,
        chess.BISHOP: 3,
        chess.ROOK: 5,
        chess.QUEEN: 9,
        chess.KING: 100,
    }

    def __init__(self):
        self.tactics_detector = None  # Lazy import to avoid circular deps

    async def explain(self, fen: str, move_san: str, analysis: dict) -> dict:
        """
        Generate comprehensive move explanation.

        Args:
            fen: Position BEFORE the move
            move_san: Move in Standard Algebraic Notation (e.g., "Nf5")
            analysis: Engine analysis data

        Returns:
            dict with explanation components
        """
        try:
            board = chess.Board(fen)
        except ValueError:
            return self._error_explanation("Invalid position")

        # Parse move
        try:
            move = board.parse_san(move_san)
        except ValueError:
            # Try UCI notation
            try:
                move = chess.Move.from_uci(move_san)
            except ValueError:
                return self._error_explanation(f"Cannot parse move: {move_san}")

        # Gather context
        context = self._analyze_move_context(board, move, analysis)

        # Generate explanation components
        tactical = self._explain_tactical(board, move, context)
        strategic = self._explain_strategic(board, move, context)
        positional = self._explain_positional(board, move, context)
        threats = self._explain_threats(board, move, context)
        weaknesses = self._explain_weaknesses(board, move, context)
        risks = self._explain_risks(board, move, context)
        summary = self._generate_summary(board, move, context, analysis)

        # Classify move quality
        quality = self._classify_quality(analysis)

        # Detect tactics
        tactics = self._detect_move_tactics(board, move, context)

        return {
            "move": move.uci(),
            "san": move_san,
            "quality": quality,
            "tactical": tactical,
            "strategic": strategic,
            "positional": positional,
            "threats": threats,
            "weaknesses": weaknesses,
            "risks": risks,
            "summary": summary,
            "tactics": tactics,
            "context": {
                "isCapture": context.get("is_capture", False),
                "isCheck": context.get("gives_check", False),
                "isCastling": context.get("is_castling", False),
                "materialBalance": context.get("material_balance", 0),
            },
        }

    def _analyze_move_context(
        self, board: chess.Board, move: chess.Move, analysis: dict
    ) -> dict:
        """Gather all relevant information about the move"""
        ctx = {}

        piece = board.piece_at(move.from_square)
        ctx["piece"] = piece
        ctx["piece_type"] = piece.piece_type if piece else None
        ctx["piece_name"] = (
            self.PIECE_NAMES.get(piece.piece_type, "piece") if piece else "piece"
        )
        ctx["piece_color"] = piece.color if piece else chess.WHITE
        ctx["from_square"] = chess.square_name(move.from_square)
        ctx["to_square"] = chess.square_name(move.to_square)

        # Capture info
        captured = board.piece_at(move.to_square)
        ctx["is_capture"] = captured is not None
        ctx["captured_piece"] = captured
        ctx["captured_name"] = (
            self.PIECE_NAMES.get(captured.piece_type, "piece") if captured else None
        )

        # Special moves
        ctx["is_castling"] = board.is_castling(move)
        ctx["is_en_passant"] = board.is_en_passant(move)
        ctx["is_promotion"] = bool(move.promotion)

        # After move analysis
        board_after = board.copy()
        board_after.push(move)

        ctx["gives_check"] = board_after.is_check()
        ctx["gives_checkmate"] = board_after.is_checkmate()
        ctx["is_stalemate"] = board_after.is_stalemate()

        # Material balance
        ctx["material_balance"] = self._calculate_material_balance(board)
        ctx["material_after"] = self._calculate_material_balance(board_after)
        ctx["material_gain"] = ctx["material_after"] - ctx["material_balance"]

        # Piece activity
        ctx["piece_mobility_before"] = len(list(board.attacks(move.from_square)))
        ctx["piece_mobility_after"] = len(list(board_after.attacks(move.to_square)))

        # King safety
        our_king = board.king(piece.color if piece else chess.WHITE)
        ctx["our_king_square"] = chess.square_name(our_king) if our_king else "unknown"

        # Attacks
        ctx["attacks_after"] = list(board_after.attacks(move.to_square))
        ctx["attacked_pieces"] = [
            board_after.piece_at(sq)
            for sq in ctx["attacks_after"]
            if board_after.piece_at(sq)
            and board_after.piece_at(sq).color
            != (piece.color if piece else chess.WHITE)
        ]

        # Pawn structure
        if piece and piece.piece_type == chess.PAWN:
            ctx["creates_passed_pawn"] = self._is_passed_pawn(
                board_after, move.to_square
            )
            ctx["is_pawn_advance"] = True
        else:
            ctx["creates_passed_pawn"] = False
            ctx["is_pawn_advance"] = False

        # Center control
        center_squares = [chess.E4, chess.D4, chess.E5, chess.D5]
        ctx["goes_to_center"] = move.to_square in center_squares
        ctx["controls_center"] = any(
            sq in ctx["attacks_after"] for sq in center_squares
        )

        # Open files
        ctx["creates_open_file"] = (
            ctx["is_capture"]
            and piece
            and piece.piece_type == chess.PAWN
            and captured
            and captured.piece_type == chess.PAWN
        )

        # Analysis data
        ctx["evaluation"] = analysis.get("evaluation", 0)
        ctx["best_move"] = analysis.get("bestMove", "")
        ctx["is_best_move"] = move.uci() == ctx["best_move"]

        return ctx

    def _explain_tactical(self, board: chess.Board, move: chess.Move, ctx: dict) -> str:
        """Explain the immediate tactical purpose of the move"""
        parts = []

        piece_name = ctx["piece_name"].capitalize()
        to_sq = ctx["to_square"]

        if ctx.get("gives_checkmate"):
            return f"{piece_name} to {to_sq} delivers checkmate! The game is over."

        if ctx.get("gives_check"):
            parts.append(f"{piece_name} to {to_sq} puts the king in check")

        if ctx.get("is_capture"):
            captured = ctx["captured_name"]
            gain = ctx["material_gain"]
            if gain > 0:
                parts.append(
                    f"Captures the {captured} on {to_sq}, winning {gain} pawn(s) of material"
                )
            elif gain == 0:
                parts.append(
                    f"Exchanges {piece_name.lower()} for {captured} on {to_sq} (equal trade)"
                )
            else:
                parts.append(
                    f"Recaptures on {to_sq} (sacrifice of {abs(gain)} pawn value)"
                )

        # Multiple attacks (fork potential)
        attacked = ctx.get("attacked_pieces", [])
        if len(attacked) >= 2:
            attacked_names = [
                self.PIECE_NAMES.get(p.piece_type, "piece") for p in attacked[:3]
            ]
            parts.append(
                f"Attacks {len(attacked)} pieces simultaneously: {', '.join(attacked_names)} "
                f"— creating a {'fork' if ctx['piece_name'] == 'knight' else 'double attack'}"
            )
        elif len(attacked) == 1:
            target = self.PIECE_NAMES.get(attacked[0].piece_type, "piece")
            parts.append(f"Threatens the {target}")

        if ctx.get("is_en_passant"):
            parts.append(
                "En passant capture — removes the pawn that just advanced two squares"
            )

        if ctx.get("is_promotion"):
            parts.append(
                f"Pawn promotes — gains a queen, dramatically increasing material advantage"
            )

        if not parts:
            if ctx["piece_mobility_after"] > ctx["piece_mobility_before"]:
                parts.append(
                    f"Improves {piece_name.lower()} activity from {ctx['piece_mobility_before']} "
                    f"to {ctx['piece_mobility_after']} available squares"
                )
            else:
                parts.append(f"Repositions the {piece_name.lower()} to {to_sq}")

        return ". ".join(parts) + "."

    def _explain_strategic(
        self, board: chess.Board, move: chess.Move, ctx: dict
    ) -> str:
        """Explain the long-term strategic ideas"""
        parts = []

        piece_name = ctx["piece_name"]
        to_sq = ctx["to_square"]

        if ctx.get("is_castling"):
            return (
                "Castling brings the king to safety behind the pawns while "
                "connecting the rooks and preparing them for active play along open files."
            )

        if ctx.get("controls_center"):
            parts.append(
                f"{piece_name.capitalize()} on {to_sq} controls central squares, "
                "increasing influence over the most important area of the board"
            )

        if ctx.get("goes_to_center"):
            parts.append(
                f"Centralized {piece_name} on {to_sq} radiates power across the board "
                "and limits opponent's options"
            )

        if piece_name == "rook":
            file_letter = to_sq[0]
            # Check if file is semi-open or open
            pawns_on_file = [
                sq
                for sq in chess.BB_FILES[ord(file_letter) - ord("a")]
                if board.piece_type_at(sq) == chess.PAWN
            ]
            if not pawns_on_file:
                parts.append(
                    f"Rook seizes the open {file_letter.upper()}-file, creating dangerous "
                    "pressure against opponent's position"
                )
            elif len(pawns_on_file) == 1:
                parts.append(
                    f"Rook occupies semi-open {file_letter.upper()}-file, "
                    "preparing to pressure opponent's pawns"
                )

        if piece_name == "knight":
            rank = int(to_sq[1])
            # Knights on 5th/6th rank are typically strong outposts
            moving_color = ctx["piece_color"]
            is_advanced = (rank >= 5 and moving_color == chess.WHITE) or (
                rank <= 4 and moving_color == chess.BLACK
            )
            if is_advanced:
                parts.append(
                    f"Knight establishes an advanced outpost on {to_sq}, "
                    "a powerful centralized position difficult for opponent to challenge"
                )

        if ctx.get("creates_passed_pawn"):
            parts.append(
                "Creates a passed pawn — a pawn with no opponent pawns blocking its path "
                "to promotion, which becomes a long-term winning advantage"
            )

        if not parts:
            parts.append(
                f"Improves piece coordination and prepares for the next phase of the game"
            )

        return ". ".join(parts) + "."

    def _explain_positional(
        self, board: chess.Board, move: chess.Move, ctx: dict
    ) -> str:
        """Explain positional impact"""
        parts = []

        piece_name = ctx["piece_name"]
        to_sq = ctx["to_square"]
        from_sq = ctx["from_square"]

        if ctx.get("creates_open_file"):
            parts.append(
                "Exchange opens a file, giving rooks access to the seventh rank "
                "and increased pressure on the position"
            )

        # King safety
        if ctx.get("gives_check"):
            parts.append("King is forced to move, potentially losing castling rights")

        # Piece development
        board_copy = board.copy()
        if not ctx.get("is_capture"):
            from_rank = int(from_sq[1])
            starting_ranks = {chess.WHITE: [1, 2], chess.BLACK: [7, 8]}
            color = ctx["piece_color"]
            if from_rank in starting_ranks.get(color, []):
                parts.append(
                    f"Develops the {piece_name} from its starting square, "
                    "contributing to piece activity"
                )

        # Pawn structure
        if piece_name == "pawn":
            if ctx.get("is_capture"):
                parts.append(
                    "Pawn structure changes — creates connected or isolated pawns "
                    "that will affect endgame prospects"
                )

        # Piece coordination
        parts.append(
            f"{'Increases' if ctx['piece_mobility_after'] > ctx['piece_mobility_before'] else 'Maintains'} "
            f"piece coordination with {ctx['piece_mobility_after']} available moves"
        )

        return ". ".join(parts) + "."

    def _explain_threats(self, board: chess.Board, move: chess.Move, ctx: dict) -> str:
        """Explain threats created by this move"""
        parts = []

        board_after = board.copy()
        board_after.push(move)

        attacked_pieces = ctx.get("attacked_pieces", [])

        if ctx.get("gives_checkmate"):
            return "This move ends the game immediately with checkmate."

        if ctx.get("gives_check"):
            parts.append("Opponent must respond to check immediately")

        if len(attacked_pieces) >= 2:
            names = [
                self.PIECE_NAMES.get(p.piece_type, "piece") for p in attacked_pieces[:3]
            ]
            values = [
                self.PIECE_VALUES.get(p.piece_type, 0) for p in attacked_pieces[:3]
            ]
            most_valuable = max(zip(names, values), key=lambda x: x[1])
            parts.append(
                f"Creates a fork attacking {', '.join(names)} simultaneously. "
                f"Opponent can only save one — the {most_valuable[0]} is most at risk"
            )
        elif len(attacked_pieces) == 1:
            target = self.PIECE_NAMES.get(attacked_pieces[0].piece_type, "piece")
            target_value = self.PIECE_VALUES.get(attacked_pieces[0].piece_type, 0)
            our_value = (
                self.PIECE_VALUES.get(ctx["piece_type"], 0) if ctx["piece_type"] else 0
            )

            if target_value > our_value:
                parts.append(
                    f"Threatens to win the {target} (worth {target_value} pawns) "
                    f"with our {ctx['piece_name']} (worth {our_value} pawns) — "
                    "a favorable trade for us"
                )
            else:
                parts.append(f"Threatens the {target}")

        # Check for back-rank threats
        if board_after.turn == chess.BLACK:  # Just moved white
            if chess.E8 in ctx.get("attacks_after", []) or chess.D8 in ctx.get(
                "attacks_after", []
            ):
                parts.append("Threatens back-rank checkmate")

        if not parts:
            parts.append(
                "Prepares future tactical possibilities while maintaining positional pressure"
            )

        return ". ".join(parts) + "."

    def _explain_weaknesses(
        self, board: chess.Board, move: chess.Move, ctx: dict
    ) -> str:
        """Explain weaknesses this move exploits"""
        board_after = board.copy()
        board_after.push(move)
        turn = board.turn  # Color that just moved

        weaknesses = []

        # Check for undefended pieces after move
        opponent_color = not turn
        for sq in chess.SQUARES:
            piece = board_after.piece_at(sq)
            if piece and piece.color == opponent_color:
                if not board_after.is_attacked_by(opponent_color, sq):
                    if board_after.is_attacked_by(turn, sq):
                        piece_name = self.PIECE_NAMES.get(piece.piece_type, "piece")
                        weaknesses.append(
                            f"Exploits the undefended {piece_name} on {chess.square_name(sq)}"
                        )

        # King exposure
        opp_king = board_after.king(opponent_color)
        if opp_king:
            attackers = len(list(board_after.attackers(turn, opp_king)))
            if attackers > 0:
                weaknesses.append(
                    f"Takes advantage of king exposure — "
                    f"{attackers} piece{'s' if attackers > 1 else ''} "
                    f"threatening the king"
                )

        # Weak square exploitation
        to_sq = move.to_square
        if not board_after.is_attacked_by(opponent_color, to_sq):
            weaknesses.append(
                f"Occupies the weak square {chess.square_name(to_sq)} "
                "which cannot be easily challenged by opponent"
            )

        if not weaknesses:
            weaknesses.append(
                "Maintains pressure while avoiding immediate weaknesses in our position"
            )

        return ". ".join(weaknesses) + "."

    def _explain_risks(self, board: chess.Board, move: chess.Move, ctx: dict) -> str:
        """Explain what happens if this move/threat is ignored"""
        parts = []

        if ctx.get("gives_checkmate"):
            return "This IS checkmate — the game is over, opponent has no choice."

        if ctx.get("gives_check"):
            parts.append(
                "If the check is not dealt with immediately, checkmate may follow. "
                "Opponent MUST respond to check on this move"
            )

        attacked = ctx.get("attacked_pieces", [])
        if attacked:
            most_valuable = max(
                attacked, key=lambda p: self.PIECE_VALUES.get(p.piece_type, 0)
            )
            value = self.PIECE_VALUES.get(most_valuable.piece_type, 0)
            name = self.PIECE_NAMES.get(most_valuable.piece_type, "piece")

            if value >= 5:
                parts.append(
                    f"If opponent ignores this threat, they lose their {name} "
                    f"(worth {value} pawns) — a significant material advantage"
                )
            elif value >= 3:
                parts.append(
                    f"Ignoring this costs a {name} — opponent falls behind in material"
                )
            else:
                parts.append(
                    f"Ignoring this move allows us to capture the {name} freely"
                )

        if len(attacked) >= 2:
            parts.append(
                "With two pieces attacked, opponent cannot save both. "
                "They must choose which piece to sacrifice"
            )

        if not parts:
            eval_advantage = ctx.get("evaluation", 0)
            if abs(eval_advantage) > 100:
                who = "White" if eval_advantage > 0 else "Black"
                parts.append(
                    f"Ignoring this move allows {who}'s advantage to grow further. "
                    "The position becomes increasingly difficult to defend"
                )
            else:
                parts.append(
                    "Even if not immediately critical, ignoring this move "
                    "concedes positional advantage that compounds over time"
                )

        return ". ".join(parts) + "."

    def _generate_summary(
        self, board: chess.Board, move: chess.Move, ctx: dict, analysis: dict
    ) -> str:
        """Generate a brief, compelling move summary"""
        piece = ctx["piece_name"].capitalize()
        to_sq = ctx["to_square"]
        quality_label = self._classify_quality(analysis).get("label", "good")

        if ctx.get("gives_checkmate"):
            return (
                f"{piece} to {to_sq} — Checkmate! A decisive combination ends the game."
            )

        if ctx.get("gives_check"):
            if len(ctx.get("attacked_pieces", [])) > 0:
                return (
                    f"{piece} to {to_sq} — Checks the king while simultaneously "
                    f"attacking other pieces. A powerful dual threat."
                )
            return (
                f"{piece} to {to_sq} — Puts pressure on the king, forcing a response."
            )

        if len(ctx.get("attacked_pieces", [])) >= 2:
            return (
                f"{piece} to {to_sq} — Creates a deadly fork! "
                f"Attacks multiple pieces simultaneously, winning material."
            )

        if ctx.get("is_capture") and ctx.get("material_gain", 0) > 0:
            gain = ctx["material_gain"]
            captured = ctx["captured_name"]
            return (
                f"{piece} captures {captured} on {to_sq} — "
                f"Wins {gain} pawn{'s' if gain != 1 else ''} of material advantage."
            )

        if ctx.get("controls_center") or ctx.get("goes_to_center"):
            return (
                f"{piece} to {to_sq} — Seizes central control. "
                "A strong positional move that increases piece activity."
            )

        if ctx.get("is_castling"):
            return "Castling — King safety achieved while activating the rook."

        return (
            f"{piece} to {to_sq} — "
            f"{'An excellent move that improves the position significantly.' if quality_label in ['brilliant', 'great', 'best'] else 'Solid move maintaining good position.'}"
        )

    def _classify_quality(self, analysis: dict) -> dict:
        """Classify move quality based on evaluation difference"""
        eval_diff = analysis.get("eval_diff", 0)  # Set by move classifier
        is_best = analysis.get("is_best_move", False)

        if eval_diff == 0 and is_best:
            label = "best"
        elif eval_diff >= 0:
            label = "good"
        elif eval_diff > -20:
            label = "good"
        elif eval_diff > -50:
            label = "inaccuracy"
        elif eval_diff > -150:
            label = "mistake"
        else:
            label = "blunder"

        symbols = {
            "brilliant": "✨",
            "great": "!!",
            "best": "!",
            "good": "✓",
            "inaccuracy": "⊙",
            "mistake": "?",
            "blunder": "??",
            "miss": "✗",
        }

        colors = {
            "brilliant": "#1bada6",
            "great": "#5c8bb0",
            "best": "#94c23c",
            "good": "#94c23c",
            "inaccuracy": "#f6b740",
            "mistake": "#e07d13",
            "blunder": "#ca3431",
            "miss": "#ca3431",
        }

        return {
            "label": label,
            "symbol": symbols.get(label, "?"),
            "color": colors.get(label, "#888"),
            "scoreDiff": eval_diff,
            "description": self._quality_description(label),
        }

    def _quality_description(self, label: str) -> str:
        descriptions = {
            "brilliant": "A computer-level move that finds a hidden resource",
            "great": "An excellent move that significantly improves the position",
            "best": "The top engine recommendation in this position",
            "good": "A solid move that maintains or improves your position",
            "inaccuracy": "A slightly suboptimal move — a better option was available",
            "mistake": "A significant error that worsens your position",
            "blunder": "A game-changing error — position becomes much worse",
            "miss": "Missed a winning opportunity",
        }
        return descriptions.get(label, "")

    def _detect_move_tactics(
        self, board: chess.Board, move: chess.Move, ctx: dict
    ) -> list:
        """Detect tactical patterns in this move"""
        tactics = []

        attacked = ctx.get("attacked_pieces", [])

        # Fork detection
        if len(attacked) >= 2:
            tactics.append(
                {
                    "type": "fork",
                    "description": f"{ctx['piece_name'].capitalize()} forks {len(attacked)} pieces",
                    "squares": [
                        chess.square_name(p.square if hasattr(p, "square") else 0)
                        for p in attacked[:2]
                    ],
                    "severity": (
                        "high"
                        if any(
                            self.PIECE_VALUES.get(p.piece_type, 0) >= 5
                            for p in attacked
                        )
                        else "medium"
                    ),
                }
            )

        # Check-related
        if ctx.get("gives_check"):
            tactics.append(
                {
                    "type": (
                        "discovered_check" if not ctx.get("is_capture") else "check"
                    ),
                    "description": "Gives check to the opponent's king",
                    "squares": [ctx["to_square"]],
                    "severity": "high",
                }
            )

        # Capture of hanging piece
        if ctx.get("is_capture") and ctx.get("material_gain", 0) > 0:
            tactics.append(
                {
                    "type": "hanging_piece",
                    "description": f"Captures undefended {ctx['captured_name']}",
                    "squares": [ctx["to_square"]],
                    "severity": "medium",
                }
            )

        # Passed pawn
        if ctx.get("creates_passed_pawn"):
            tactics.append(
                {
                    "type": "passed_pawn",
                    "description": "Creates a passed pawn with promotion potential",
                    "squares": [ctx["to_square"]],
                    "severity": "medium",
                }
            )

        return tactics

    def _calculate_material_balance(self, board: chess.Board) -> int:
        """Calculate material balance from White's perspective"""
        total = 0
        for piece_type, value in self.PIECE_VALUES.items():
            if piece_type == chess.KING:
                continue
            white_count = len(board.pieces(piece_type, chess.WHITE))
            black_count = len(board.pieces(piece_type, chess.BLACK))
            total += (white_count - black_count) * value
        return total

    def _is_passed_pawn(self, board: chess.Board, square: int) -> bool:
        """Check if a pawn on square is passed"""
        piece = board.piece_at(square)
        if not piece or piece.piece_type != chess.PAWN:
            return False

        color = piece.color
        file_idx = chess.square_file(square)
        rank_idx = chess.square_rank(square)

        opponent_pawns = board.pieces(chess.PAWN, not color)

        for opp_sq in opponent_pawns:
            opp_file = chess.square_file(opp_sq)
            opp_rank = chess.square_rank(opp_sq)

            if abs(opp_file - file_idx) <= 1:
                if color == chess.WHITE and opp_rank > rank_idx:
                    return False
                elif color == chess.BLACK and opp_rank < rank_idx:
                    return False

        return True

    def _error_explanation(self, message: str) -> dict:
        return {
            "move": "",
            "san": "",
            "quality": {
                "label": "good",
                "symbol": "?",
                "color": "#888",
                "scoreDiff": 0,
                "description": "",
            },
            "tactical": message,
            "strategic": "",
            "positional": "",
            "threats": "",
            "weaknesses": "",
            "risks": "",
            "summary": message,
            "tactics": [],
        }
