import chess.engine
import os

print("Current folder:", os.getcwd())
print("Files here:", os.listdir("."))
print("Files in stockfish folder:", os.listdir("stockfish"))

try:
    engine = chess.engine.SimpleEngine.popen_uci("stockfish/stockfish.exe")
    print("Stockfish works!")
    engine.quit()
except Exception as e:
    print("FAILED:", e)