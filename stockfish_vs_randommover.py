
import chess          
import chess.svg      
import random         
import subprocess     
import base64         
import os             

SF_PATH = r"C:\Users\akhil\OneDrive\Desktop\Akhila\Code\.vscode\chess_app\stockfish\stockfish.exe"


# stockfish
def find_stockfish():

    # check the file location 
    if not os.path.exists(SF_PATH):
        return None  # file not found

    #  path is available
    try:
        # subprocess.Popen opens the Stockfish program
        
        proc = subprocess.Popen(
            SF_PATH,
            #to SEND commands to Stockfish
            stdin=subprocess.PIPE, 
            #to READ replies from stockfish  
            stdout=subprocess.PIPE,  
            #to catch any error message
            stderr=subprocess.PIPE, 
            text=True                
        )

        # Send "uci" (a standard chess engine greeting) then "quit"
        proc.stdin.write("uci\nquit\n")
        #send it 
        proc.stdin.flush()  
        # wait max 5 seconds for it to finish    
        proc.wait(timeout=5)   

        return SF_PATH 
    except Exception:
        return None 


# stockfish move 
def get_stockfish_move(board, skill_level=1, movetime_ms=100):
   

    try:
        # Open Stockfish again (we open a fresh process each time)
        proc = subprocess.Popen(
            SF_PATH,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Build the commands we want to send to Stockfish
        # board.fen() converts the board to a text string Stockfish understands
        commands = (
            #setoption name [Setting Name] value [X] , in this case the setting name is Skill level
            f"setoption name Skill Level value {skill_level}\n"  
            #pass the position using fen
            f"position fen {board.fen()}\n"         
            #how much time does it hve to make the decision             
            f"go movetime {movetime_ms}\n"                       
        )

        # Send all commands at once
        proc.stdin.write(commands)
        proc.stdin.flush()

        # Read Stockfish's reply line by line until we see "bestmove"
        best_move = None
        while True:
            line = proc.stdout.readline().strip()
            if line.startswith("bestmove"):
                parts = line.split()   
                if len(parts) >= 2:
                    best_move = parts[1] 
                break  

        # Close Stockfish cleanly
        proc.stdin.write("quit\n")
        proc.stdin.flush()
        proc.wait(timeout=5)

        # Convert the move string "e2e4" into uci form
        if best_move and best_move != "(none)":
            return chess.Move.from_uci(best_move)

        return get_random_move(board)

    except Exception:
        return get_random_move(board)  


# Pick a random legal move 
def get_random_move(board):
 
    return random.choice(list(board.legal_moves))


# Play one move on the board 
def do_next_move(board, move_history, stats, sf_path, skill_level=1):

    # If game is already finished, do nothing
    if board.is_game_over():
        return board, move_history, stats, True

    # Decide who plays and what move they make
    if board.turn == chess.WHITE:
        move   = get_random_move(board)  
        player = "random"
    else:
        if sf_path:
            move   = get_stockfish_move(board, skill_level) 
            player = "stockfish"
        else:
            move   = get_random_move(board)  # no Stockfish? random vs random
            player = "random"

    # Convert the move to human-readable format before pushing
    # (we must do this BEFORE push, because after push it's the next turn)
    san = board.san(move)   # e.g. "e4" or "Nf3"

    # Make the move on the board
    board.push(move)

    # Save this move to the history log
    # format: (uci string, who played, san string, move number)
    move_history.append((move.uci(), player, san, board.fullmove_number))

    # Check if the game just ended after this movef
    game_over = False
    if board.is_game_over():
        game_over = True
        result = board.result()  

        # Update the scoreboard
        stats["games"] += 1
        if result == "1-0":
            stats["random_wins"] += 1    
        elif result == "0-1":
            stats["stockfish_wins"] += 1  
        else:
            stats["draws"] += 1          

    return board, move_history, stats, game_over


def new_game():
   
    return {
         # fresh board
        "board":        chess.Board(), 
        "move_history": [],             
        "last_move":    None,          
        "game_over":    False,         
    }


# Default stats
def default_stats():
 
    return {
        "random_wins":    0,
        "stockfish_wins": 0,
        "draws":          0,
        "games":          0,
    }


# Draw the board as an image 
def board_to_svg(board, last_move=None, size=420):

    # If there was a last move, draw a blue arrow showing it
    arrows = []
    if last_move:
        arrows = [chess.svg.Arrow(
            last_move.from_square,
            last_move.to_square,
            color="#185FA5" 
        )]

    # Generate the SVG image string
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

    # Convert SVG text --> bytes --> base64 string
    # This is needed so we can embed it directly in an HTML <img> tag
    b64 = base64.b64encode(svg_str.encode()).decode()
    return f"data:image/svg+xml;base64,{b64}"


def result_label(result_str):
    if result_str == "1-0":
        return " White wins"
    elif result_str == "0-1":
        return "Black wins"
    else:
        return "Draw"


def turn_label(board):
   
    if board.turn == chess.WHITE:
        return f" White (Random Mover)- Move {board.fullmove_number}"
    return f" Black (Stockfish) - Move {board.fullmove_number}"


