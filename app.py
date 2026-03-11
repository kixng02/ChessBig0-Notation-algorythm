import streamlit as st
import chess
import chess.svg
import chess.pgn
import pandas as pd
import numpy as np
import io
import base64

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Chess Big O Visualizer", layout="wide")

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&display=swap');
  h1, h2, h3 { font-family: 'Cinzel', serif !important; }
  .stButton>button {
    background: #c9a84c; color: #0f0e17; font-weight: 700;
    border: none; border-radius: 6px; padding: 8px 20px;
    font-family: 'Cinzel', serif;
  }
  .stButton>button:hover { background: #e8c46a; color: #0f0e17; }
  .metric-box {
    background: #1a1a2e; border-radius: 8px; padding: 14px;
    border: 1px solid #c9a84c44; text-align: center;
  }
  .metric-label { font-size: 0.72rem; color: #a7a9be; letter-spacing: 0.08em; margin-bottom: 4px; }
  .metric-value { font-size: 1.4rem; font-weight: 700; font-family: 'Cinzel', serif; }
</style>
""", unsafe_allow_html=True)

# ── Session State ─────────────────────────────────────────────────────────────
def init_state():
    if 'board' not in st.session_state:
        st.session_state.board = chess.Board()
    if 'selected_square' not in st.session_state:
        st.session_state.selected_square = None
    if 'legal_targets' not in st.session_state:
        st.session_state.legal_targets = []
    if 'move_history' not in st.session_state:
        st.session_state.move_history = []
    if 'status' not in st.session_state:
        st.session_state.status = "White to move ♔"
    if 'promotion_pending' not in st.session_state:
        st.session_state.promotion_pending = None  # (from_sq, to_sq)

init_state()

# ── Helper Functions ──────────────────────────────────────────────────────────
def sq_name_to_index(sq_name):
    """Convert 'e4' -> chess square index."""
    return chess.parse_square(sq_name)

def render_board_svg(board, selected=None, legal_targets=None):
    """Render board SVG with highlights."""
    arrows = []
    squares_dict = {}

    if selected is not None:
        squares_dict[selected] = "#c9a84c"  # gold for selected

    if legal_targets:
        for sq in legal_targets:
            squares_dict[sq] = "#7eb53a99"  # green tint for legal moves

    board_svg = chess.svg.board(
        board=board,
        squares=chess.SquareSet(squares_dict.keys()) if squares_dict else None,
        colors={"square light lastmove": "#cdd16e", "square dark lastmove": "#aaa23a"},
        size=420
    )

    # Custom SVG coloring via injection
    if squares_dict:
        for sq, color in squares_dict.items():
            file_idx = chess.square_file(sq)
            rank_idx = chess.square_rank(sq)
            # chess.svg uses rank 0=bottom; display rank = 7-rank_idx for white's perspective
            x = file_idx * 45 + 20
            y = (7 - rank_idx) * 45 + 20
            highlight = f'<rect x="{x}" y="{y}" width="45" height="45" fill="{color}" opacity="0.55"/>'
            board_svg = board_svg.replace("</svg>", highlight + "</svg>")

    b64 = base64.b64encode(board_svg.encode('utf-8')).decode('utf-8')
    return f'<img src="data:image/svg+xml;base64,{b64}" style="width:100%; max-width:430px; border: 3px solid #c9a84c; border-radius:4px; box-shadow: 0 0 30px #c9a84c22;"/>'

def update_status():
    board = st.session_state.board
    if board.is_checkmate():
        winner = "Black" if board.turn == chess.WHITE else "White"
        st.session_state.status = f"♛ Checkmate! {winner} wins!"
    elif board.is_stalemate():
        st.session_state.status = "½ Stalemate — Draw"
    elif board.is_check():
        side = "White" if board.turn == chess.WHITE else "Black"
        st.session_state.status = f"⚠️ {side} is in Check!"
    else:
        side = "White ♔" if board.turn == chess.WHITE else "Black ♚"
        st.session_state.status = f"{side} to move"

def handle_square_click(sq: int):
    board = st.session_state.board
    selected = st.session_state.selected_square

    # If promotion dialog is open, ignore board clicks
    if st.session_state.promotion_pending:
        return

    piece = board.piece_at(sq)

    if selected is None:
        # Select a piece belonging to current player
        if piece and piece.color == board.turn:
            st.session_state.selected_square = sq
            st.session_state.legal_targets = [
                m.to_square for m in board.legal_moves if m.from_square == sq
            ]
    else:
        if sq in st.session_state.legal_targets:
            move = chess.Move(selected, sq)
            # Check if promotion
            moving_piece = board.piece_at(selected)
            if (moving_piece and moving_piece.piece_type == chess.PAWN and
                    chess.square_rank(sq) in (0, 7)):
                # Need promotion choice
                st.session_state.promotion_pending = (selected, sq)
                st.session_state.selected_square = None
                st.session_state.legal_targets = []
                return
            # Normal move
            board.push(move)
            san = board.san(board.peek()) if False else chess.Board(board.fen().replace(board.fen().split()[-1], str(int(board.fen().split()[-1])))).san(move) 
            try:
                san = board.peek().uci()
            except Exception:
                san = move.uci()
            st.session_state.move_history.append(san)
            st.session_state.selected_square = None
            st.session_state.legal_targets = []
            update_status()
        else:
            # Re-select if clicking own piece
            if piece and piece.color == board.turn:
                st.session_state.selected_square = sq
                st.session_state.legal_targets = [
                    m.to_square for m in board.legal_moves if m.from_square == sq
                ]
            else:
                st.session_state.selected_square = None
                st.session_state.legal_targets = []

def apply_promotion(piece_type):
    pending = st.session_state.promotion_pending
    if not pending:
        return
    from_sq, to_sq = pending
    move = chess.Move(from_sq, to_sq, promotion=piece_type)
    board = st.session_state.board
    board.push(move)
    st.session_state.move_history.append(move.uci())
    st.session_state.promotion_pending = None
    update_status()

def calc_nodes(b, d, algo):
    if algo == "Minimax":
        return float(b) ** d
    return 2 * float(b) ** (d / 2) - 1

# ── Title ─────────────────────────────────────────────────────────────────────
st.title("♟️ Chess Engine: Big O Notation Visualizer")
st.markdown(
    "<p style='color:#a7a9be; font-size:1.05rem;'>Compare <b>Minimax</b> O(bᵈ) vs "
    "<b>Alpha-Beta Pruning</b> O(b^d/2) — interact with the board to see live complexity metrics.</p>",
    unsafe_allow_html=True
)

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.header("⚙️ Engine Settings")
branching_factor = st.sidebar.slider("Avg. Branching Factor (b)", 2, 40, 35)
max_depth = st.sidebar.slider("Simulation Depth (d)", 1, 8, 4)

st.sidebar.markdown("---")
st.sidebar.header("📋 PGN Input")
pgn_input = st.sidebar.text_area("Paste PGN (optional)", height=140, placeholder="1. e4 e5 2. Nf3 ...")
if pgn_input and st.sidebar.button("Load PGN"):
    try:
        pgn = io.StringIO(pgn_input)
        game = chess.pgn.read_game(pgn)
        if game:
            st.session_state.board = game.board()
            for move in game.mainline_moves():
                st.session_state.board.push(move)
            st.session_state.move_history = [m.uci() for m in game.mainline_moves()]
            st.session_state.selected_square = None
            st.session_state.legal_targets = []
            update_status()
            st.rerun()
    except Exception as e:
        st.sidebar.error(f"PGN error: {e}")

# ── Main Layout ───────────────────────────────────────────────────────────────
col_board, col_analysis = st.columns([1, 1.3])

# ── Board Column ──────────────────────────────────────────────────────────────
with col_board:
    st.subheader("Interactive Board")

    # Status banner
    status = st.session_state.status
    color = "#ff6b6b" if "Check" in status or "Checkmate" in status else \
            "#69ff9a" if "wins" in status or "Draw" in status else "#c9a84c"
    st.markdown(
        f'<div style="background:#1a1a2e;border:1px solid {color}44;border-radius:8px;'
        f'padding:10px 16px;text-align:center;margin-bottom:12px;">'
        f'<span style="color:{color};font-size:1rem;font-weight:600;">{status}</span></div>',
        unsafe_allow_html=True
    )

    # Promotion dialog (shown ABOVE board when active)
    if st.session_state.promotion_pending:
        st.markdown("**Promote pawn to:**")
        pcols = st.columns(4)
        pieces = [(chess.QUEEN, "♕ Queen"), (chess.ROOK, "♖ Rook"),
                  (chess.BISHOP, "♗ Bishop"), (chess.KNIGHT, "♘ Knight")]
        for i, (pt, label) in enumerate(pieces):
            with pcols[i]:
                if st.button(label, key=f"promo_{pt}"):
                    apply_promotion(pt)
                    st.rerun()

    # Board SVG
    st.markdown(
        render_board_svg(
            st.session_state.board,
            st.session_state.selected_square,
            st.session_state.legal_targets
        ),
        unsafe_allow_html=True
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # Clickable square grid — 8x8 buttons
    st.markdown("**Click a square to select / move:**")
    board = st.session_state.board

    for rank in range(7, -1, -1):  # rank 8 down to 1
        cols = st.columns(8)
        for file in range(8):
            sq = chess.square(file, rank)
            piece = board.piece_at(sq)
            is_sel = (st.session_state.selected_square == sq)
            is_target = sq in st.session_state.legal_targets

            # Button label
            if piece:
                symbol = piece.unicode_symbol()
            else:
                symbol = "·" if is_target else " "

            # Square color hint in label
            prefix = "🟡" if is_sel else ("🟢" if is_target and piece else ("⚫" if is_target else ""))
            label = f"{prefix}{symbol}" if prefix else symbol if symbol.strip() else "·"

            with cols[file]:
                if st.button(label, key=f"sq_{sq}", help=chess.square_name(sq)):
                    handle_square_click(sq)
                    st.rerun()

    # Controls
    bcol1, bcol2 = st.columns(2)
    with bcol1:
        if st.button("↺ Reset Board"):
            st.session_state.board = chess.Board()
            st.session_state.selected_square = None
            st.session_state.legal_targets = []
            st.session_state.move_history = []
            st.session_state.promotion_pending = None
            st.session_state.status = "White to move ♔"
            st.rerun()
    with bcol2:
        if st.button("↩ Undo Move"):
            if len(st.session_state.board.move_stack) > 0:
                st.session_state.board.pop()
                if st.session_state.move_history:
                    st.session_state.move_history.pop()
                st.session_state.selected_square = None
                st.session_state.legal_targets = []
                update_status()
                st.rerun()

    # Move history
    if st.session_state.move_history:
        st.markdown("**Move History:**")
        history = st.session_state.move_history
        pairs = []
        for i in range(0, len(history), 2):
            w = history[i]
            b = history[i+1] if i+1 < len(history) else ""
            pairs.append(f"{i//2+1}. {w} {b}")
        st.text(" | ".join(pairs[-8:]))  # show last 8 half-move pairs

# ── Analysis Column ───────────────────────────────────────────────────────────
with col_analysis:
    st.subheader("Complexity Analysis")

    # Metrics
    actual_b = board.legal_moves.count()
    m_nodes = calc_nodes(branching_factor, max_depth, "Minimax")
    a_nodes = calc_nodes(branching_factor, max_depth, "Alpha-Beta")
    reduction = ((m_nodes - a_nodes) / m_nodes * 100) if m_nodes > 0 else 0

    def fmt(n):
        n = int(n)
        if n >= 1_000_000_000: return f"{n/1e9:.1f}B"
        if n >= 1_000_000: return f"{n/1e6:.1f}M"
        if n >= 1_000: return f"{n/1e3:.0f}K"
        return f"{n:,}"

    mc1, mc2, mc3, mc4 = st.columns(4)
    with mc1:
        st.markdown(f'<div class="metric-box"><div class="metric-label">MINIMAX NODES</div>'
                    f'<div class="metric-value" style="color:#ff6b6b">{fmt(m_nodes)}</div></div>', unsafe_allow_html=True)
    with mc2:
        st.markdown(f'<div class="metric-box"><div class="metric-label">ALPHA-BETA NODES</div>'
                    f'<div class="metric-value" style="color:#69ff9a">{fmt(a_nodes)}</div></div>', unsafe_allow_html=True)
    with mc3:
        st.markdown(f'<div class="metric-box"><div class="metric-label">REDUCTION</div>'
                    f'<div class="metric-value" style="color:#c9a84c">{reduction:.1f}%</div></div>', unsafe_allow_html=True)
    with mc4:
        st.markdown(f'<div class="metric-box"><div class="metric-label">LEGAL MOVES NOW</div>'
                    f'<div class="metric-value" style="color:#7eb5ff">{actual_b}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Chart data
    depths = list(range(1, max_depth + 1))
    chart_df = pd.DataFrame({
        "Depth": depths,
        "Minimax O(bᵈ)": [calc_nodes(branching_factor, d, "Minimax") for d in depths],
        "Alpha-Beta O(b^d/2)": [calc_nodes(branching_factor, d, "Alpha-Beta") for d in depths],
    }).set_index("Depth")

    st.line_chart(chart_df, color=["#ff6b6b", "#69ff9a"])

    # Theory section
    st.markdown("---")
    st.markdown("### Understanding the Algorithms")

    t1, t2 = st.columns(2)
    with t1:
        st.markdown(f"""
**🔴 Minimax: O(bᵈ)**

Every single node in the game tree must be visited. With b={branching_factor} and d={max_depth}:

- **Nodes:** {fmt(m_nodes)}
- Grows **exponentially** — each extra ply multiplies work by {branching_factor}×
        """)
    with t2:
        st.markdown(f"""
**🟢 Alpha-Beta: O(b^d/2)**

"Prunes" branches that can't affect the result. Best-case with b={branching_factor} and d={max_depth}:

- **Nodes:** {fmt(a_nodes)}
- Searches **twice as deep** for the same compute cost
        """)

    st.markdown("---")
    st.caption("Theoretical values assume optimal move ordering for Alpha-Beta. Real-world performance varies.")
