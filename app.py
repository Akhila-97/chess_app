import streamlit as st
import time

from stockfish_vs_decisiontree import (
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
    page_title="Adams DT vs Stockfish",   # fix 1 — updated title
    layout="wide",
)

# SESSION STATE
if "board" not in st.session_state:
    game = new_game()
    st.session_state.board         = game["board"]
    st.session_state.move_history  = game["move_history"]
    st.session_state.last_move     = game["last_move"]
    st.session_state.game_over     = game["game_over"]
    st.session_state.white_castled = game["white_castled"]  # fix 2 — add castled
    st.session_state.stats         = default_stats()
    st.session_state.sf_path       = find_stockfish()


# HELPER FUNCTIONS
def reset():
    game = new_game()
    st.session_state.board         = game["board"]
    st.session_state.move_history  = game["move_history"]
    st.session_state.last_move     = game["last_move"]
    st.session_state.game_over     = game["game_over"]
    st.session_state.white_castled = game["white_castled"]  # fix 3 — reset castled too


def step():
    board, history, stats, over, white_castled = do_next_move(
        st.session_state.board,
        st.session_state.move_history,
        st.session_state.stats,
        st.session_state.sf_path,
        st.session_state.get("white_castled", False),
        st.session_state.get("skill_level", 1),
    )
    st.session_state.board         = board
    st.session_state.move_history  = history
    st.session_state.stats         = stats
    st.session_state.game_over     = over
    st.session_state.white_castled = white_castled

    if history:
        if not over:
            st.session_state.last_move = board.peek()
        else:
            st.session_state.last_move = history[-1][0]


# PAGE TITLE
st.title("Adams Decision Tree vs Stockfish")           # fix 4 — updated title
st.caption("White plays using Adams' style. Black is Stockfish.")  # fix 5 — updated caption


# LAYOUT
left, right = st.columns([2, 1], gap="large")


# LEFT COLUMN — BOARD
with left:

    if st.session_state.sf_path:
        st.success("Stockfish connected")
    else:
        st.warning("Stockfish not found")

    last_move = None
    if st.session_state.move_history:
        try:
            last_move = st.session_state.board.peek()
        except Exception:
            pass

    svg = board_to_svg(st.session_state.board, last_move)
    st.markdown(
        f'<div style="text-align:center; margin:12px 0">'
        f'<img src="{svg}" width="420"/>'
        f'</div>',
        unsafe_allow_html=True
    )

    if st.session_state.game_over:
        result = st.session_state.board.result()
        st.success(f"Game over — {result_label(result)}")
    else:
        st.caption(turn_label(st.session_state.board))

    st.write("")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        if st.button("Next Move", disabled=st.session_state.game_over):
            step()
            st.rerun()

    with c2:
        if st.button("Play 10 Moves", disabled=st.session_state.game_over):
            for _ in range(10):
                if not st.session_state.board.is_game_over():
                    step()
            st.rerun()

    with c3:
        if st.button("Play Full Game"):
            with st.spinner("Playing full game..."):
                while not st.session_state.board.is_game_over():
                    step()
                    time.sleep(0.02)
            st.rerun()

    with c4:
        if st.button("New Game"):
            reset()
            st.rerun()


# RIGHT COLUMN — STATS AND MOVE LOG
with right:

    st.subheader("Session Stats")

    stats = st.session_state.stats

    s1, s2, s3 = st.columns(3)
    with s1:
        st.metric("Adams DT Wins", stats["dt_wins"])    # fix 6 — label updated
    with s2:
        st.metric("SF Wins", stats["stockfish_wins"])
    with s3:
        st.metric("Draws", stats["draws"])

    st.caption(f"{stats['games']} total games played")

    st.write("")

    st.subheader("Move Log")

    history = st.session_state.move_history

    if not history:
        st.caption("No moves yet — press Next Move to start!")
    else:
        for uci, player, san, move_num in reversed(history[-20:]):

            # fix 7 — correct player labels
            if player == "adams_dt":
                who = "Adams DT"
            elif player == "stockfish":
                who = "Stockfish"
            else:
                who = "Random"

            st.text(f"{move_num}. {san} ({uci})  —  {who}")