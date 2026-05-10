"""
train_tree.py
=============
Reads adams.pgn, extracts Adams' moves,
trains a decision tree, and saves it.

Run this ONCE before running the game:
    python train_tree.py

It produces two files:
    adams_tree.pkl        — the trained decision tree
    adams_leaf_moves.pkl  — moves Adams played in each leaf bucket
"""

import chess
import chess.pgn
import pickle
import joblib
from collections import Counter, defaultdict
from sklearn.tree import DecisionTreeClassifier, plot_tree
import matplotlib.pyplot as plt

# ── settings ──────────────────────────────────────────────────────────────────
PGN_FILE    = "adams.pgn"       # must be in the same folder as this script
PLAYER_NAME = "Adams, Michael"  # exactly as it appears in the PGN headers
MAX_DEPTH   = 4                 # how deep the tree is allowed to grow
# ──────────────────────────────────────────────────────────────────────────────


def get_features(board, castled):
    """
    Turn a board position into 3 numbers the tree can understand.

    move_number  — what move are we on?
                   tells the tree: opening / middlegame / endgame

    can_capture  — can we take an opponent piece right now?
                   1 = yes,  0 = no

    castled      — has Adams already castled?
                   1 = yes,  0 = no
    """
    move_number = board.fullmove_number
    can_capture = int(any(board.is_capture(m) for m in board.legal_moves))
    return [move_number, can_capture, int(castled)]


def read_pgn(pgn_file, player_name):
    """
    Walk through every game in the PGN file.
    For every position where it is Adams' turn,
    record the 3 features AND the move he played.
    Returns a list of (features, uci_move) pairs.
    """
    rows = []

    with open(pgn_file, encoding="utf-8", errors="ignore") as f:
        while True:
            game = chess.pgn.read_game(f)
            if game is None:
                break   # no more games

            white = game.headers.get("White", "")
            black = game.headers.get("Black", "")

            # which colour is Adams in this game?
            if player_name in white:
                adams_colour = chess.WHITE
            elif player_name in black:
                adams_colour = chess.BLACK
            else:
                continue   # Adams not in this game — skip

            board   = game.board()
            castled = False   # we track castling ourselves

            for move in game.mainline_moves():

                if board.turn == adams_colour:
                    # record features BEFORE the move is made
                    features = get_features(board, castled)
                    rows.append((features, move.uci()))

                    # did Adams just castle?
                    if board.is_castling(move):
                        castled = True

                board.push(move)   # advance the board

    return rows


# ── 1. read PGN ───────────────────────────────────────────────────────────────
print(f"Reading {PGN_FILE} ...")
rows = read_pgn(PGN_FILE, PLAYER_NAME)
print(f"  Positions found where Adams moved: {len(rows)}")

if not rows:
    print("ERROR: no moves found — check PGN_FILE and PLAYER_NAME above.")
    exit()

# ── 2. build X and y ──────────────────────────────────────────────────────────
X = [r[0] for r in rows]   # features: [[move_no, can_cap, castled], ...]
y = [r[1] for r in rows]   # labels:   ["e2e4", "g1f3", ...]

print(f"  Unique moves Adams played: {len(set(y))}")

# ── 3. train the tree ─────────────────────────────────────────────────────────
print(f"\nTraining decision tree (max_depth={MAX_DEPTH}) ...")
tree = DecisionTreeClassifier(max_depth=MAX_DEPTH, random_state=42)
tree.fit(X, y)
print(f"  Done — tree has {tree.get_n_leaves()} leaf buckets")

# ── 4. build leaf_moves dictionary ───────────────────────────────────────────
# For each leaf bucket, store every move Adams played that landed there.
# Sort by frequency so the most repeated move is first.
# At game time we will try moves from this list top to bottom
# until we find one that is legal in the current position.

leaf_ids   = tree.apply(X)
leaf_moves = defaultdict(list)

for leaf_id, move in zip(leaf_ids, y):
    leaf_moves[leaf_id].append(move)

leaf_moves_sorted = {}
for leaf_id, moves in leaf_moves.items():
    counter = Counter(moves)
    leaf_moves_sorted[int(leaf_id)] = [m for m, _ in counter.most_common()]

print("\nLeaf summary (each leaf = one type of position):")
for lid, moves in leaf_moves_sorted.items():
    top     = moves[0]
    top_cnt = Counter(leaf_moves[lid])[top]
    print(f"  Leaf {lid:4d} | {len(moves):3d} positions | "
          f"top move: {top} ({top_cnt}x)")

# ── 5. save ───────────────────────────────────────────────────────────────────
joblib.dump(tree, "adams_tree.pkl")
with open("adams_leaf_moves.pkl", "wb") as f:
    pickle.dump(leaf_moves_sorted, f)

print("\nSaved: adams_tree.pkl  and  adams_leaf_moves.pkl")

# ── 6. draw the tree diagram ──────────────────────────────────────────────────
print("Drawing tree diagram ...")
plt.figure(figsize=(16, 6))
plot_tree(
    tree,
    feature_names=["move_number", "can_capture", "castled"],
    filled=True,
    rounded=True,
    fontsize=9,
    max_depth=3,
    impurity=False,
)
plt.title(
    "Adams Decision Tree — move_number / can_capture / castled",
    fontsize=12,
    fontweight="bold",
)
plt.tight_layout()
plt.savefig("adams_tree.png", dpi=130, bbox_inches="tight")
plt.close()
print("Saved: adams_tree.png")
print("\nAll done — now run your game file.")