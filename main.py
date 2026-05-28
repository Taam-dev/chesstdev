#!/usr/bin/env python3
"""
Chess Assistant — Suggest best moves using Stockfish.

Usage:
    python main.py                          # Open GUI
    python main.py --fen "FEN_STRING"       # CLI Analysis
    python main.py --fen "..." --top 3      # Top 3 moves
    python main.py --stockfish "path"       # Specify Stockfish path
"""

import argparse
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

from config import Config


def cli_analyze(fen: str, depth: int, top: int):
    """Phân tích qua command line."""
    from engine_manager import EngineManager
    import chess

    try:
        board = chess.Board(fen)
    except ValueError as e:
        print(f"❌ Invalid FEN: {e}")
        sys.exit(1)

    print()
    print("=" * 55)
    print("  ♟ Chess Assistant — CLI")
    print("=" * 55)
    print(f"  FEN:    {fen}")
    print(
        f"  Turn:   {'White' if board.turn else 'Black'} (move {board.fullmove_number})"
    )
    print(f"  Depth:  {depth}")
    print()
    print(board.unicode(borders=True))
    print()

    with EngineManager() as engine:
        if top > 1:
            results = engine.get_top_moves(fen, count=top, depth=depth)
            medals = ["🥇", "🥈", "🥉", "4.", "5."]
            print(f"  Top {len(results)} moves:")
            print()
            for i, r in enumerate(results):
                medal = medals[i] if i < len(medals) else f"{i + 1}."
                pv = " → ".join(r.pv[:6])
                desc_part = f"({r.best_move_desc})" if r.best_move_desc else ""
                print(
                    f"    {medal} {r.best_move_san:8s} {desc_part:<30s} {r.score_display:>8s}  PV: {pv}"
                )
        else:
            result = engine.analyze(fen, depth=depth)
            print(f"  ┌──────────────────────────────────────────────┐")
            print(f"  │  Best Move:   {result.best_move_san:<31s}│")
            if result.best_move_desc:
                print(f"  │  Description: {result.best_move_desc:<31s}│")
            print(f"  │  Eval:        {result.score_display:<31s}│")
            print(f"  │  {result.evaluation_text:<44s}│")
            print(f"  │  Depth:       {result.depth:<31d}│")
            print(f"  │  Time:        {result.thinking_time:<30.2f}s│")
            print(f"  │  UCI:         {result.best_move_uci:<31s}│")
            print(f"  └──────────────────────────────────────────────┘")

            if result.pv:
                pv_str = " → ".join(result.pv)
                print(f"\n  PV: {pv_str}")

    print()


def is_server_running() -> bool:
    """Check if FEN relay server is already running on port 5555."""
    import urllib.request
    try:
        with urllib.request.urlopen("http://127.0.0.1:5555/ping", timeout=0.5) as response:
            return response.read() == b"pong"
    except Exception:
        return False


def start_relay_server():
    """Start fen_relay_server.py in a separate cmd window."""
    import os
    import sys
    import subprocess

    if is_server_running():
        print("✓ FEN Relay Server is already running on port 5555.")
        return

    # Find fen_relay_server.py
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    server_path = os.path.join(base_dir, "fen_relay_server.py")
    if not os.path.exists(server_path):
        print(f"⚠ FEN Relay Server not found at {server_path}")
        return

    try:
        # Determine the python interpreter path
        python_exe = "python"
        venv_python = os.path.join(base_dir, "venv", "Scripts", "python.exe")
        if os.path.exists(venv_python):
            python_exe = venv_python
        elif sys.executable and "python" in os.path.basename(sys.executable).lower():
            python_exe = sys.executable

        # Run in a new command prompt window, keep it open on close using cmd.exe /k
        cmd = f'cmd.exe /k ""{python_exe}" "{server_path}""'
        subprocess.Popen(
            cmd,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        print("✓ Started FEN Relay Server in a new cmd window.")
    except Exception as e:
        print(f"⚠ Failed to start FEN Relay Server: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="♟ Chess Assistant — Suggest moves using Stockfish",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py
  python main.py --fen "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
  python main.py --fen "..." --depth 20 --top 5
  python main.py --stockfish "C:/stockfish/stockfish-windows-x86-64-avx2.exe"
        """,
    )
    parser.add_argument(
        "--fen", type=str, default=None, help="FEN to analyze (CLI mode)"
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=Config.ENGINE_DEPTH,
        help=f"Analysis depth (default: {Config.ENGINE_DEPTH})",
    )
    parser.add_argument(
        "--top", type=int, default=1, help="Number of moves to display (default: 1)"
    )
    parser.add_argument(
        "--stockfish", type=str, default=None, help="Path to Stockfish binary"
    )
    parser.add_argument(
        "--gui", action="store_true", help="Force GUI mode even if --fen is provided"
    )

    args = parser.parse_args()

    # Ghi đè đường dẫn Stockfish
    if args.stockfish:
        Config.STOCKFISH_PATH = args.stockfish

    # Kiểm tra cấu hình
    # CLI mode
    if args.fen and not args.gui:
        problems = Config.validate()
        if problems:
            for p in problems:
                print(f"⚠ {p}")
            print()
            sys.exit(1)
        print(f"✓ Stockfish: {Config.STOCKFISH_PATH}")
        cli_analyze(args.fen, args.depth, args.top)
        return

    # GUI mode
    problems = Config.validate()
    if problems:
        for p in problems:
            print(f"⚠ {p}")
        print()
    else:
        print(f"✓ Stockfish: {Config.STOCKFISH_PATH}")

    # Launch FEN Relay Server automatically
    start_relay_server()

    from overlay_gui import ChessOverlay

    app = ChessOverlay()
    app.run()


if __name__ == "__main__":
    main()
