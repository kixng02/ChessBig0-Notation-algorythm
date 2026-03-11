"""
♚ Chess & Big O Notation Explorer ♚
A Streamlit app that visualizes algorithmic complexity through chess.
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
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional
from collections import defaultdict

# ─────────────────────────────────────────────
# Page Config
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Chess & Big O Explorer",
    page_icon="♚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# Custom CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;700&family=Playfair+Display:wght@400;700;900&family=Source+Sans+3:wght@300;400;600&display=swap');

:root {
    --bg-dark: #0a0a0f;
    --bg-card: #12121a;
    --accent-gold: #d4a843;
    --accent-cyan: #4ecdc4;
    --accent-red: #ff6b6b;
    --accent-purple: #a78bfa;
    --accent-green: #34d399;
    --text-primary: #e8e6e3;
    --text-muted: #8a8a9a;
    --border-subtle: #1e1e2e;
}

.stApp {
    background: linear-gradient(170deg, #0a0a0f 0%, #0f0f1a 40%, #0a0f14 100%);
}

h1, h2, h3 {
    font-family: 'Playfair Display', serif !important;
    color: var(--accent-gold) !important;
}

.main-title {
    font-family: 'Playfair Display', serif;
    font-size: 2.8rem;
    font-weight: 900;
    text-align: center;
    background: linear-gradient(135deg, #d4a843 0%, #f0d78c 50%, #d4a843 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0;
    letter-spacing: 2px;
}

.subtitle {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.95rem;
    text-align: center;
    color: var(--text-muted);
    margin-top: 0.2rem;
    margin-bottom: 2rem;
    letter-spacing: 3px;
}

.bigo-card {
    background: linear-gradient(135deg, #12121a 0%, #1a1a2e 100%);
    border: 1px solid #1e1e2e;
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    margin-bottom: 1rem;
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
}

.bigo-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 4px;
    height: 100%;
    border-radius: 4px 0 0 4px;
}

.bigo-card.o1::before { background: var(--accent-green); }
.bigo-card.ologn::before { background: var(--accent-cyan); }
.bigo-card.on::before { background: var(--accent-gold); }
.bigo-card.onlogn::before { background: var(--accent-purple); }
.bigo-card.on2::before { background: var(--accent-red); }
.bigo-card.on3::before { background: #ff4444; }
.bigo-card.oexp::before { background: #ff0066; }

.bigo-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.4rem;
    font-weight: 700;
    margin-bottom: 0.3rem;
}

.bigo-name {
    font-family: 'Source Sans 3', sans-serif;
    font-size: 0.85rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 1.5px;
}

.bigo-desc {
    font-family: 'Source Sans 3', sans-serif;
    font-size: 0.9rem;
    color: var(--text-primary);
    margin-top: 0.5rem;
    line-height: 1.5;
}

.metric-box {
    background: linear-gradient(135deg, #12121a 0%, #1a1a2e 100%);
    border: 1px solid #1e1e2e;
    border-radius: 10px;
    padding: 1rem 1.2rem;
    text-align: center;
}

.metric-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.8rem;
    font-weight: 700;
    color: var(--accent-gold);
}

.metric-label {
    font-family: 'Source Sans 3', sans-serif;
    font-size: 0.75rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-top: 0.2rem;
}

.algo-highlight {
    font-family: 'JetBrains Mono', monospace;
    background: rgba(78, 205, 196, 0.1);
    border: 1px solid rgba(78, 205, 196, 0.2);
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.85rem;
    color: var(--accent-cyan);
}

.chess-insight {
    background: linear-gradient(135deg, rgba(212, 168, 67, 0.05) 0%, rgba(212, 168, 67, 0.02) 100%);
    border-left: 3px solid var(--accent-gold);
    padding: 1rem 1.2rem;
    border-radius: 0 8px 8px 0;
    margin: 1rem 0;
    font-family: 'Source Sans 3', sans-serif;
    color: var(--text-primary);
    line-height: 1.6;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
}

.stTabs [data-baseweb="tab"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.85rem;
    letter-spacing: 0.5px;
}

div[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a0a0f 0%, #0f0f1a 100%);
    border-right: 1px solid #1e1e2e;
}

.board-container {
    display: flex;
    justify-content: center;
    margin: 1rem 0;
}

/* Fix code block styling */
code {
    font-family: 'JetBrains Mono', monospace !important;
}

</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Data Structures & Chess Algorithms
# ─────────────────────────────────────────────

@dataclass
class AlgorithmProfile:
    name: str
    complexity: str
    css_class: str
    color: str
    description: str
    chess_analogy: str
    example_ops: str


ALGORITHMS = {
    "O(1)": AlgorithmProfile(
        name="Constant Time",
        complexity="O(1)",
        css_class="o1",
        color="#34d399",
        description="Operations that take the same time regardless of input size.",
        chess_analogy="Checking if a square is occupied on a bitboard — one operation, always.",
        example_ops="Hash table lookup for transposition table entries",
    ),
    "O(log n)": AlgorithmProfile(
        name="Logarithmic",
        complexity="O(log n)",
        css_class="ologn",
        color="#4ecdc4",
        description="Halving the problem space each step — incredibly efficient.",
        chess_analogy="Binary search through a sorted opening book to find the current position.",
        example_ops="Opening book lookup via binary search",
    ),
    "O(n)": AlgorithmProfile(
        name="Linear",
        complexity="O(n)",
        css_class="on",
        color="#d4a843",
        description="Time grows proportionally with input size.",
        chess_analogy="Scanning all pieces to generate legal moves — check each piece once.",
        example_ops="Iterating over all 32 pieces to compute material balance",
    ),
    "O(n log n)": AlgorithmProfile(
        name="Linearithmic",
        complexity="O(n log n)",
        css_class="onlogn",
        color="#a78bfa",
        description="Slightly more than linear — the sweet spot for comparison-based sorting.",
        chess_analogy="Sorting candidate moves by evaluation score using merge sort.",
        example_ops="Sorting moves by heuristic value for move ordering",
    ),
    "O(n²)": AlgorithmProfile(
        name="Quadratic",
        complexity="O(n²)",
        css_class="on2",
        color="#ff6b6b",
        description="Nested iterations — every element compared with every other.",
        chess_analogy="Checking every piece against every square for attack patterns.",
        example_ops="Naive attack table generation: piece × square",
    ),
    "O(n³)": AlgorithmProfile(
        name="Cubic",
        complexity="O(n³)",
        css_class="on3",
        color="#ff4444",
        description="Triple nested loops — complexity escalates fast.",
        chess_analogy="Evaluating piece interactions across multiple board dimensions.",
        example_ops="Matrix-based positional analysis",
    ),
    "O(bᵈ)": AlgorithmProfile(
        name="Exponential (Game Tree)",
        complexity="O(bᵈ)",
        css_class="oexp",
        color="#ff0066",
        description="The branching factor b raised to depth d — the core challenge of chess engines.",
        chess_analogy="Full minimax search: ~35 legal moves per position, 40+ moves deep = 35⁴⁰ nodes!",
        example_ops="Minimax without pruning (b≈35, depth d)",
    ),
}


def render_board_svg(board: chess.Board, last_move=None, size=350) -> str:
    """Render chess board as SVG with custom styling."""
    kwargs = {"size": size, "coordinates": True}
    if last_move:
        kwargs["lastmove"] = last_move
    # Highlight check
    if board.is_check():
        kwargs["check"] = board.king(board.turn)
    svg = chess.svg.board(board, **kwargs)
    # Custom colors
    svg = svg.replace("#ffce9e", "#b8860b44")  # light squares
    svg = svg.replace("#d18b47", "#8b6914aa")  # dark squares
    return svg


def svg_to_html(svg_str: str) -> str:
    """Wrap SVG in centered HTML container."""
    b64 = base64.b64encode(svg_str.encode()).decode()
    return f'<div class="board-container"><img src="data:image/svg+xml;base64,{b64}" /></div>'


# ─────────────────────────────────────────────
# Algorithm Simulations for Chess
# ─────────────────────────────────────────────

def simulate_move_search(board: chess.Board, depth: int) -> Dict:
    """Simulate different search algorithms and measure operations."""
    legal_moves = list(board.legal_moves)
    n = len(legal_moves)
    results = {}

    # O(1) — Transposition table hit (simulated)
    start = time.perf_counter()
    _ = hash(board.fen())  # constant-time hash
    results["O(1)"] = {
        "ops": 1,
        "time": time.perf_counter() - start,
        "label": "Transposition Lookup",
        "detail": "Hash the position FEN → 1 operation"
    }

    # O(log n) — Binary search in sorted move list
    sorted_moves = sorted(legal_moves, key=lambda m: m.uci())
    start = time.perf_counter()
    ops = 0
    target = random.choice(sorted_moves).uci() if sorted_moves else ""
    lo, hi = 0, len(sorted_moves) - 1
    while lo <= hi:
        ops += 1
        mid = (lo + hi) // 2
        if sorted_moves[mid].uci() == target:
            break
        elif sorted_moves[mid].uci() < target:
            lo = mid + 1
        else:
            hi = mid - 1
    results["O(log n)"] = {
        "ops": ops,
        "time": time.perf_counter() - start,
        "label": "Binary Search (sorted moves)",
        "detail": f"Search through {n} sorted moves → {ops} comparisons"
    }

    # O(n) — Linear scan of all moves
    start = time.perf_counter()
    ops = 0
    for move in legal_moves:
        ops += 1
        board.push(move)
        _ = simple_eval(board)
        board.pop()
    results["O(n)"] = {
        "ops": ops,
        "time": time.perf_counter() - start,
        "label": "Linear Move Evaluation",
        "detail": f"Evaluate each of {n} moves once → {ops} evaluations"
    }

    # O(n log n) — Sort moves by evaluation
    start = time.perf_counter()
    ops_count = [0]
    def eval_key(m):
        ops_count[0] += 1
        board.push(m)
        v = simple_eval(board)
        board.pop()
        return v
    sorted_by_eval = sorted(legal_moves, key=eval_key)
    results["O(n log n)"] = {
        "ops": ops_count[0],
        "time": time.perf_counter() - start,
        "label": "Move Ordering (Sort by eval)",
        "detail": f"Sort {n} moves → ~{ops_count[0]} comparisons"
    }

    # O(n²) — Compare every pair of moves
    start = time.perf_counter()
    ops = 0
    for i, m1 in enumerate(legal_moves):
        for j, m2 in enumerate(legal_moves):
            ops += 1
            if ops > 5000:
                break
        if ops > 5000:
            break
    results["O(n²)"] = {
        "ops": min(n * n, 5000),
        "time": time.perf_counter() - start,
        "label": "Pairwise Move Comparison",
        "detail": f"{n} moves × {n} moves = {n*n} comparisons"
    }

    # O(bᵈ) — Minimax tree (simulated count)
    b = min(n, 35)
    d = min(depth, 5)
    start = time.perf_counter()
    minimax_ops, _ = minimax_count(board, d, False)
    results["O(bᵈ)"] = {
        "ops": minimax_ops,
        "time": time.perf_counter() - start,
        "label": f"Minimax Search (depth={d})",
        "detail": f"b≈{b}, d={d} → theoretical {b}^{d}={b**d:,} nodes"
    }

    # Alpha-Beta pruning comparison
    start = time.perf_counter()
    ab_ops, _ = alphabeta_count(board, d, -99999, 99999, True)
    results["Alpha-Beta"] = {
        "ops": ab_ops,
        "time": time.perf_counter() - start,
        "label": f"Alpha-Beta Pruning (depth={d})",
        "detail": f"Pruned search: {ab_ops:,} nodes vs {minimax_ops:,} minimax"
    }

    return results


def simple_eval(board: chess.Board) -> float:
    """Simple material evaluation."""
    piece_values = {
        chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3.25,
        chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0
    }
    score = 0.0
    for sq in chess.SQUARES:
        piece = board.piece_at(sq)
        if piece:
            val = piece_values.get(piece.piece_type, 0)
            score += val if piece.color == chess.WHITE else -val
    return score


def minimax_count(board: chess.Board, depth: int, maximizing: bool) -> Tuple[int, float]:
    """Minimax with operation counting (capped for performance)."""
    if depth == 0 or board.is_game_over():
        return 1, simple_eval(board)

    total_ops = 0
    moves = list(board.legal_moves)[:15]  # Cap branching for performance

    if maximizing:
        best = -99999.0
        for move in moves:
            board.push(move)
            ops, val = minimax_count(board, depth - 1, False)
            board.pop()
            total_ops += ops + 1
            best = max(best, val)
        return total_ops, best
    else:
        best = 99999.0
        for move in moves:
            board.push(move)
            ops, val = minimax_count(board, depth - 1, True)
            board.pop()
            total_ops += ops + 1
            best = min(best, val)
        return total_ops, best


def alphabeta_count(board: chess.Board, depth: int, alpha: float, beta: float, maximizing: bool) -> Tuple[int, float]:
    """Alpha-Beta pruning with operation counting."""
    if depth == 0 or board.is_game_over():
        return 1, simple_eval(board)

    total_ops = 0
    moves = list(board.legal_moves)[:15]

    if maximizing:
        best = -99999.0
        for move in moves:
            board.push(move)
            ops, val = alphabeta_count(board, depth - 1, alpha, beta, False)
            board.pop()
            total_ops += ops + 1
            best = max(best, val)
            alpha = max(alpha, val)
            if beta <= alpha:
                break  # Prune!
        return total_ops, best
    else:
        best = 99999.0
        for move in moves:
            board.push(move)
            ops, val = alphabeta_count(board, depth - 1, alpha, beta, True)
            board.pop()
            total_ops += ops + 1
            best = min(best, val)
            beta = min(beta, val)
            if beta <= alpha:
                break  # Prune!
        return total_ops, best


def analyze_pgn_complexity(pgn_text: str) -> Optional[Dict]:
    """Analyze a PGN game and measure complexity at each move."""
    try:
        pgn_io = io.StringIO(pgn_text)
        game = chess.pgn.read_game(pgn_io)
        if game is None:
            return None

        analysis = {
            "headers": dict(game.headers),
            "moves": [],
            "branching_factors": [],
            "cumulative_tree_size": [],
            "total_positions": 0,
        }

        board = game.board()
        cumulative = 0
        for i, move in enumerate(game.mainline_moves()):
            legal_count = len(list(board.legal_moves))
            cumulative += legal_count

            analysis["moves"].append({
                "move_num": i + 1,
                "san": board.san(move),
                "uci": move.uci(),
                "legal_moves": legal_count,
                "fen": board.fen(),
                "is_capture": board.is_capture(move),
                "is_check": board.gives_check(move),
            })
            analysis["branching_factors"].append(legal_count)
            analysis["cumulative_tree_size"].append(cumulative)

            board.push(move)

        analysis["total_positions"] = cumulative
        analysis["result"] = game.headers.get("Result", "*")
        return analysis

    except Exception as e:
        st.error(f"Error parsing PGN: {e}")
        return None


# ─────────────────────────────────────────────
# Sample PGN Games
# ─────────────────────────────────────────────

SAMPLE_GAMES = {
    "Kasparov vs Deep Blue (1997, Game 6)": """[Event "IBM Man-Machine"]
