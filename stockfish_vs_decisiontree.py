

import chess
import chess.svg
import random
import subprocess
import base64
import os
import joblib

# paths
SF_PATH         = r"C:\Users\akhil\OneDrive\Desktop\Akhila\Code\.vscode\chess_app\stockfish\stockfish.exe"
TREE_FILE       = "adams_tree.pkl"
LEAF_MOVES_FILE = "adams_leaf_moves.pkl"

# LOAD THE SAVED MODEL

_tree       = None
_leaf_moves = None

if os.path.exists(TREE_FILE) and os.path.exists(LEAF_MOVES_FILE):
    _tree       = joblib.load(TREE_FILE)
    _leaf_moves = joblib.load(LEAF_MOVES_FILE)
    print("Adams decision tree loaded successfully.")
    print(f"  Tree leaves  : {_tree.get_n_leaves()}")
    print(f"  Buckets      : {len(_leaf_moves)}")
else:
    print("WARNING: model files not found.")
    print("  Run train_tree.py first to create them.")
    print("  Until then White will play randomly.")


# FEATURE EXTRACTION
def get_features(board, castled):
    """

    Turn a board position into 3 numbers the tree can understand.
     
    """
    move_number = board.fullmove_number

    can_capture = 0
    for m in board.legal_moves:
        if board.is_capture(m):
            can_capture = 1
            break

    return [move_number, can_capture, int(castled)]


# DECISION TREE MOVE
def get_dt_move(board, castled):
    """
    Use the Adams decision tree to pick a move.
    """
    if _tree is None or _leaf_moves is None:
        return get_random_move(board)

    features        = get_features(board, castled)
    # feature is gonna be like the move is gonna be one and the second is gonna be the move
    # _leaf_moves  = {6:["e2e4","G1F3",.....]}
    # bucket - 7 or something else 
    bucket          = int(_tree.apply([features])[0])
    # Get the possible moves based on the position
    candidate_moves = _leaf_moves.get(bucket, [])
    for uci_move in candidate_moves:
        try: 
            move = chess.Move.from_uci(uci_move)
            if move in board.legal_moves:
                print(move)
                return move
        except Exception:
            continue

    return get_random_move(board)


# STOCKFISH
def find_stockfish():
    if not os.path.exists(SF_PATH):
        return None
    try:
        proc = subprocess.Popen(
            SF_PATH,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        proc.stdin.write("uci\nquit\n")
        proc.stdin.flush()
        proc.wait(timeout=5)
        return SF_PATH
    except Exception:
        return None


def get_stockfish_move(board, skill_level=1, movetime_ms=100):
    try:
        proc = subprocess.Popen(
            SF_PATH,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        commands = (
            f"setoption name Skill Level value {skill_level}\n"
            f"position fen {board.fen()}\n"
            f"go movetime {movetime_ms}\n"
        )
        proc.stdin.write(commands)
        proc.stdin.flush()

        best_move = None
        while True:
            line = proc.stdout.readline().strip()
            if line.startswith("bestmove"):
                parts = line.split()
                if len(parts) >= 2:
                    best_move = parts[1]
                break

        proc.stdin.write("quit\n")
        proc.stdin.flush()
        proc.wait(timeout=5)

        if best_move and best_move != "(none)":
            return chess.Move.from_uci(best_move)
        return get_random_move(board)

    except Exception:
        return get_random_move(board)


def get_random_move(board):
    return random.choice(list(board.legal_moves))


# MAIN GAME LOOP
# White = Adams decision tree
# Black = Stockfish
def do_next_move(board, move_history, stats, sf_path,
                 white_castled, skill_level=1):
   
    if board.is_game_over():
        return board, move_history, stats, True, white_castled

    if board.turn == chess.WHITE:

        # Adams decision tree plays White
        move   = get_dt_move(board, white_castled)
        player = "adams_dt"

        # update castled flag if White just castled
        if board.is_castling(move):
            white_castled = True

    else:

        # Stockfish plays Black
        if sf_path:
            move   = get_stockfish_move(board, skill_level)
            player = "stockfish"
        else:
            move   = get_random_move(board)
            player = "random"

    san = board.san(move)
    board.push(move)
    move_history.append((move.uci(), player, san, board.fullmove_number))

    game_over = False
    if board.is_game_over():
        game_over = True
        result    = board.result()
        stats["games"] += 1
        if result == "1-0":
            stats["dt_wins"] += 1
        elif result == "0-1":
            stats["stockfish_wins"] += 1
        else:
            stats["draws"] += 1

    return board, move_history, stats, game_over, white_castled


# HELPERS

def new_game():
    return {
        "board":         chess.Board(),
        "move_history":  [],
        "last_move":     None,
        "game_over":     False,
        "white_castled": False,   # decision tree needs this
    }


def default_stats():
    return {
        "dt_wins":        0,
        "stockfish_wins": 0,
        "draws":          0,
        "games":          0,
    }


def board_to_svg(board, last_move=None, size=420):
    arrows = []
    if last_move:
        arrows = [chess.svg.Arrow(
            last_move.from_square,
            last_move.to_square,
            color="#185FA5"
        )]
    svg_str = chess.svg.board(
        board,
        size=size,
        lastmove=last_move,
        arrows=arrows,
        colors={
            "square light":          "#F0EDE6",
            "square dark":           "#B08A6A",
            "square light lastmove": "#CDD88A",
            "square dark lastmove":  "#AABA5A",
        }
    )
    b64 = base64.b64encode(svg_str.encode()).decode()
    return f"data:image/svg+xml;base64,{b64}"


def result_label(result_str):
    if result_str == "1-0":
        return "White (Adams DT) wins"
    elif result_str == "0-1":
        return "Black (Stockfish) wins"
    return "Draw"


def turn_label(board):
    if board.turn == chess.WHITE:
        return f"White (Adams DT) — Move {board.fullmove_number}"
    return f"Black (Stockfish) — Move {board.fullmove_number}" 