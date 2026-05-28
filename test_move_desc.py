import sys
import chess
from engine_manager import EngineManager

def test():
    tests = [
        # Normal move
        ("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", "e2e4", "e4", "Pawn to e4"),
        # Capture (pawn takes pawn)
        ("rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2", "e4d5", "exd5", "Pawn takes pawn on d5"),
        # Capture (bishop takes pawn with check)
        ("rnbqk2r/pppp1ppp/7n/4p3/1bB1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4", "c4f7", "Bxf7+", "Bishop takes pawn on f7 (check)"),
        # Kingside Castle
        ("rnbqk2r/pppp1ppp/5n2/4p3/1bB1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4", "e1g1", "O-O", "Kingside castle"),
        # Queenside Castle
        ("r3kbnr/ppp1pppp/2nq4/3p4/3P4/2NQ4/PPP1PPPP/R3KBNR w KQkq - 4 5", "e1c1", "O-O-O", "Queenside castle"),
        # Promotion
        ("8/4P3/8/8/8/8/8/k6K w - - 0 1", "e7e8q", "e8=Q", "Pawn to e8, promoting to Queen"),
        # Checkmate
        ("rnbqkbnr/ppppp2p/5p2/6p1/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2", "d1h5", "Qh5#", "Queen to h5 (checkmate)")
    ]
    
    manager = EngineManager(stockfish_path="dummy")
    
    success = True
    for fen, uci, san, expected_desc in tests:
        board = chess.Board(fen)
        move = chess.Move.from_uci(uci)
        desc = manager._get_move_description(board, move)
        print(f"Position FEN: {fen}")
        print(f"Move: {san} ({uci})")
        print(f"Calculated Description: {desc}")
        print(f"Expected Description:   {expected_desc}")
        
        # We can do exact or partial matches
        if desc.lower().strip() != expected_desc.lower().strip():
            print("MATCH FAIL [X]")
            success = False
        else:
            print("MATCH OK [OK]")
        print("-" * 50)
        
    if success:
        print("ALL TESTS PASSED SUCCESSFULLY! OK")
        sys.exit(0)
    else:
        print("SOME TESTS FAILED! FAIL")
        sys.exit(1)

if __name__ == "__main__":
    test()
