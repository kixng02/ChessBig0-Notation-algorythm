"""
♚ Chess & Big O — Interactive Explorer
Click pieces, make moves, and watch algorithmic complexity unfold in real-time.
"""

import streamlit as st
import chess
import chess.pgn
import chess.svg
import io
import time
import math
import random
import base64
import json
from typing import List, Tuple, Dict, Optional

# ─────────────────────────────────────────────
# Page Config
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Chess & Big O",
    page_icon="♚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# Session State Init
# ─────────────────────────────────────────────
if "board" not in st.session_state:
    st.session_state.board = chess.Board()
if "selected_square" not in st.session_state:
    st.session_state.selected_square = None
if "move_history" not in st.session_state:
    st.session_state.move_history = []
if "algo_log" not in st.session_state:
    st.session_state.algo_log = []
if "highlight_squares" not in st.session_state:
    st.session_state.highlight_squares = set()
if "show_attacks" not in st.session_state:
    st.session_state.show_attacks = False
if "auto_engine" not in st.session_state:
    st.session_state.auto_engine = False
if "engine_depth" not in st.session_state:
    st.session_state.engine_depth = 3
if "pgn_loaded" not in st.session_state:
    st.session_state.pgn_loaded = False
if "pgn_moves" not in st.session_state:
    st.session_state.pgn_moves = []
if "pgn_index" not in st.session_state:
    st.session_state.pgn_index = 0

board: chess.Board = st.session_state.board

# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600;700&family=Cormorant+Garamond:wght@400;600;700&family=DM+Sans:wght@300;400;500;600&display=swap');

:root {
    --bg: #0b0c10;
    --surface: #13141a;
    --surface2: #1a1b23;
    --border: #242530;
    --gold: #c9a84c;
    --gold-dim: #8a7434;
    --cyan: #45b7aa;
    --red: #e05555;
    --purple: #9580ff;
    --green: #50fa7b;
    --orange: #ffb86c;
    --text: #e2e0dc;
    --muted: #6b6d7b;
    --piece-font: 2.2rem;
}

.stApp { background: var(--bg); }

/* Hide default streamlit padding */
.block-container { padding-top: 1rem !important; }

h1, h2, h3 {
    font-family: 'Cormorant Garamond', serif !important;
    color: var(--gold) !important;
    letter-spacing: 0.5px;
}

/* ── CHESSBOARD ── */
.chess-grid {
    display: inline-grid;
    grid-template-columns: repeat(8, 1fr);
    border: 3px solid var(--gold-dim);
    border-radius: 4px;
    overflow: hidden;
    box-shadow: 0 8px 32px rgba(0,0,0,0.6), 0 0 60px rgba(201,168,76,0.06);
    max-width: 480px;
    width: 100%;
    aspect-ratio: 1;
}

.sq {
    aspect-ratio: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: clamp(1.4rem, 4vw, 2.6rem);
    cursor: pointer;
    position: relative;
    transition: all 0.15s ease;
    user-select: none;
    -webkit-user-select: none;
    line-height: 1;
}
.sq:hover { filter: brightness(1.2); }

