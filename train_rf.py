

import chess
import chess.pgn
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
import numpy as np

PGN_FILE     = "adams.pgn"
PLAYER_NAME  = "Adams, Michael"
N_TREES      = 100  
# piece values for material_diff feature
PIECE_VALUES = {
    chess.PAWN:   1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK:   5,
    chess.QUEEN:  9,
}

# FEATURE EXTRACTION — now 5 features
# same concept as decision tree but more features
# Random Forest handles more features much better

def get_features(board, castled, adams_colour):
    """
    Turn a board position into 5 numbers.

    1. move_number   — opening / middlegame / endgame
    2. can_capture   — is there an enemy piece to take? 1=yes 0=no
    3. castled       — has Adams already castled?       1=yes 0=no
    4. material_diff — Adams piece value minus opponent piece value
    5. in_check      — is Adams currently in check?    1=yes 0=no
    """

    # feature 1 - move number
    move_number = board.fullmove_number

    # feature 2 - can capture
    can_capture = 0
    for m in board.legal_moves:
        if board.is_capture(m):
            can_capture = 1
            break

    # feature 3 - castled (passed in from outside)

    # feature 4 - material difference
    # count Adams' total piece value
    my_total = 0
    for pt, v in PIECE_VALUES.items():
        count     = len(board.pieces(pt, adams_colour))
        my_total  = my_total + (count * v)

    # count opponent's total piece value
    opp_total = 0
    for pt, v in PIECE_VALUES.items():
        count     = len(board.pieces(pt, not adams_colour))
        opp_total = opp_total + (count * v)

    # subtract - positive means Adams is winning material
    #           - negative means Adams is losing material
    #           - zero means equal
    material_diff = my_total - opp_total

    # feature 5 - in check
    in_check = int(board.is_check())

    return [move_number, can_capture, int(castled), material_diff, in_check]


def read_pgn(pgn_file, player_name):
  
    rows = []

    with open(pgn_file, encoding="utf-8", errors="ignore") as f:
        while True:
            game = chess.pgn.read_game(f)
            if game is None:
                break

            white = game.headers.get("White", "")
            black = game.headers.get("Black", "")

            if player_name in white:     
                
                adams_colour = chess.WHITE
            elif player_name in black:
                adams_colour = chess.BLACK
            else:
                continue

            board   = game.board()
            castled = False

            for move in game.mainline_moves():

                if board.turn == adams_colour:
                    features = get_features(board, castled, adams_colour)
                    rows.append((features, move.uci()))

                    if board.is_castling(move):
                        castled = True

                board.push(move)

    return rows


# TOP-K CHECK using predict_proba

def check_topk(label, X_data, y_data, forest):
    """
    For every position use predict_proba to get a ranked list of moves.
    Check if Adams' actual move is in the top 1, 3, or 5.

    With Random Forest predict_proba averages probabilities across
    all 100 trees — much more meaningful than a single tree.
    """
    classes = forest.classes_
    top1 = top3 = top5 = 0
    total = len(X_data)

    for i in range(total):
        actual_move = y_data[i]

        # get probability of every move — averaged across all 100 trees
        proba = forest.predict_proba([X_data[i]])[0]

        # sort by probability highest first - keep only non-zero
        ranked_moves = [
            move for move, prob in
            sorted(zip(classes, proba),
                   key=lambda x: x[1], reverse=True)
            if prob > 0
        ]

        if actual_move in ranked_moves[:1]: top1 += 1
        if actual_move in ranked_moves[:3]: top3 += 1
        if actual_move in ranked_moves[:5]: top5 += 1

    print(f"\n  {label} ({total} positions):")
    print(f"    top-1 : {top1}/{total}  ({top1/total*100:.1f}%)")
    print(f"    top-3 : {top3}/{total}  ({top3/total*100:.1f}%)")
    print(f"    top-5 : {top5}/{total}  ({top5/total*100:.1f}%)")

    return top1, top3, top5, total


# MAIN
FEATURE_NAMES = [
    "move_number", "can_capture", "castled",
    "material_diff", "in_check"
]

#  read PGN 
print(f"Reading {PGN_FILE} ...")
rows = read_pgn(PGN_FILE, PLAYER_NAME)
print(f"  Positions found where Adams moved : {len(rows)}")

if not rows:
    print("ERROR: no moves found.")
    exit()

#  build X and y 
X = [r[0] for r in rows]
y = [r[1] for r in rows]

print(f"  Unique moves Adams played         : {len(set(y))}")

# split 80% train  20% test
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)
print(f"  Training positions                : {len(X_train)}")
print(f"  Test positions                    : {len(X_test)}")

# train the Random Forest 
# n_estimators = how many trees in the forest
# each tree is trained on a random sample of X_train (bagging)
# each tree uses a random subset of features at each split
print(f"\nTraining Random Forest ({N_TREES} trees) ...")
forest = RandomForestClassifier(
    n_estimators = N_TREES,
    random_state = 42
)
#model_train
forest.fit(X_train, y_train)
print(f"  Done - {N_TREES} trees trained")

# feature importance 
# Random Forest averages feature importance across all 100 trees
# much more reliable than a single tree's importance scores
print("\nFeature importance scores:")

importances = forest.feature_importances_
pairs = sorted(zip(FEATURE_NAMES, importances),
               key=lambda x: x[1], reverse=True)
for name, score in pairs:
    print(f"  {name:<15}  {score:.3f}")

# save 
joblib.dump(forest, "adams_forest.pkl")
print("\nSaved: adams_forest.pkl")

#  top-1 using score()
print("ACCURACY USING forest.score()")
train_score = forest.score(X_train, y_train)
test_score  = forest.score(X_test,  y_test)
print(f"\n  TRAIN top-1 : {train_score*100:.1f}%")
print(f"  TEST  top-1 : {test_score*100:.1f}%")

#  top-k using predict_proba 
print("TOP-K ACCURACY USING predict_proba")
print("Probabilities averaged across all 100 trees")

train_top1, train_top3, train_top5, n_train = check_topk(
    "TRAIN", X_train, y_train, forest
)
test_top1, test_top3, test_top5, n_test = check_topk(
    "TEST", X_test, y_test, forest
)