[Site "New York"]
[Date "1997.05.11"]
[White "Deep Blue"]
[Black "Kasparov, Garry"]
[Result "1-0"]

1. e4 c6 2. d4 d5 3. Nc3 dxe4 4. Nxe4 Nd7 5. Ng5 Ngf6 6. Bd3 e6
7. N1f3 h6 8. Nxe6 Qe7 9. O-O fxe6 10. Bg6+ Kd8 11. Bf4 b5
12. a4 Bb7 13. Re1 Nd5 14. Bg3 Kc8 15. axb5 cxb5 16. Qd3 Bc6
17. Bf5 exf5 18. Rxe7 Bxe7 19. c4 1-0""",

    "Immortal Game (Anderssen vs Kieseritzky, 1851)": """[Event "London"]
[Site "London"]
[Date "1851.06.21"]
[White "Anderssen, Adolf"]
[Black "Kieseritzky, Lionel"]
[Result "1-0"]

1. e4 e5 2. f4 exf4 3. Bc4 Qh4+ 4. Kf1 b5 5. Bxb5 Nf6 6. Nf3 Qh6
7. d3 Nh5 8. Nh4 Qg5 9. Nf5 c6 10. g4 Nf6 11. Rg1 cxb5 12. h4 Qg6
13. h5 Qg5 14. Qf3 Ng8 15. Bxf4 Qf6 16. Nc3 Bc5 17. Nd5 Qxb2
18. Bd6 Bxg1 19. e5 Qxa1+ 20. Ke2 Na6 21. Nxg7+ Kd8 22. Qf6+ Nxf6
23. Be7# 1-0""",

    "Short Draw (Berlin Defense)": """[Event "Example"]
[Site "Internet"]
[Date "2024.01.01"]
[White "Player A"]
[Black "Player B"]
[Result "1/2-1/2"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 Nf6 4. O-O Nxe4 5. d4 Nd6 6. Bxc6 dxc6
7. dxe5 Nf5 8. Qxd8+ Kxd8 1/2-1/2""",
}


