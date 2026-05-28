#!/usr/bin/env python3
"""
Chess Assistant — Gợi ý nước đi tốt nhất bằng Stockfish.

Cách dùng:
    python main.py                          # Mở GUI
    python main.py --fen "FEN_STRING"       # Phân tích CLI
    python main.py --fen "..." --top 3      # Top 3 nước
    python main.py --stockfish "path"       # Chỉ định Stockfish
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
        print(f"❌ FEN không hợp lệ: {e}")
        sys.exit(1)

    print()
    print("=" * 55)
    print("  ♟ Chess Assistant — CLI")
    print("=" * 55)
    print(f"  FEN:    {fen}")
    print(
        f"  Lượt:   {'Trắng' if board.turn else 'Đen'} (nước {board.fullmove_number})"
    )
    print(f"  Depth:  {depth}")
    print()
    print(board.unicode(borders=True))
    print()

    with EngineManager() as engine:
        if top > 1:
            results = engine.get_top_moves(fen, count=top, depth=depth)
            medals = ["🥇", "🥈", "🥉", "4.", "5."]
            print(f"  Top {len(results)} nước đi:")
            print()
            for i, r in enumerate(results):
                medal = medals[i] if i < len(medals) else f"{i + 1}."
                pv = " → ".join(r.pv[:6])
                print(
                    f"    {medal} {r.best_move_san:8s}  {r.score_display:>8s}  PV: {pv}"
                )
        else:
            result = engine.analyze(fen, depth=depth)
            print(f"  ┌──────────────────────────────────┐")
            print(f"  │  Best Move:  {result.best_move_san:<20s}│")
            print(f"  │  Eval:       {result.score_display:<20s}│")
            print(f"  │  {result.evaluation_text:<32s}│")
            print(f"  │  Depth:      {result.depth:<20d}│")
            print(f"  │  Time:       {result.thinking_time:<19.2f}s│")
            print(f"  │  UCI:        {result.best_move_uci:<20s}│")
            print(f"  └──────────────────────────────────┘")

            if result.pv:
                pv_str = " → ".join(result.pv)
                print(f"\n  PV: {pv_str}")

    print()


def main():
    parser = argparse.ArgumentParser(
        description="♟ Chess Assistant — Gợi ý nước đi bằng Stockfish",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ:
  python main.py
  python main.py --fen "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
  python main.py --fen "..." --depth 20 --top 5
  python main.py --stockfish "C:/stockfish/stockfish-windows-x86-64-avx2.exe"
        """,
    )
    parser.add_argument(
        "--fen", type=str, default=None, help="FEN để phân tích (chế độ CLI)"
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=Config.ENGINE_DEPTH,
        help=f"Độ sâu phân tích (mặc định: {Config.ENGINE_DEPTH})",
    )
    parser.add_argument(
        "--top", type=int, default=1, help="Số nước đi hiển thị (mặc định: 1)"
    )
    parser.add_argument(
        "--stockfish", type=str, default=None, help="Đường dẫn tới Stockfish"
    )
    parser.add_argument(
        "--gui", action="store_true", help="Bắt buộc mở GUI dù có --fen"
    )

    args = parser.parse_args()

    # Ghi đè đường dẫn Stockfish
    if args.stockfish:
        Config.STOCKFISH_PATH = args.stockfish

    # Kiểm tra cấu hình
    problems = Config.validate()
    if problems:
        for p in problems:
            print(f"⚠ {p}")
        print()
        sys.exit(1)

    print(f"✓ Stockfish: {Config.STOCKFISH_PATH}")

    # CLI mode
    if args.fen and not args.gui:
        cli_analyze(args.fen, args.depth, args.top)
        return

    # GUI mode
    from overlay_gui import ChessOverlay

    app = ChessOverlay()
    app.run()


if __name__ == "__main__":
    main()
