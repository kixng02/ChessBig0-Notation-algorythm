import streamlit as st
import chess
import chess.svg
import chess.pgn
import pandas as pd
import numpy as np
import io
import base64
import time

# --- Helper Functions ---
def render_board(board):
    """Renders the chess board as an SVG and displays it in Streamlit."""
    board_svg = chess.svg.board(board=board, size=400)
    b64 = base64.b64encode(board_svg.encode('utf-8')).decode('utf-8')
    return f'<img src="data:image/svg+xml;base64,{b64}"/>'

def calculate_nodes(branching_factor, depth, algorithm):
    """
    Calculates the theoretical upper bound of nodes for Big O demonstration.
    Minimax: O(b^d)
    Alpha-Beta (Best Case): O(b^(d/2))
    """
    if algorithm == "Minimax":
        return branching_factor ** depth
    else:  # Alpha-Beta Pruning (Best case approximation)
        return 2 * (branching_factor ** (depth / 2)) - 1

# --- Streamlit UI Configuration ---
st.set_page_config(page_title="Chess Algorithmic Complexity", layout="wide")

st.title("♟️ Chess Engine: Big O Notation Visualizer")
st.markdown("""
This application demonstrates how **Search Depth** and **Branching Factor** impact the computational complexity 
of chess engines. We compare the standard **Minimax** algorithm ($O(b^d)$) with **Alpha-Beta Pruning** ($O(b^{d/2})$).
""")

# --- Sidebar Controls ---
st.sidebar.header("Engine Settings")
branching_factor = st.sidebar.slider("Avg. Branching Factor (b)", 2, 40, 35)
max_depth_sim = st.sidebar.slider("Simulation Depth (d)", 1, 8, 4)

st.sidebar.markdown("---")
st.sidebar.header("Game Input")
pgn_input = st.sidebar.text_area("Paste PGN here (optional)", height=150)

# --- Main Logic ---
col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("Interactive Board")
    
    # Session state for board
    if 'board' not in st.session_state:
        st.session_state.board = chess.Board()
    
    # Handle PGN
    if pgn_input:
        pgn = io.StringIO(pgn_input)
        game = chess.pgn.read_game(pgn)
        if game:
            moves = list(game.mainline_moves())
            move_idx = st.select_slider("Step through PGN", options=range(len(moves) + 1), value=0)
            
            # Reconstruct board up to move_idx
            new_board = chess.Board()
            for i in range(move_idx):
                new_board.push(moves[i])
            st.session_state.board = new_board

    st.write(render_board(st.session_state.board), unsafe_safe_html=True)
    
    if st.button("Reset Board"):
        st.session_state.board = chess.Board()
        st.rerun()

with col2:
    st.subheader("Complexity Analysis")
    
    # Data Generation for Graph
    depths = np.arange(1, max_depth_sim + 1)
    minimax_nodes = [calculate_nodes(branching_factor, d, "Minimax") for d in depths]
    alphabeta_nodes = [calculate_nodes(branching_factor, d, "Alpha-Beta") for d in depths]
    
    chart_data = pd.DataFrame({
        "Depth": depths,
        "Minimax (Nodes)": minimax_nodes,
        "Alpha-Beta (Nodes)": alphabeta_nodes
    }).set_index("Depth")
    
    st.line_chart(chart_data)
    
    # Stats Table
    current_b = len(list(st.session_state.board.legal_moves))
    st.info(f"**Current State:** {current_b} legal moves available (Actual Branching Factor).")
    
    metrics_col1, metrics_col2 = st.columns(2)
    m_nodes = calculate_nodes(branching_factor, max_depth_sim, "Minimax")
    a_nodes = calculate_nodes(branching_factor, max_depth_sim, "Alpha-Beta")
    
    metrics_col1.metric("Minimax Nodes", f"{int(m_nodes):,}")
    metrics_col2.metric("Alpha-Beta Nodes", f"{int(a_nodes):,}", delta=f"-{((m_nodes-a_nodes)/m_nodes)*100:.1f}% Reduction", delta_color="normal")

# --- Educational Content ---
st.markdown("---")
st.header("Understanding the Notation")

edu1, edu2 = st.columns(2)

with edu1:
    st.markdown("""
    ### 🔴 Minimax: $O(b^d)$
    In a raw Minimax search, the engine must visit every single node in the tree. 
    If there are 35 possible moves ($b=35$) and you want to look 4 moves ahead ($d=4$):
    - **Total Nodes:** $35^4 = 1,500,625$
    - This grows **exponentially**. Adding just one more ply of depth increases the work by 35x.
    """)

with edu2:
    st.markdown("""
    ### 🟢 Alpha-Beta Pruning: $O(b^{d/2})$
    Alpha-Beta optimizes the search by "pruning" branches that cannot possibly affect the final result.
    In the best-case scenario (searching the best move first):
    - **Total Nodes:** $\\approx 2 \\times 35^{4/2} = 2,450$
    - **Efficiency:** You can search **twice as deep** as Minimax using the same computational power.
    """)

st.write("---")
st.caption("Note: Theoretical values assume optimal move ordering for Alpha-Beta. Real-world performance varies based on heuristics.")
