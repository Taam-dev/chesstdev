"""
UCI Protocol Parser - Raw UCI communication utilities
Supplements python-chess with additional parsing helpers
"""

import re
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class UCIInfo:
    """Parsed info line from Stockfish"""

    depth: int = 0
    seldepth: int = 0
    multipv: int = 1
    score_cp: Optional[int] = None
    score_mate: Optional[int] = None
    nodes: int = 0
    nps: int = 0
    time_ms: int = 0
    pv: list[str] = field(default_factory=list)
    hashfull: int = 0
    tbhits: int = 0
    string: str = ""

    @property
    def has_score(self) -> bool:
        return self.score_cp is not None or self.score_mate is not None

    @property
    def is_mate(self) -> bool:
        return self.score_mate is not None

    @property
    def evaluation_cp(self) -> int:
        """Evaluation in centipawns (approximate for mate scores)"""
        if self.score_mate is not None:
            return 30000 if self.score_mate > 0 else -30000
        return self.score_cp or 0


# ─── Parsers ─────────────────────────────────────────────────────────────────


def parse_info_line(line: str) -> Optional[UCIInfo]:
    """
    Parse a UCI 'info' line from Stockfish output.

    Example:
    info depth 20 seldepth 28 multipv 1 score cp 45 nodes 1234567
         nps 2345678 hashfull 123 tbhits 0 time 526 pv e2e4 e7e5
    """
    if not line.startswith("info"):
        return None

    info = UCIInfo()
    tokens = line.split()
    i = 1

    while i < len(tokens):
        token = tokens[i]

        if token == "depth" and i + 1 < len(tokens):
            info.depth = _safe_int(tokens[i + 1])
            i += 2

        elif token == "seldepth" and i + 1 < len(tokens):
            info.seldepth = _safe_int(tokens[i + 1])
            i += 2

        elif token == "multipv" and i + 1 < len(tokens):
            info.multipv = _safe_int(tokens[i + 1])
            i += 2

        elif token == "score" and i + 1 < len(tokens):
            score_type = tokens[i + 1]
            if score_type == "cp" and i + 2 < len(tokens):
                info.score_cp = _safe_int(tokens[i + 2])
                i += 3
            elif score_type == "mate" and i + 2 < len(tokens):
                info.score_mate = _safe_int(tokens[i + 2])
                i += 3
            else:
                i += 1

        elif token == "nodes" and i + 1 < len(tokens):
            info.nodes = _safe_int(tokens[i + 1])
            i += 2

        elif token == "nps" and i + 1 < len(tokens):
            info.nps = _safe_int(tokens[i + 1])
            i += 2

        elif token == "time" and i + 1 < len(tokens):
            info.time_ms = _safe_int(tokens[i + 1])
            i += 2

        elif token == "hashfull" and i + 1 < len(tokens):
            info.hashfull = _safe_int(tokens[i + 1])
            i += 2

        elif token == "tbhits" and i + 1 < len(tokens):
            info.tbhits = _safe_int(tokens[i + 1])
            i += 2

        elif token == "pv":
            info.pv = tokens[i + 1 :]
            break  # PV is always last

        elif token == "string":
            info.string = " ".join(tokens[i + 1 :])
            break

        else:
            i += 1

    return info if info.depth > 0 else None


def parse_bestmove_line(line: str) -> tuple[str, Optional[str]]:
    """
    Parse 'bestmove e2e4 ponder e7e5'

    Returns:
        (bestmove_uci, ponder_uci or None)
    """
    parts = line.split()
    if len(parts) < 2 or parts[0] != "bestmove":
        return "", None

    bestmove = parts[1] if parts[1] != "(none)" else ""
    ponder = parts[3] if len(parts) >= 4 and parts[2] == "ponder" else None

    return bestmove, ponder


def parse_option_line(line: str) -> Optional[dict]:
    """
    Parse 'option name Threads type spin default 1 min 1 max 512'

    Returns dict with option info or None
    """
    if not line.startswith("option"):
        return None

    pattern = r"option name (.+?) type (\w+)(.*)"
    match = re.match(pattern, line)
    if not match:
        return None

    name = match.group(1).strip()
    opt_type = match.group(2)
    rest = match.group(3)

    option = {"name": name, "type": opt_type}

    # Parse default/min/max/var
    for key in ["default", "min", "max"]:
        m = re.search(rf"\b{key}\s+(\S+)", rest)
        if m:
            option[key] = m.group(1)

    # Parse var options (combo type)
    vars_found = re.findall(r"\bvar\s+(\S+)", rest)
    if vars_found:
        option["vars"] = vars_found

    return option


def format_position_command(fen: str, moves: list[str] = None) -> str:
    """
    Build UCI position command.

    Args:
        fen: Position FEN string
        moves: List of UCI moves to apply after position

    Returns:
        UCI command string
    """
    if fen == "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1":
        cmd = "position startpos"
    else:
        cmd = f"position fen {fen}"

    if moves:
        cmd += " moves " + " ".join(moves)

    return cmd


def format_go_command(
    depth: Optional[int] = None,
    movetime: Optional[int] = None,
    nodes: Optional[int] = None,
    infinite: bool = False,
    searchmoves: Optional[list[str]] = None,
) -> str:
    """
    Build UCI go command.

    Args:
        depth: Search depth
        movetime: Time limit in ms
        nodes: Node limit
        infinite: Search indefinitely
        searchmoves: Restrict search to these moves

    Returns:
        UCI command string
    """
    parts = ["go"]

    if infinite:
        parts.append("infinite")
    elif depth is not None:
        parts.extend(["depth", str(depth)])
    elif movetime is not None:
        parts.extend(["movetime", str(movetime)])
    elif nodes is not None:
        parts.extend(["nodes", str(nodes)])

    if searchmoves:
        parts.extend(["searchmoves"] + searchmoves)

    return " ".join(parts)


# ─── Helpers ─────────────────────────────────────────────────────────────────


def _safe_int(s: str, default: int = 0) -> int:
    """Safely parse integer, returning default on failure"""
    try:
        return int(s)
    except (ValueError, TypeError):
        return default


def centipawns_to_display(cp: int) -> str:
    """Convert centipawns to display string like +1.23 or -0.45"""
    pawns = cp / 100.0
    if pawns >= 0:
        return f"+{pawns:.2f}"
    return f"{pawns:.2f}"


def mate_to_display(mate: int) -> str:
    """Convert mate score to display string like M5 or -M3"""
    if mate > 0:
        return f"M{mate}"
    return f"-M{abs(mate)}"
