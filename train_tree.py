"""
It produces two files:
    adams_tree.pkl        — the trained decision tree
    adams_leaf_moves.pkl  — moves Adams played in each leaf bucket
"""

import chess
import chess.pgn
import joblib
from sklearn.tree import DecisionTreeClassifier, plot_tree
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt

PGN_FILE    = "adams.pgn"
PLAYER_NAME = "Adams, Michael"
MAX_DEPTH   = 4

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

# READ PGN
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
                    features = get_features(board, castled)
                    rows.append((features, move.uci()))

                    if board.is_castling(move):
                        castled = True

                board.push(move)

    return rows

def check_bucket(label, X_data, y_data, tree, leaf_moves_sorted):
    """
    For every position check whether Adams' actual move
    exists anywhere in that bucket's ranked move list.
    """
    found     = 0
    not_found = 0
    total     = len(X_data)

    for i in range(total):

        actual_move  = y_data[i]
        bucket       = int(tree.apply([X_data[i]])[0])
        bucket_moves = leaf_moves_sorted.get(bucket, [])

        if actual_move in bucket_moves:
            found += 1
        else:
            not_found += 1

    print(f"\n  {label} ({total} positions):")
    print(f"    move found in bucket     : {found}/{total}  ({found/total*100:.1f}%)")
    print(f"    move NOT found in bucket : {not_found}/{total}  ({not_found/total*100:.1f}%)")

    return found, not_found, total


# check the position of the move in the bucket

def check_rank(label, X_data, y_data, tree, leaf_moves_sorted):
    """
    For every position where Adams' move is in the bucket,
    find what position it sits at in the ranked list.
    """
    ranks        = []   # rank position of Adams' move for each position
    bucket_sizes = []  

    top1 = top3 = top5 = top10 = 0
    skipped = 0   # positions where move was not in bucket at all

    total = len(X_data)

    for i in range(total):

        actual_move  = y_data[i]
        bucket       = int(tree.apply([X_data[i]])[0])
        bucket_moves = leaf_moves_sorted.get(bucket, [])

        bucket_sizes.append(len(bucket_moves))
        if actual_move not in bucket_moves:
            skipped += 1
            continue   # skip positions where move is not in bucket

        # find the rank, position in the list starting from 1
        rank = bucket_moves.index(actual_move) + 1
        ranks.append(rank)

        if rank <= 1:  top1  += 1
        if rank <= 3:  top3  += 1
        if rank <= 5:  top5  += 1
        if rank <= 10: top10 += 1

    found = total - skipped

    if not ranks:
        print(f"\n  {label} no moves found in any bucket.")
        return


    print(f"\n  {label} ({found} positions where move was found):")


    print(f"    rank 1  (top move)       : {top1}/{found}  ({top1/found*100:.1f}%)")
    print(f"    rank 1-3                 : {top3}/{found}  ({top3/found*100:.1f}%)")
    print(f"    rank 1-5                 : {top5}/{found}  ({top5/found*100:.1f}%)")
    print(f"    rank 1-10                : {top10}/{found}  ({top10/found*100:.1f}%)")

    return top1,top3


# start here
# read PGN
print(f"Reading {PGN_FILE}")
rows = read_pgn(PGN_FILE, PLAYER_NAME)
print(f"  Positions found where Adams moved : {len(rows)}")

if not rows:
    print("ERROR: no moves found")
    exit()
# build X and y 
X = [r[0] for r in rows]
y = [r[1] for r in rows]

print(f"  Unique moves Adams played         : {len(set(y))}")

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)
print(f"  Training positions                : {len(X_train)}")
print(f"  Test positions                    : {len(X_test)}")

#  train the tree 
print(f"\nTraining decision tree (max_depth={MAX_DEPTH})")
tree = DecisionTreeClassifier(max_depth=MAX_DEPTH, random_state=42)
tree.fit(X_train, y_train)
print(f" Done, tree has {tree.get_n_leaves()} leaf buckets")

# build leaf_moves dictionary 
leaf_moves_sorted = {}

for i in range(len(X_train)):
    bucket = int(tree.apply([X_train[i]])[0])
    move   = y_train[i]

    if bucket not in leaf_moves_sorted:
        leaf_moves_sorted[bucket] = []
    leaf_moves_sorted[bucket].append(move)

for bucket in leaf_moves_sorted:
    moves = leaf_moves_sorted[bucket]
    leaf_moves_sorted[bucket] = sorted(
        set(moves),
        key=lambda m: moves.count(m),
        reverse=True
    )
print(f"  Buckets built : {len(leaf_moves_sorted)}")

# save
joblib.dump(tree,              "adams_tree.pkl")
joblib.dump(leaf_moves_sorted, "adams_leaf_moves.pkl")
print("saved")
#top-1 using tree.score() 
train_score = tree.score(X_train, y_train)
test_score  = tree.score(X_test,  y_test)
print(f"\n TRAIN top-1 : {train_score*100:.1f}%")
print(f"  TEST  top-1 : {test_score*100:.1f}%")
# bucket check 
train_found, train_not, train_total = check_bucket(
    "TRAIN", X_train, y_train, tree, leaf_moves_sorted
)
test_found, test_not, test_total = check_bucket(
    "TEST", X_test, y_test, tree, leaf_moves_sorted
)

# rank check
check_rank("TRAIN", X_train, y_train, tree, leaf_moves_sorted)
check_rank("TEST",  X_test,  y_test,  tree, leaf_moves_sorted)

#draw the tree

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
    "Adams Decision Tree - move_number / can_capture / castled",
    fontsize=12,
    fontweight="bold",
)
plt.tight_layout()
plt.savefig("adams_tree.png", dpi=130, bbox_inches="tight")
plt.close()
print("Saved")