# ─────────────────────────────────────────────
# UI Components
# ─────────────────────────────────────────────

def render_header():
    st.markdown('<div class="main-title">♚ Chess & Big O Explorer</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">ALGORITHMIC COMPLEXITY THROUGH THE LENS OF CHESS</div>', unsafe_allow_html=True)


def render_bigo_reference():
    """Render the Big O reference cards."""
    st.markdown("### 📐 Big O Complexity Reference")
    for key, algo in ALGORITHMS.items():
        st.markdown(f"""
        <div class="bigo-card {algo.css_class}">
            <div class="bigo-label" style="color: {algo.color};">{algo.complexity}</div>
            <div class="bigo-name">{algo.name}</div>
            <div class="bigo-desc">{algo.description}</div>
            <div class="chess-insight">♟ <b>Chess:</b> {algo.chess_analogy}</div>
        </div>
        """, unsafe_allow_html=True)


def render_complexity_chart(results: Dict):
    """Render operations comparison chart using Streamlit's native charting."""
    import pandas as pd

    chart_data = []
    for key in ["O(1)", "O(log n)", "O(n)", "O(n log n)", "O(n²)", "O(bᵈ)", "Alpha-Beta"]:
        if key in results:
            chart_data.append({
                "Algorithm": key,
                "Operations": results[key]["ops"],
                "Time (μs)": results[key]["time"] * 1_000_000,
            })

    df = pd.DataFrame(chart_data)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Operations Count")
        st.bar_chart(df.set_index("Algorithm")["Operations"], color="#d4a843")
    with col2:
        st.markdown("#### Execution Time (μs)")
        st.bar_chart(df.set_index("Algorithm")["Time (μs)"], color="#4ecdc4")


