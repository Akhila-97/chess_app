import chess as chess

board = chess.Board()
#print(board)

#print(chess.B1)

# move = chess.Move(chess.E2, chess.E4)  # from, to
# board.push(move)
# print(board)

# move = chess.Move.from_uci('e2e4')
# board.push(move)
# print(board)

# move = board.parse_san("e4")
# board.push(move)
# print(board)

# move = chess.Move.from_uci('a2e4')
# board.push(move)
# print(board)

# move = chess.Move.from_uci('a2e4')
# if move in board.legal_moves:
#     board.push(move)
#     print(board)
# else:
#     print("illegal move")

# moves = list(board.legal_moves)
# print(moves)   
# Count how many legal moves
#print(board.legal_moves.count())

# if board.turn == chess.WHITE:
#     print("White's turn")
# else:
#     print("Black's turn")

#board.turn automatically switches after every board.push(move)
# move = chess.Move.from_uci('e2e4')
# if move in board.legal_moves:
#     board.push(move)
#     print(board)
# else:
#     print("illegal move")
# if board.turn == chess.WHITE:
#     print("White's turn")
# else:
#     print("Black's turn")

print(board.is_game_over())    # True or False

print(board.is_checkmate())  # someone got checkmated
print(board.is_stalemate())   # stalemate
print(board.is_check())        # current player is in check
# Get the result
print(board.result())   

# Save current position as FEN
fen = board.fen()
print(fen)

# # Load a position from FEN
# board = chess.Board("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1")

# # Famous positions
# scholars_mate = chess.Board("r1bqkb1r/pppp1Qpp/2n2n2/4p3/2B1P3/8/PPPP1PPP/RNB1K1NR b KQkq - 0 4")


import chess.svg

board = chess.Board()

svg = chess.svg.board(board, size=1000)
#move = chess.Move.from_uci('a2a4')
svg = chess.svg.board(board)
#arrow = chess.svg.Arrow(chess.E2, chess.E4, color="red")
#svg = chess.svg.board(board, arrows=[arrow])
html = f"""
<!DOCTYPE html>
<html>
<body style="background:white">
    {svg}
</body>
</html>
"""

with open("board.html", "w") as f:
    f.write(html)

print("Done! Open board.html in Chrome")