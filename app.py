

import streamlit as st
import time

# Import all the functions we need from our chess engine
from stockfish_vs_randommover import (
    find_stockfish,
    board_to_svg,
    do_next_move,
    new_game,
    default_stats,
    result_label,
    turn_label,
)

# PAGE SETTINGS 
st.set_page_config(
    page_title="Random Mover vs Stockfish",
    layout="wide",  
)


#  SESSION STATE 
if "board" not in st.session_state:
    # create a fresh game
    game = new_game()               
    # the chess board               
    st.session_state.board        = game["board"]        
    # list of moves played
    st.session_state.move_history = game["move_history"] 
    #the last move played
    st.session_state.last_move    = game["last_move"]   
    #check the status of the game
    st.session_state.game_over    = game["game_over"]   
    # win/loss/draw counters
    st.session_state.stats        = default_stats()     
    #check whether stockfish is connected or not
    st.session_state.sf_path      = find_stockfish()    


# HELPER FUNCTIONS
def reset():
    """Start a brand new game, called when you click New Game."""
    game = new_game()
    st.session_state.board        = game["board"]
    st.session_state.move_history = game["move_history"]
    st.session_state.last_move    = game["last_move"]
    st.session_state.game_over    = game["game_over"]
  


def step():
    """Play one single move and save the result to session state."""
    # Ask the chess engine to play one move
    board, history, stats, over = do_next_move(
        st.session_state.board,
        st.session_state.move_history,
        st.session_state.stats,
        st.session_state.sf_path,
        st.session_state.get("skill_level", 1),  # default skill = 1
    )

    # Save everything back to the backpack
    st.session_state.board        = board
    st.session_state.move_history = history
    st.session_state.stats        = stats
    st.session_state.game_over    = over

    # Save the last move so we can highlight it on the board
    if history:
        if not over:
            st.session_state.last_move = board.peek()  # peek = see last move
        else:
            st.session_state.last_move = history[-1][0]  # use history if game over


#  PAGE TITLE 
st.title("Random Mover vs Stockfish")
st.caption("White plays random moves. Black is Stockfish.")


# LAYOUT: TWO COLUMNS 
# Split the screen into left (board) and right (stats) in 2:1 ratio
left, right = st.columns([2, 1], gap="large")


# THE CHESS BOARD
with left:
    # Show whether Stockfish was found or not, checkif its returing a path
    if st.session_state.sf_path:
        st.success(" Stockfish connected")
    else:
        st.warning(" Stockfish not found")

    # Draw the chess board
    # board_to_svg returns a base64 image string we can embed in HTML
    last_move = None
    if st.session_state.move_history:
        try:
            # get last move for highlight
            #board.peek()    returns the LAST move that was made, without removing it
            #board.pop() return the LAST move and will remove it
            last_move = st.session_state.board.peek()  
        except Exception:
            pass
    
    svg = board_to_svg(st.session_state.board, last_move)

    # Display the board image centered on screen
    st.markdown(
        f'<div style="text-align:center; margin:12px 0">'
        f'<img src="{svg}" width="420"/>'
        f'</div>',
        unsafe_allow_html=True
    )

    # Show game result OR whose turn it is
    if st.session_state.game_over:
        result = st.session_state.board.result()
        #change result into human readable form
        st.success(f"Game over  {result_label(result)}")
    else:
        st.caption(turn_label(st.session_state.board))

    st.write("")  

    # THE FOUR BUTTONS 
    # Put 4 buttons side by side using 4 equal columns
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        # disabled=True means the button is grayed out when game is over
        if st.button(" Next Move", disabled=st.session_state.game_over):
            step()  
            ## st.rerun() forces the entire app.py to run again from top to bottom      
            st.rerun()   

    with c2:
        if st.button("play 10 Moves", disabled=st.session_state.game_over):
            for _ in range(10):   # loop 10 times
                if not st.session_state.board.is_game_over():
                    step()
            st.rerun()

    with c3:
        if st.button("Play full Game"):
            # st.spinner shows a loading animation while running
            with st.spinner("Playing full game..."):
                while not st.session_state.board.is_game_over():
                    step()
                    time.sleep(0.02)  # tiny pause so it doesn't freeze
            st.rerun()

    with c4:
        if st.button("New Game"):
            #reset function is called
            reset()
            st.rerun()


# RIGHT COLUMN — STATS AND MOVE LOG

with right:

    #SCOREBOARD
    st.subheader("Session Stats")

    stats = st.session_state.stats  

    # Show 3 numbers side by side using 3 equal columns
    s1, s2, s3 = st.columns(3)
    with s1:
        st.metric("Random Wins", stats["random_wins"])
    with s2:
        st.metric("SF Wins", stats["stockfish_wins"])
    with s3:
        st.metric("Draws", stats["draws"])

    st.caption(f"{stats['games']} total games played")

    st.write("")  # gap


    st.subheader("Move Log")

    history = st.session_state.move_history

    if not history:
        st.caption("No moves yet — press Next Move to start!")
    else:
        # Show last 20 moves, newest first (reversed)
        for uci, player, san, move_num in reversed(history[-20:]):

            # Pick a label based on who played
            if player == "random":
                who = " Random"
            else:
                who = " Stockfish"

            # Show one line per move
            st.text(f"{move_num}. {san} ({uci})  —  {who}")