.sq-light { background: #b8a47a; }
.sq-dark { background: #7a6841; }

.sq-selected { box-shadow: inset 0 0 0 3px var(--gold), inset 0 0 12px rgba(201,168,76,0.4); z-index: 2; }
.sq-legal { position: relative; }
.sq-legal::after {
    content: '';
    position: absolute;
    width: 28%;
    height: 28%;
    border-radius: 50%;
    background: rgba(0,0,0,0.25);
}
.sq-capture-target { box-shadow: inset 0 0 0 3px var(--red); }
.sq-lastmove { background: rgba(201,168,76,0.35) !important; }
.sq-check { background: radial-gradient(circle, #e05555 0%, transparent 70%) !important; }
.sq-attack { box-shadow: inset 0 0 0 2px rgba(224,85,85,0.5); }

.coord-label {
    position: absolute;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.55rem;
    color: rgba(0,0,0,0.35);
    font-weight: 600;
}
.coord-file { bottom: 1px; right: 3px; }
.coord-rank { top: 1px; left: 3px; }

/* ── ALGO PANELS ── */
.algo-panel {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.9rem 1.1rem;
    margin-bottom: 0.6rem;
    font-family: 'DM Sans', sans-serif;
}

.algo-bar {
    height: 6px;
    border-radius: 3px;
    margin-top: 0.4rem;
    transition: width 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.metric-pill {
    display: inline-block;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.75rem;
    padding: 2px 10px;
    border-radius: 20px;
    margin: 2px 3px;
    font-weight: 500;
}

.bigo-tag {
    font-family: 'IBM Plex Mono', monospace;
    font-weight: 700;
    font-size: 0.95rem;
    margin-right: 8px;
}

.move-list {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.82rem;
    line-height: 1.8;
    color: var(--text);
    max-height: 200px;
    overflow-y: auto;
    padding: 0.5rem;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 6px;
}

.move-num { color: var(--muted); margin-right: 4px; }
.move-w { color: var(--text); margin-right: 10px; }
.move-b { color: var(--cyan); margin-right: 14px; }

.insight-box {
    background: linear-gradient(135deg, rgba(201,168,76,0.06) 0%, transparent 100%);
    border-left: 3px solid var(--gold);
    padding: 0.8rem 1rem;
    border-radius: 0 6px 6px 0;
    margin: 0.6rem 0;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.88rem;
    color: var(--text);
    line-height: 1.55;
}

.stat-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
    gap: 8px;
    margin: 0.5rem 0;
}

.stat-box {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 0.6rem;
    text-align: center;
}

.stat-val {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.3rem;
    font-weight: 700;
    color: var(--gold);
}

.stat-lbl {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.65rem;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 2px;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# PIECE UNICODE MAP
# ─────────────────────────────────────────────
PIECE_SYMBOLS = {
    (chess.PAWN, True): "♙", (chess.KNIGHT, True): "♘", (chess.BISHOP, True): "♗",
    (chess.ROOK, True): "♖", (chess.QUEEN, True): "♕", (chess.KING, True): "♔",
    (chess.PAWN, False): "♟", (chess.KNIGHT, False): "♞", (chess.BISHOP, False): "♝",
    (chess.ROOK, False): "♜", (chess.QUEEN, False): "♛", (chess.KING, False): "♚",
}


# ─────────────────────────────────────────────
# ALGORITHMS
# ─────────────────────────────────────────────

def simple_eval(b: chess.Board) -> float:
    vals = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3.25, chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}
    s = 0.0
    for sq in chess.SQUARES:
        p = b.piece_at(sq)
        if p:
            s += vals[p.piece_type] * (1 if p.color == chess.WHITE else -1)
    return s


def minimax(b, depth, maximizing):
    if depth == 0 or b.is_game_over():
        return 1, simple_eval(b), None
    moves = list(b.legal_moves)
    total = 0
    best_move = None
    best_val = -99999 if maximizing else 99999
    for m in moves:
        b.push(m)
        ops, val, _ = minimax(b, depth - 1, not maximizing)
        b.pop()
        total += ops + 1
        if maximizing and val > best_val:
            best_val = val
            best_move = m
        elif not maximizing and val < best_val:
            best_val = val
            best_move = m
    return total, best_val, best_move


def alphabeta(b, depth, alpha, beta, maximizing):
    if depth == 0 or b.is_game_over():
        return 1, simple_eval(b), None, 0
    moves = list(b.legal_moves)
    total = 0
    pruned = 0
    best_move = None
    best_val = -99999 if maximizing else 99999
    for i, m in enumerate(moves):
        b.push(m)
        ops, val, _, p = alphabeta(b, depth - 1, alpha, beta, not maximizing)
        b.pop()
        total += ops + 1
        pruned += p
        if maximizing:
            if val > best_val:
                best_val = val
                best_move = m
            alpha = max(alpha, val)
        else:
            if val < best_val:
                best_val = val
                best_move = m
            beta = min(beta, val)
        if beta <= alpha:
            pruned += len(moves) - i - 1
            break
    return total, best_val, best_move, pruned


def run_all_algorithms(b: chess.Board, depth: int) -> Dict:
    """Run all algorithms on the current position and return metrics."""
    legal = list(b.legal_moves)
    n = len(legal)
    results = {}

    # O(1) — hash lookup
    t0 = time.perf_counter()
    _ = hash(b.fen())
    results["O(1)"] = {"ops": 1, "time": time.perf_counter() - t0,
                        "name": "Position Hash", "color": "#50fa7b",
                        "desc": f"Hash the board FEN → always 1 op"}

    # O(log n) — binary search
    sorted_m = sorted(legal, key=lambda m: m.uci())
    t0 = time.perf_counter()
    ops = 0
    if sorted_m:
        target = random.choice(sorted_m).uci()
        lo, hi = 0, len(sorted_m) - 1
        while lo <= hi:
            ops += 1
            mid = (lo + hi) // 2
            if sorted_m[mid].uci() == target: break
            elif sorted_m[mid].uci() < target: lo = mid + 1
            else: hi = mid - 1
    results["O(log n)"] = {"ops": max(ops, 1), "time": time.perf_counter() - t0,
                            "name": "Binary Search", "color": "#45b7aa",
                            "desc": f"Find move in sorted list of {n} → {max(ops,1)} steps"}

    # O(n) — evaluate each move
    t0 = time.perf_counter()
    evals = []
    for m in legal:
        b.push(m)
        evals.append((m, simple_eval(b)))
        b.pop()
    results["O(n)"] = {"ops": n, "time": time.perf_counter() - t0,
                        "name": "Scan All Moves", "color": "#c9a84c",
                        "desc": f"Evaluate each of {n} legal moves once"}

    # O(n log n) — sort moves
    t0 = time.perf_counter()
    comp_count = [0]
    def key_fn(m):
        comp_count[0] += 1
        b.push(m)
        v = simple_eval(b)
        b.pop()
        return v
    sorted(legal, key=key_fn)
    results["O(n log n)"] = {"ops": comp_count[0], "time": time.perf_counter() - t0,
                              "name": "Sort Moves", "color": "#9580ff",
                              "desc": f"Sort {n} moves by eval → {comp_count[0]} comparisons"}

    # O(n²) — pairwise
    t0 = time.perf_counter()
    pair_ops = n * n
    results["O(n²)"] = {"ops": pair_ops, "time": time.perf_counter() - t0,
                          "name": "Pairwise Compare", "color": "#e05555",
                          "desc": f"{n}×{n} = {pair_ops} pair comparisons"}

    # Minimax
    t0 = time.perf_counter()
    mm_ops, mm_val, mm_move = minimax(b, depth, b.turn == chess.WHITE)
    results["Minimax"] = {"ops": mm_ops, "time": time.perf_counter() - t0,
                           "name": f"Minimax (d={depth})", "color": "#ff5555",
                           "desc": f"Full tree: {mm_ops:,} nodes explored",
                           "move": mm_move, "eval": mm_val}

    # Alpha-Beta
    t0 = time.perf_counter()
    ab_ops, ab_val, ab_move, ab_pruned = alphabeta(b, depth, -99999, 99999, b.turn == chess.WHITE)
    savings = (1 - ab_ops / max(mm_ops, 1)) * 100
    results["Alpha-Beta"] = {"ops": ab_ops, "time": time.perf_counter() - t0,
                              "name": f"α-β Pruning (d={depth})", "color": "#50fa7b",
                              "desc": f"{ab_ops:,} nodes, pruned {ab_pruned} branches ({savings:.0f}% saved)",
                              "move": ab_move, "eval": ab_val, "pruned": ab_pruned, "savings": savings}

    return results


# ─────────────────────────────────────────────
# INTERACTIVE BOARD RENDERER (Streamlit buttons)
# ─────────────────────────────────────────────

def render_interactive_board():
    """Render an 8x8 clickable chessboard using st.columns and buttons."""
    b = st.session_state.board
    selected = st.session_state.selected_square
    last_move = st.session_state.move_history[-1] if st.session_state.move_history else None

    # Determine legal destination squares if a piece is selected
    legal_dests = set()
    legal_moves_map = {}
    if selected is not None:
        for m in b.legal_moves:
            if m.from_square == selected:
                legal_dests.add(m.to_square)
                legal_moves_map[m.to_square] = m

    # Check square
    check_sq = None
    if b.is_check():
        check_sq = b.king(b.turn)

    # Render rank labels + board
    for rank in range(7, -1, -1):
        cols = st.columns([0.3] + [1]*8 + [0.3])
        # Rank label
        cols[0].markdown(f"<div style='text-align:center;color:#6b6d7b;font-family:IBM Plex Mono,monospace;font-size:0.8rem;padding-top:0.6rem;'>{rank+1}</div>", unsafe_allow_html=True)

        for file in range(8):
            sq = chess.square(file, rank)
            piece = b.piece_at(sq)
            is_light = (file + rank) % 2 == 1

            # Determine square appearance
            bg = "#b8a47a" if is_light else "#7a6841"
            border = "none"
            extra_style = ""

            if sq == selected:
                bg = "#d4b84c" if is_light else "#a08930"
                border = "2px solid #ffd700"
            elif last_move and sq in (last_move.from_square, last_move.to_square):
                bg = "#c9a84c55"
                bg = "#bfa54a" if is_light else "#8a7230"
            if sq == check_sq:
                bg = "#cc4444"
            if sq in legal_dests:
                if piece:
                    border = "3px solid #e05555"
                else:
                    extra_style = "box-shadow: inset 0 0 0 10px rgba(0,0,0,0.18); border-radius: 50%;"

            # Piece symbol
            symbol = ""
            if piece:
                symbol = PIECE_SYMBOLS.get((piece.piece_type, piece.color), "")

            # Determine label for the dot hint on empty legal squares
            dot = ""
            if sq in legal_dests and not piece:
                dot = "•"

            display = symbol if symbol else dot

            with cols[file + 1]:
                btn_label = display if display else " "
                if st.button(
                    btn_label,
                    key=f"sq_{sq}",
                    use_container_width=True,
                    help=f"{chess.square_name(sq)}",
                ):
                    handle_square_click(sq)
                    st.rerun()

        cols[9].write("")

    # File labels
    file_cols = st.columns([0.3] + [1]*8 + [0.3])
    file_cols[0].write("")
    for f_idx, f_name in enumerate("abcdefgh"):
        file_cols[f_idx + 1].markdown(
            f"<div style='text-align:center;color:#6b6d7b;font-family:IBM Plex Mono,monospace;font-size:0.8rem;'>{f_name}</div>",
            unsafe_allow_html=True
        )


def handle_square_click(sq: int):
    """Handle clicking on a square — select piece or make move."""
    b = st.session_state.board
    selected = st.session_state.selected_square

    if selected is not None:
        # Try to make a move from selected → sq
        move = None
        for m in b.legal_moves:
            if m.from_square == selected and m.to_square == sq:
                # Handle promotion — default to queen
                if m.promotion:
                    move = chess.Move(selected, sq, promotion=chess.QUEEN)
                else:
                    move = m
                break

        if move and move in b.legal_moves:
            make_move(move)
            st.session_state.selected_square = None
            return
        else:
            # Clicking on own piece = reselect
            piece = b.piece_at(sq)
            if piece and piece.color == b.turn:
                st.session_state.selected_square = sq
            else:
                st.session_state.selected_square = None
    else:
        # Select a piece
        piece = b.piece_at(sq)
        if piece and piece.color == b.turn:
            st.session_state.selected_square = sq
        else:
            st.session_state.selected_square = None


def make_move(move: chess.Move):
    """Execute a move and log algorithm data."""
    b = st.session_state.board
    san = b.san(move)
    legal_before = len(list(b.legal_moves))

    b.push(move)

    legal_after = len(list(b.legal_moves))

    st.session_state.move_history.append(move)
    st.session_state.algo_log.append({
        "move": san,
        "legal_before": legal_before,
        "legal_after": legal_after,
        "ply": len(st.session_state.move_history),
    })


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────

def render_sidebar():
    with st.sidebar:
        st.markdown("## ♚ Chess & Big O")
        st.markdown("<div style='color:#6b6d7b;font-family:DM Sans,sans-serif;font-size:0.85rem;margin-bottom:1rem;'>Click pieces to move. Watch algorithms react in real-time.</div>", unsafe_allow_html=True)

        st.markdown("---")

        # Game controls
        st.markdown("### Controls")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔄 New Game", use_container_width=True):
                st.session_state.board = chess.Board()
                st.session_state.selected_square = None
                st.session_state.move_history = []
                st.session_state.algo_log = []
                st.session_state.pgn_loaded = False
                st.rerun()
        with c2:
            if st.button("↩️ Undo", use_container_width=True):
                if st.session_state.move_history:
                    st.session_state.board.pop()
                    st.session_state.move_history.pop()
                    if st.session_state.algo_log:
                        st.session_state.algo_log.pop()
                    st.session_state.selected_square = None
                    st.rerun()

        st.markdown("---")

        # Engine
        st.markdown("### Engine Settings")
        st.session_state.engine_depth = st.slider("Search Depth", 1, 4, 3, help="Higher = slower but shows more Big O impact")

        if st.button("🤖 Engine Move", use_container_width=True, type="primary"):
            engine_move()

        st.session_state.auto_engine = st.checkbox("Auto-reply as Black", value=st.session_state.auto_engine)

        st.markdown("---")

        # Load PGN
        st.markdown("### Load PGN")
        pgn_choice = st.selectbox("Sample Games", [
            "— Select —",
            "Kasparov vs Deep Blue G6 (1997)",
            "Immortal Game (1851)",
            "Opera Game (1858)",
        ])

        PGNS = {
            "Kasparov vs Deep Blue G6 (1997)": '[Event "IBM"]\n[White "Deep Blue"]\n[Black "Kasparov"]\n[Result "1-0"]\n\n1. e4 c6 2. d4 d5 3. Nc3 dxe4 4. Nxe4 Nd7 5. Ng5 Ngf6 6. Bd3 e6 7. N1f3 h6 8. Nxe6 Qe7 9. O-O fxe6 10. Bg6+ Kd8 11. Bf4 b5 12. a4 Bb7 13. Re1 Nd5 14. Bg3 Kc8 15. axb5 cxb5 16. Qd3 Bc6 17. Bf5 exf5 18. Rxe7 Bxe7 19. c4 1-0',
            "Immortal Game (1851)": '[Event "London"]\n[White "Anderssen"]\n[Black "Kieseritzky"]\n[Result "1-0"]\n\n1. e4 e5 2. f4 exf4 3. Bc4 Qh4+ 4. Kf1 b5 5. Bxb5 Nf6 6. Nf3 Qh6 7. d3 Nh5 8. Nh4 Qg5 9. Nf5 c6 10. g4 Nf6 11. Rg1 cxb5 12. h4 Qg6 13. h5 Qg5 14. Qf3 Ng8 15. Bxf4 Qf6 16. Nc3 Bc5 17. Nd5 Qxb2 18. Bd6 Bxg1 19. e5 Qxa1+ 20. Ke2 Na6 21. Nxg7+ Kd8 22. Qf6+ Nxf6 23. Be7# 1-0',
            "Opera Game (1858)": '[Event "Opera"]\n[White "Morphy"]\n[Black "Allies"]\n[Result "1-0"]\n\n1. e4 e5 2. Nf3 d6 3. d4 Bg4 4. dxe5 Bxf3 5. Qxf3 dxe5 6. Bc4 Nf6 7. Qb3 Qe7 8. Nc3 c6 9. Bg5 b5 10. Nxb5 cxb5 11. Bxb5+ Nbd7 12. O-O-O Rd8 13. Rxd7 Rxd7 14. Rd1 Qe6 15. Bxd7+ Nxd7 16. Qb8+ Nxb8 17. Rd8# 1-0',
        }

        if pgn_choice != "— Select —":
            if st.button("📥 Load Game", use_container_width=True):
                load_pgn(PGNS[pgn_choice])

        custom_pgn = st.text_area("Or paste PGN:", height=100, placeholder="1. e4 e5 2. Nf3 ...")
        if custom_pgn.strip() and st.button("📥 Load Custom PGN", use_container_width=True):
            load_pgn(custom_pgn)

        if st.session_state.pgn_loaded:
            st.markdown("---")
            st.markdown("### PGN Playback")
            total = len(st.session_state.pgn_moves)
            idx = st.slider("Move", 0, total, st.session_state.pgn_index, key="pgn_slider")
            if idx != st.session_state.pgn_index:
                navigate_pgn(idx)
            pc1, pc2, pc3 = st.columns(3)
            with pc1:
                if st.button("⏮", use_container_width=True):
                    navigate_pgn(0)
            with pc2:
                if st.button("⏭", use_container_width=True):
                    navigate_pgn(total)
            with pc3:
                if st.button("▶ Next", use_container_width=True):
                    navigate_pgn(min(st.session_state.pgn_index + 1, total))

        st.markdown("---")
        st.markdown("### Position Setup")
        fen = st.text_input("Load FEN:", placeholder="rnbqkbnr/pppppppp/...")
        if fen.strip() and st.button("Load FEN", use_container_width=True):
            try:
                st.session_state.board = chess.Board(fen.strip())
                st.session_state.selected_square = None
                st.session_state.move_history = []
                st.session_state.algo_log = []
                st.rerun()
            except ValueError:
                st.error("Invalid FEN")


def load_pgn(pgn_text: str):
    """Load a PGN game for step-through playback."""
    try:
        game = chess.pgn.read_game(io.StringIO(pgn_text))
        if game:
            moves = list(game.mainline_moves())
            st.session_state.pgn_moves = moves
            st.session_state.pgn_index = 0
            st.session_state.pgn_loaded = True
            st.session_state.board = chess.Board()
            st.session_state.move_history = []
            st.session_state.algo_log = []
            st.session_state.selected_square = None
            st.rerun()
    except Exception as e:
        st.error(f"PGN error: {e}")


def navigate_pgn(target_idx: int):
    """Navigate to a specific move in the PGN."""
    st.session_state.board = chess.Board()
    st.session_state.move_history = []
    st.session_state.algo_log = []
    for i, m in enumerate(st.session_state.pgn_moves[:target_idx]):
        b = st.session_state.board
        san = b.san(m)
        legal_before = len(list(b.legal_moves))
        b.push(m)
        legal_after = len(list(b.legal_moves))
        st.session_state.move_history.append(m)
        st.session_state.algo_log.append({
            "move": san, "legal_before": legal_before,
            "legal_after": legal_after, "ply": i + 1,
        })
    st.session_state.pgn_index = target_idx
    st.session_state.selected_square = None
    st.rerun()


def engine_move():
    """Make a move using alpha-beta search."""
    b = st.session_state.board
    if b.is_game_over():
        return
    depth = st.session_state.engine_depth
    _, _, move, _ = alphabeta(b, depth, -99999, 99999, b.turn == chess.WHITE)
    if move:
        make_move(move)
        st.rerun()


# ─────────────────────────────────────────────
# RIGHT PANEL — ALGORITHM VISUALIZATION
# ─────────────────────────────────────────────

def render_algo_panel():
    """Show real-time algorithm metrics for the current position."""
    b = st.session_state.board
    n = len(list(b.legal_moves))
    depth = st.session_state.engine_depth

    # Status
    turn = "White" if b.turn == chess.WHITE else "Black"
    status = f"**{turn} to move**"
    if b.is_checkmate():
        status = "**Checkmate!** " + ("Black wins" if b.turn == chess.WHITE else "White wins")
    elif b.is_stalemate():
        status = "**Stalemate** — Draw"
    elif b.is_check():
        status = f"**{turn} is in check!**"

    st.markdown(status)

    # Key stats
    st.markdown(f"""
    <div class="stat-grid">
        <div class="stat-box"><div class="stat-val">{n}</div><div class="stat-lbl">Legal Moves</div></div>
        <div class="stat-box"><div class="stat-val">{simple_eval(b):+.1f}</div><div class="stat-lbl">Material</div></div>
        <div class="stat-box"><div class="stat-val">{len(st.session_state.move_history)}</div><div class="stat-lbl">Ply</div></div>
        <div class="stat-box"><div class="stat-val">{n**depth:,}</div><div class="stat-lbl">Tree Size (d={depth})</div></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Run algorithms button
    if st.button("⚡ Analyze Position — See Big O in Action", use_container_width=True, type="primary"):
        if b.is_game_over():
            st.warning("Game is over!")
            return

        with st.spinner("Running algorithms..."):
            results = run_all_algorithms(b, depth)

        st.session_state["last_results"] = results

    # Display results
    if "last_results" in st.session_state:
        results = st.session_state["last_results"]
        max_ops = max(r["ops"] for r in results.values())

        st.markdown("### Algorithm Comparison")
        st.markdown(f"""
        <div class="insight-box">
            Each algorithm solves a different chess sub-problem. Notice how operations
            explode from <b>O(1)</b> (1 op) to <b>Minimax</b> ({results['Minimax']['ops']:,} ops)
            — that's the power of Big O!
        </div>
        """, unsafe_allow_html=True)

        for key in ["O(1)", "O(log n)", "O(n)", "O(n log n)", "O(n²)", "Minimax", "Alpha-Beta"]:
            r = results[key]
            pct = min((r["ops"] / max(max_ops, 1)) * 100, 100)

            st.markdown(f"""
            <div class="algo-panel">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <span class="bigo-tag" style="color:{r['color']};">{key}</span>
                        <span style="color:#6b6d7b;font-size:0.8rem;">{r['name']}</span>
                    </div>
                    <div>
                        <span class="metric-pill" style="background:{r['color']}22;color:{r['color']};">{r['ops']:,} ops</span>
                        <span class="metric-pill" style="background:#1a1b23;color:#6b6d7b;">{r['time']*1000:.2f}ms</span>
                    </div>
                </div>
                <div style="color:#6b6d7b;font-size:0.78rem;margin-top:4px;">{r['desc']}</div>
                <div class="algo-bar" style="width:{max(pct, 0.5)}%;background:{r['color']};"></div>
            </div>
            """, unsafe_allow_html=True)

        # Highlight the pruning savings
        mm = results["Minimax"]["ops"]
        ab = results["Alpha-Beta"]["ops"]
        pruned = results["Alpha-Beta"].get("pruned", 0)
        savings = results["Alpha-Beta"].get("savings", 0)

        st.markdown(f"""
        <div class="insight-box">
            <b>🌿 Alpha-Beta Pruning Impact:</b><br>
            Minimax explored <b>{mm:,}</b> nodes. Alpha-Beta needed only <b>{ab:,}</b> nodes
            by cutting <b>{pruned}</b> branches — a <b>{savings:.1f}%</b> reduction.<br><br>
            This is why chess engines are possible: pruning transforms O(bᵈ) ≈ O({n}^{depth}) = {n**depth:,}
            toward O(b^(d/2)) ≈ {int(n**(depth/2)):,} in the best case.
        </div>
        """, unsafe_allow_html=True)

    # Move history
    st.markdown("---")
    st.markdown("### Move History")
    if st.session_state.algo_log:
        html_moves = ""
        for i, entry in enumerate(st.session_state.algo_log):
            ply = entry["ply"]
            if ply % 2 == 1:
                html_moves += f'<span class="move-num">{(ply+1)//2}.</span>'
                html_moves += f'<span class="move-w">{entry["move"]}</span>'
            else:
                html_moves += f'<span class="move-b">{entry["move"]}</span> '

        st.markdown(f'<div class="move-list">{html_moves}</div>', unsafe_allow_html=True)

        # Branching factor chart
        if len(st.session_state.algo_log) > 1:
            import pandas as pd
            bf_data = pd.DataFrame({
                "Move": [e["ply"] for e in st.session_state.algo_log],
                "Legal Moves": [e["legal_before"] for e in st.session_state.algo_log],
            }).set_index("Move")
            st.markdown("#### Branching Factor per Move")
            st.area_chart(bf_data, color="#c9a84c", height=150)
    else:
        st.markdown("<div style='color:#6b6d7b;font-size:0.85rem;'>No moves yet. Click a piece to start!</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# MAIN LAYOUT
# ─────────────────────────────────────────────

def main():
    render_sidebar()

    st.markdown("""
    <div style="text-align:center;margin-bottom:0.3rem;">
        <span style="font-family:'Cormorant Garamond',serif;font-size:2.2rem;font-weight:700;
            background:linear-gradient(135deg,#c9a84c,#f0d78c,#c9a84c);
            -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
            ♚ Chess & Big O Explorer
        </span>
        <div style="font-family:'IBM Plex Mono',monospace;font-size:0.78rem;color:#6b6d7b;letter-spacing:3px;margin-top:2px;">
            CLICK PIECES · MAKE MOVES · SEE ALGORITHMS
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_board, col_algo = st.columns([1, 1], gap="large")

    with col_board:
        st.markdown("### Board")
        render_interactive_board()

        # Quick info below board
        b = st.session_state.board
        if b.is_game_over():
            if b.is_checkmate():
                winner = "Black" if b.turn == chess.WHITE else "White"
                st.success(f"♔ Checkmate! {winner} wins!")
            elif b.is_stalemate():
                st.info("Draw by stalemate")
            elif b.is_insufficient_material():
                st.info("Draw — insufficient material")
            else:
                st.info("Game over — draw")

        # Auto engine reply
        if st.session_state.auto_engine and b.turn == chess.BLACK and not b.is_game_over():
            time.sleep(0.3)
            engine_move()

    with col_algo:
        st.markdown("### Algorithm Dashboard")
        render_algo_panel()


main()