def render_growth_comparison():
    """Show how different complexities grow with input size."""
    import pandas as pd

    st.markdown("### 📈 Growth Rate Comparison")
    st.markdown("""
    <div class="chess-insight">
    See how the number of operations scales as the number of chess pieces/moves (n) increases.
    In chess, n might represent legal moves (~20-40), pieces on the board (up to 32),
    or search depth. The exponential growth of the game tree is why chess engines need
    clever pruning algorithms!
    </div>
    """, unsafe_allow_html=True)

    max_n = st.slider("Maximum n (input size)", 5, 60, 30)

    data = []
    for n in range(1, max_n + 1):
        row = {
            "n": n,
            "O(1)": 1,
            "O(log n)": math.log2(max(n, 1)),
            "O(n)": n,
            "O(n log n)": n * math.log2(max(n, 1)),
            "O(n²)": n ** 2,
        }
        if n <= 20:
            row["O(2ⁿ)"] = 2 ** n
        data.append(row)

    df = pd.DataFrame(data).set_index("n")
    st.line_chart(df, color=["#34d399", "#4ecdc4", "#d4a843", "#a78bfa", "#ff6b6b", "#ff0066"][:len(df.columns)])

    # Concrete chess numbers
    st.markdown("#### 🔢 Concrete Chess Numbers")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown("""<div class="metric-box">
            <div class="metric-value">35</div>
            <div class="metric-label">Avg. Branching Factor</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown("""<div class="metric-box">
            <div class="metric-value">10⁴⁷</div>
            <div class="metric-label">Shannon Number (game-tree)</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown("""<div class="metric-box">
            <div class="metric-value">10⁴⁴</div>
            <div class="metric-label">Legal Positions Est.</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown("""<div class="metric-box">
            <div class="metric-value">~80</div>
            <div class="metric-label">Avg. Moves Per Game</div>
        </div>""", unsafe_allow_html=True)


def render_live_analysis():
    """Interactive board with live algorithm analysis."""
    st.markdown("### ⚡ Live Position Analysis")
    st.markdown("""
    <div class="chess-insight">
    Set up a position and watch different algorithms work on it in real-time.
    Adjust the search depth to see how exponential complexity explodes!
    </div>
    """, unsafe_allow_html=True)

    col_board, col_controls = st.columns([1, 1])

    with col_controls:
        fen_input = st.text_input(
            "FEN Position",
            value="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            help="Enter a valid FEN string or use the starting position"
        )

        depth = st.slider("Search Depth", 1, 4, 2, help="⚠️ Higher depths take exponentially longer!")

        preset = st.selectbox("Or choose a preset position:", [
            "Starting Position",
            "Middle Game (complex)",
            "Endgame (simple)",
            "Tactical Position",
        ])

        presets = {
            "Starting Position": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            "Middle Game (complex)": "r1bq1rk1/pp2bppp/2n1pn2/2pp4/3P4/2NBPN2/PPP2PPP/R1BQ1RK1 w - - 0 8",
            "Endgame (simple)": "8/5pk1/8/8/8/8/5PK1/4R3 w - - 0 1",
            "Tactical Position": "r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 0 4",
        }

        if preset != "Starting Position" or fen_input == presets["Starting Position"]:
            fen_input = presets[preset]

    try:
        board = chess.Board(fen_input)
    except ValueError:
        st.error("Invalid FEN string!")
        return

    with col_board:
        svg = render_board_svg(board, size=380)
        st.markdown(svg_to_html(svg), unsafe_allow_html=True)

        legal_count = len(list(board.legal_moves))
        mc1, mc2, mc3 = st.columns(3)
        with mc1:
            st.markdown(f"""<div class="metric-box">
                <div class="metric-value">{legal_count}</div>
                <div class="metric-label">Legal Moves</div>
            </div>""", unsafe_allow_html=True)
        with mc2:
            mat = simple_eval(board)
            st.markdown(f"""<div class="metric-box">
                <div class="metric-value">{mat:+.1f}</div>
                <div class="metric-label">Material Eval</div>
            </div>""", unsafe_allow_html=True)
        with mc3:
            phase = "Opening" if board.fullmove_number < 10 else "Middle" if board.fullmove_number < 30 else "Endgame"
            st.markdown(f"""<div class="metric-box">
                <div class="metric-value">{phase}</div>
                <div class="metric-label">Game Phase</div>
            </div>""", unsafe_allow_html=True)

    # Run analysis
    if st.button("🔍 Run Algorithm Analysis", type="primary", use_container_width=True):
        with st.spinner("Running algorithms..."):
            results = simulate_move_search(board, depth)

        # Results table
        st.markdown("#### 📊 Algorithm Comparison Results")

        for key in ["O(1)", "O(log n)", "O(n)", "O(n log n)", "O(n²)", "O(bᵈ)", "Alpha-Beta"]:
            if key in results:
                r = results[key]
                algo = ALGORITHMS.get(key, None)
                color = algo.color if algo else "#4ecdc4"
                st.markdown(f"""
                <div class="bigo-card {algo.css_class if algo else ''}">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <span class="bigo-label" style="color:{color};">{key}</span>
                            <span class="bigo-name" style="margin-left:12px;">{r['label']}</span>
                        </div>
                        <div style="text-align:right;">
                            <span style="font-family:'JetBrains Mono',monospace; font-size:1.2rem; color:{color};">{r['ops']:,}</span>
                            <span style="color:#8a8a9a; font-size:0.8rem; margin-left:6px;">ops</span>
                            <span style="color:#8a8a9a; font-size:0.75rem; margin-left:12px;">({r['time']*1000:.2f} ms)</span>
                        </div>
                    </div>
                    <div style="color:#8a8a9a; font-size:0.82rem; margin-top:4px;">{r['detail']}</div>
                </div>
                """, unsafe_allow_html=True)

        # Chart
        render_complexity_chart(results)

        # Alpha-Beta savings
        if "O(bᵈ)" in results and "Alpha-Beta" in results:
            minimax_ops = results["O(bᵈ)"]["ops"]
            ab_ops = results["Alpha-Beta"]["ops"]
            if minimax_ops > 0:
                savings = (1 - ab_ops / minimax_ops) * 100
                st.markdown(f"""
                <div class="chess-insight">
                    <b>🌳 Alpha-Beta Pruning Savings:</b> Reduced search from
                    <b>{minimax_ops:,}</b> to <b>{ab_ops:,}</b> nodes —
                    a <b>{savings:.1f}%</b> reduction!
                    This is why alpha-beta is essential: it effectively reduces
                    O(bᵈ) toward O(b^(d/2)) in the best case.
                </div>
                """, unsafe_allow_html=True)


def render_pgn_analysis():
    """PGN game analysis with complexity tracking."""
    st.markdown("### 📜 PGN Game Analysis")
    st.markdown("""
    <div class="chess-insight">
    Load a PGN game to see how algorithmic complexity varies throughout the game.
    The branching factor (legal moves) changes dramatically between opening, middlegame,
    and endgame — directly affecting search tree size.
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        game_choice = st.selectbox("Choose a famous game:", list(SAMPLE_GAMES.keys()))

    with col2:
        use_custom = st.checkbox("Use custom PGN instead")

    if use_custom:
        pgn_text = st.text_area(
            "Paste PGN here:",
            height=200,
            placeholder="[Event \"...\"]\n[White \"...\"]\n[Black \"...\"]\n\n1. e4 e5 2. Nf3 ..."
        )
    else:
        pgn_text = SAMPLE_GAMES[game_choice]
        with st.expander("View PGN"):
            st.code(pgn_text, language=None)

    if pgn_text.strip():
        analysis = analyze_pgn_complexity(pgn_text)
        if analysis:
            import pandas as pd

            # Game info
            headers = analysis["headers"]
            ic1, ic2, ic3, ic4 = st.columns(4)
            with ic1:
                st.markdown(f"""<div class="metric-box">
                    <div class="metric-value" style="font-size:1rem;">{headers.get('White','?')}</div>
                    <div class="metric-label">White</div>
                </div>""", unsafe_allow_html=True)
            with ic2:
                st.markdown(f"""<div class="metric-box">
                    <div class="metric-value" style="font-size:1rem;">{headers.get('Black','?')}</div>
                    <div class="metric-label">Black</div>
                </div>""", unsafe_allow_html=True)
            with ic3:
                st.markdown(f"""<div class="metric-box">
                    <div class="metric-value">{analysis['result']}</div>
                    <div class="metric-label">Result</div>
                </div>""", unsafe_allow_html=True)
            with ic4:
                st.markdown(f"""<div class="metric-box">
                    <div class="metric-value">{len(analysis['moves'])}</div>
                    <div class="metric-label">Total Moves</div>
                </div>""", unsafe_allow_html=True)

            # Move navigator
            st.markdown("---")
            move_idx = st.slider(
                "Navigate to move:",
                0, len(analysis["moves"]) - 1, 0,
                format="Move %d"
            )

            move_data = analysis["moves"][move_idx]

            bc, mc = st.columns([1, 1])

            with bc:
                # Rebuild board to this position
                pgn_io = io.StringIO(pgn_text)
                game = chess.pgn.read_game(pgn_io)
                nav_board = game.board()
                last_move = None
                for i, m in enumerate(game.mainline_moves()):
                    if i > move_idx:
                        break
                    last_move = m
                    nav_board.push(m)

                svg = render_board_svg(nav_board, last_move=last_move, size=360)
                st.markdown(svg_to_html(svg), unsafe_allow_html=True)

            with mc:
                st.markdown(f"**Move {move_data['move_num']}:** `{move_data['san']}`")
                flags = []
                if move_data['is_capture']:
                    flags.append("⚔️ Capture")
                if move_data['is_check']:
                    flags.append("♚ Check")
                if flags:
                    st.markdown(" | ".join(flags))

                st.markdown(f"""<div class="metric-box" style="margin:0.5rem 0;">
                    <div class="metric-value">{move_data['legal_moves']}</div>
                    <div class="metric-label">Legal Moves (Branching Factor)</div>
                </div>""", unsafe_allow_html=True)

                # Theoretical tree sizes at different depths
                b = move_data['legal_moves']
                st.markdown("**Theoretical Search Tree Size:**")
                for d in [1, 2, 3, 4, 5]:
                    tree_size = b ** d
                    st.markdown(
                        f"<span class='algo-highlight'>Depth {d}: {b}^{d} = {tree_size:,} nodes</span>",
                        unsafe_allow_html=True
                    )

            # Branching factor over game
            st.markdown("#### 🌿 Branching Factor Throughout the Game")
            bf_df = pd.DataFrame({
                "Move": range(1, len(analysis["branching_factors"]) + 1),
                "Legal Moves": analysis["branching_factors"],
            }).set_index("Move")
            st.area_chart(bf_df, color="#d4a843")

            # Cumulative complexity
            st.markdown("#### 📈 Cumulative Search Space")
            cum_df = pd.DataFrame({
                "Move": range(1, len(analysis["cumulative_tree_size"]) + 1),
                "Cumulative Positions": analysis["cumulative_tree_size"],
            }).set_index("Move")
            st.area_chart(cum_df, color="#4ecdc4")

            # Complexity insights
            bfs = analysis["branching_factors"]
            avg_bf = sum(bfs) / len(bfs) if bfs else 0
            max_bf = max(bfs) if bfs else 0
            min_bf = min(bfs) if bfs else 0
            max_move = bfs.index(max_bf) + 1 if bfs else 0

            st.markdown(f"""
            <div class="chess-insight">
                <b>📊 Complexity Summary:</b><br>
                • Average branching factor: <b>{avg_bf:.1f}</b><br>
                • Peak complexity at move <b>{max_move}</b> with <b>{max_bf}</b> legal moves<br>
                • Minimum branching: <b>{min_bf}</b> moves (most forced position)<br>
                • At depth 4, peak position creates <b>{max_bf**4:,}</b> minimax nodes<br>
                • With alpha-beta, this reduces to ≈<b>{int(max_bf**2):,}</b> nodes (best case)
            </div>
            """, unsafe_allow_html=True)


def render_pruning_visualizer():
    """Visualize how alpha-beta pruning saves computation."""
    st.markdown("### ✂️ Pruning Visualizer")
    st.markdown("""
    <div class="chess-insight">
    Alpha-beta pruning is the key optimization that makes chess engines practical.
    Without it, searching just 4 moves deep with 35 legal moves per position would
    require examining <b>1,500,625</b> positions. With perfect move ordering,
    alpha-beta reduces this to approximately <b>1,225</b> — a >99.9% reduction!
    </div>
    """, unsafe_allow_html=True)

    import pandas as pd

    st.markdown("#### Branching Factor vs. Search Tree Size")

    b = st.slider("Branching factor (avg legal moves)", 5, 50, 35)
    max_depth = st.slider("Maximum depth to compare", 1, 8, 5)

    data = []
    for d in range(1, max_depth + 1):
        minimax = b ** d
        alphabeta_best = b ** math.ceil(d / 2)  # Best case
        alphabeta_avg = int(b ** (d * 0.75))  # Typical case

        data.append({
            "Depth": d,
            "Minimax O(bᵈ)": minimax,
            "Alpha-Beta (best)": alphabeta_best,
            "Alpha-Beta (typical)": alphabeta_avg,
        })

    df = pd.DataFrame(data).set_index("Depth")
    st.line_chart(df, color=["#ff6b6b", "#34d399", "#4ecdc4"])

    # Table view
    st.markdown("#### 📋 Detailed Comparison")
    table_data = []
    for d in range(1, max_depth + 1):
        minimax = b ** d
        ab_best = b ** math.ceil(d / 2)
        ab_avg = int(b ** (d * 0.75))
        table_data.append({
            "Depth": d,
            "Minimax Nodes": f"{minimax:,}",
            "AB Best Case": f"{ab_best:,}",
            "AB Typical": f"{ab_avg:,}",
            "Best Savings": f"{(1-ab_best/minimax)*100:.1f}%",
            "Typical Savings": f"{(1-ab_avg/minimax)*100:.1f}%",
        })

    st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)

    # Why it matters
    st.markdown(f"""
    <div class="chess-insight">
        <b>Why This Matters:</b><br>
        At branching factor <b>{b}</b> and depth <b>{max_depth}</b>:<br>
        • Minimax examines <b>{b**max_depth:,}</b> positions<br>
        • Alpha-beta (best case) examines <b>{b**math.ceil(max_depth/2):,}</b> positions<br>
        • That's like the difference between searching for
          {format_time_analogy(b**max_depth)} vs {format_time_analogy(b**math.ceil(max_depth/2))}<br><br>
        This is why <b>move ordering</b> matters so much — examining the best move first
        maximizes pruning efficiency!
    </div>
    """, unsafe_allow_html=True)


def format_time_analogy(nodes: int) -> str:
    """Convert node count to a time analogy assuming 1M nodes/sec."""
    seconds = nodes / 1_000_000
    if seconds < 1:
        return f"{nodes:,} microseconds"
    elif seconds < 60:
        return f"{seconds:.1f} seconds"
    elif seconds < 3600:
        return f"{seconds/60:.1f} minutes"
    elif seconds < 86400:
        return f"{seconds/3600:.1f} hours"
    elif seconds < 31536000:
        return f"{seconds/86400:.1f} days"
    else:
        return f"{seconds/31536000:.1f} years"


# ─────────────────────────────────────────────
# Main App
# ─────────────────────────────────────────────

def main():
    render_header()

    # Sidebar
    with st.sidebar:
        st.markdown("## 🧭 Navigation")
        st.markdown("---")

        st.markdown("""
        <div style="font-family:'Source Sans 3',sans-serif; color:#8a8a9a; font-size:0.85rem; line-height:1.6;">
        This app explores how <b style="color:#d4a843;">algorithmic complexity (Big O notation)</b>
        manifests in chess engines. From constant-time hash lookups to exponential game tree search,
        chess is a perfect lens for understanding computational complexity.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### Key Concepts")
        st.markdown("""
        - **Branching Factor**: ~35 legal moves per position
        - **Game Tree**: All possible continuations
        - **Minimax**: O(bᵈ) exhaustive search
        - **Alpha-Beta**: Prunes to O(b^(d/2))
        - **Transposition Table**: O(1) position lookup
        """)

        st.markdown("---")
        st.markdown("""
        <div style="font-family:'JetBrains Mono',monospace; font-size:0.7rem; color:#555; text-align:center;">
        Built with Streamlit + python-chess
        </div>
        """, unsafe_allow_html=True)

    # Main tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📐 Big O Reference",
        "⚡ Live Analysis",
        "📜 PGN Analysis",
        "✂️ Pruning Visualizer",
        "📈 Growth Rates",
    ])

    with tab1:
        render_bigo_reference()

    with tab2:
        render_live_analysis()

    with tab3:
        render_pgn_analysis()

    with tab4:
        render_pruning_visualizer()

    with tab5:
        render_growth_comparison()


if __name__ == "__main__":
    main()
