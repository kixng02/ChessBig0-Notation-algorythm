import streamlit as st
import streamlit.components.v1 as components
import chess
import chess.pgn
import pandas as pd
import numpy as np
import io

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Chess Big O Visualizer", layout="wide", page_icon="♟️")

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap');
  html, body, [class*="css"] { font-family: 'Crimson Text', serif; }
  h1, h2, h3, .stSubheader { font-family: 'Cinzel', serif !important; }
  .stApp { background-color: #0f0e17; color: #fffffe; }
  section[data-testid="stSidebar"] { background-color: #1a1a2e; }
  .stButton>button {
    background: #c9a84c; color: #0f0e17; font-weight: 700;
    border: none; border-radius: 6px; padding: 8px 20px;
    font-family: 'Cinzel', serif; font-size: 0.85rem;
  }
  .stButton>button:hover { background: #e8c46a !important; color: #0f0e17 !important; }
  .metric-box {
    background: #1a1a2e; border-radius: 10px; padding: 14px 16px;
    border: 1px solid #c9a84c44; text-align: center; margin-bottom: 10px;
  }
  .metric-label { font-size: 0.7rem; color: #a7a9be; letter-spacing: 0.1em; margin-bottom: 4px; font-family: 'Cinzel', serif; }
  .metric-value { font-size: 1.5rem; font-weight: 700; font-family: 'Cinzel', serif; }
  .status-bar {
    background: #1a1a2e; border-radius: 8px; padding: 10px 16px;
    border: 1px solid #c9a84c44; text-align: center; margin-bottom: 14px;
  }
  .move-history {
    background: #1a1a2e; border-radius: 8px; padding: 12px;
    border: 1px solid #c9a84c22; font-family: 'Crimson Text', serif;
    font-size: 1rem; max-height: 90px; overflow-y: auto;
  }
</style>
""", unsafe_allow_html=True)


# ── Session State ─────────────────────────────────────────────────────────────
if 'board' not in st.session_state:
    st.session_state.board = chess.Board()
if 'move_history_san' not in st.session_state:
    st.session_state.move_history_san = []
if 'pending_move' not in st.session_state:
    st.session_state.pending_move = ""


# ── Helpers ───────────────────────────────────────────────────────────────────
def get_status(board):
    if board.is_checkmate():
        winner = "Black" if board.turn == chess.WHITE else "White"
        return f"Checkmate! {winner} wins!", "#69ff9a"
    if board.is_stalemate():
        return "Stalemate — Draw", "#a7a9be"
    if board.is_insufficient_material():
        return "Insufficient material — Draw", "#a7a9be"
    if board.is_check():
        side = "White" if board.turn == chess.WHITE else "Black"
        return f"{side} is in Check!", "#ff6b6b"
    side = "White" if board.turn == chess.WHITE else "Black"
    return f"{side} to move", "#c9a84c"


def calc_nodes(b, d, algo):
    if algo == "Minimax":
        return float(b) ** d
    return max(0.0, 2 * float(b) ** (d / 2) - 1)


def fmt_nodes(n):
    n = int(n)
    if n >= 1_000_000_000: return f"{n/1e9:.1f}B"
    if n >= 1_000_000:     return f"{n/1e6:.1f}M"
    if n >= 1_000:         return f"{n/1e3:.0f}K"
    return f"{n:,}"


def get_dests_js(board):
    """Build JS object literal of legal moves for Chessground."""
    dests = {}
    for move in board.legal_moves:
        f = chess.square_name(move.from_square)
        t = chess.square_name(move.to_square)
        dests.setdefault(f, []).append(t)
    parts = []
    for k, v in dests.items():
        parts.append(f'"{k}": {str(v).replace(chr(39), chr(34))}')
    return "{" + ", ".join(parts) + "}"


def build_board_html(fen, dests_js, last_move, orientation):
    last_move_js = str(last_move).replace("'", '"') if last_move else "null"
    turn_color = "white" if fen.split()[1] == "w" else "black"

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{ width: 100%; height: 100%; background: transparent; overflow: hidden; }}

/* ── Chessground base styles ── */
.cg-wrap {{
  width: 100vmin; height: 100vmin; max-width: 440px; max-height: 440px;
  position: relative; user-select: none; margin: 0 auto;
}}
cg-container {{
  position: absolute; width: 100%; height: 100%; display: block;
}}
cg-board {{
  position: absolute; top: 0; left: 0; width: 100%; height: 100%;
  cursor: pointer;
  /* Brown board checkerboard */
  background-color: #b58863;
}}
cg-board square {{
  position: absolute; width: 12.5%; height: 12.5%; pointer-events: none;
}}
cg-board square.last-move {{ background-color: rgba(20,85,30,0.5); }}
cg-board square.selected  {{ background-color: rgba(20,85,0,0.5); }}
cg-board square.move-dest {{
  pointer-events: auto; cursor: pointer;
  background: radial-gradient(rgba(20,85,30,0.5) 22%, rgba(20,85,30,0.5) 0, rgba(0,0,0,0.3) 0) center/100% 100%;
}}
cg-board square.move-dest.capture {{
  background: radial-gradient(transparent 0%, transparent 79%, rgba(20,85,30,0.6) 80%) center/100% 100%;
}}

piece {{
  position: absolute; width: 12.5%; height: 12.5%;
  background-size: cover; z-index: 2; will-change: transform;
  pointer-events: auto; cursor: pointer;
  transition: transform 0.15s ease;
}}
piece.dragging {{ cursor: grabbing; z-index: 9; transition: none; pointer-events: none; }}

coords {{
  position: absolute; display: flex; pointer-events: none;
  opacity: 0.85; font-size: 9px; font-weight: bold; font-family: sans-serif;
  z-index: 3;
}}
coords.ranks {{ flex-direction: column; top: 0; left: 2px; height: 100%; justify-content: space-around; }}
coords.files {{ flex-direction: row; bottom: 1px; right: 3px; width: 96%; justify-content: space-around; }}
coords.ranks coord {{ color: #f0d9b5; }}
coords.ranks coord:nth-child(even) {{ color: #b58863; }}
coords.files coord {{ color: #b58863; }}
coords.files coord:nth-child(even) {{ color: #f0d9b5; }}

/* Piece SVGs via Lichess CDN (cburnett set) */
piece.white.pawn   {{ background-image: url('https://lichess1.org/assets/piece/cburnett/wP.svg'); }}
piece.white.rook   {{ background-image: url('https://lichess1.org/assets/piece/cburnett/wR.svg'); }}
piece.white.knight {{ background-image: url('https://lichess1.org/assets/piece/cburnett/wN.svg'); }}
piece.white.bishop {{ background-image: url('https://lichess1.org/assets/piece/cburnett/wB.svg'); }}
piece.white.queen  {{ background-image: url('https://lichess1.org/assets/piece/cburnett/wQ.svg'); }}
piece.white.king   {{ background-image: url('https://lichess1.org/assets/piece/cburnett/wK.svg'); }}
piece.black.pawn   {{ background-image: url('https://lichess1.org/assets/piece/cburnett/bP.svg'); }}
piece.black.rook   {{ background-image: url('https://lichess1.org/assets/piece/cburnett/bR.svg'); }}
piece.black.knight {{ background-image: url('https://lichess1.org/assets/piece/cburnett/bN.svg'); }}
piece.black.bishop {{ background-image: url('https://lichess1.org/assets/piece/cburnett/bB.svg'); }}
piece.black.queen  {{ background-image: url('https://lichess1.org/assets/piece/cburnett/bQ.svg'); }}
piece.black.king   {{ background-image: url('https://lichess1.org/assets/piece/cburnett/bK.svg'); }}

/* Promotion modal */
#promo-modal {{
  display: none; position: fixed; inset: 0;
  background: rgba(0,0,0,0.8); z-index: 50;
  align-items: center; justify-content: center;
}}
#promo-modal.show {{ display: flex; }}
.promo-box {{
  background: #1a1a2e; border: 2px solid #c9a84c; border-radius: 12px;
  padding: 16px 20px; display: flex; flex-direction: column; align-items: center; gap: 12px;
}}
.promo-box h3 {{ color: #c9a84c; font-family: Georgia, serif; font-size: 1rem; }}
.promo-row {{ display: flex; gap: 8px; }}
.promo-piece {{
  width: 56px; height: 56px; background-size: cover; cursor: pointer;
  border: 2px solid #c9a84c44; border-radius: 8px;
}}
.promo-piece:hover {{ border-color: #c9a84c; }}
</style>
</head>
<body>

<div class="cg-wrap">
  <cg-container id="cgc">
    <cg-board id="cgb"></cg-board>
  </cg-container>
</div>

<div id="promo-modal">
  <div class="promo-box">
    <h3>Promote pawn to:</h3>
    <div class="promo-row" id="promo-row"></div>
  </div>
</div>

<script>
const FILES = ['a','b','c','d','e','f','g','h'];
const PIECE_MAP = {{ p:'pawn', r:'rook', n:'knight', b:'bishop', q:'queen', k:'king' }};

let S = {{
  fen: {repr(fen)},
  orientation: {repr(orientation)},
  dests: {dests_js},
  lastMove: {last_move_js},
  turnColor: {repr(turn_color)},
  selected: null,
  promoState: null,
}};

const board = document.getElementById('cgb');
const container = document.getElementById('cgc');

// ── FEN parser ──
function parseFen(fen) {{
  const pos = fen.split(' ')[0];
  const pieces = {{}};
  pos.split('/').forEach((row, ri) => {{
    let ci = 0;
    for (const ch of row) {{
      if (isNaN(ch)) {{
        const sq = FILES[ci] + (8 - ri);
        pieces[sq] = {{ color: ch === ch.toUpperCase() ? 'white' : 'black', type: PIECE_MAP[ch.toLowerCase()] }};
        ci++;
      }} else ci += +ch;
    }}
  }});
  return pieces;
}}

// ── Square → CSS position ──
function sqPos(sq) {{
  const fi = FILES.indexOf(sq[0]), ri = +sq[1] - 1;
  return S.orientation === 'white'
    ? {{ left: fi * 12.5 + '%', top: (7 - ri) * 12.5 + '%' }}
    : {{ left: (7 - fi) * 12.5 + '%', top: ri * 12.5 + '%' }};
}}

// ── Render ──
function render() {{
  board.innerHTML = '';
  container.querySelectorAll('coords').forEach(e => e.remove());

  const pieces = parseFen(S.fen);

  // Highlight squares
  const highlights = [];
  if (S.lastMove) S.lastMove.forEach(sq => highlights.push({{ sq, cls: 'last-move' }}));
  if (S.selected) {{
    highlights.push({{ sq: S.selected, cls: 'selected' }});
    (S.dests[S.selected] || []).forEach(sq => {{
      highlights.push({{ sq, cls: pieces[sq] ? 'move-dest capture' : 'move-dest' }});
    }});
  }}

  highlights.forEach(({{ sq, cls }}) => {{
    const el = document.createElement('square');
    el.className = cls; Object.assign(el.style, sqPos(sq));
    if (cls.includes('move-dest')) {{
      el.addEventListener('click', () => doMove(sq));
    }}
    board.appendChild(el);
  }});

  // Pieces
  Object.entries(pieces).forEach(([sq, {{ color, type }}]) => {{
    const el = document.createElement('piece');
    el.className = color + ' ' + type;
    Object.assign(el.style, sqPos(sq));
    el.addEventListener('click', e => {{ e.stopPropagation(); handlePieceClick(sq, color); }});
    board.appendChild(el);
  }});

  // Coords
  const ranks = document.createElement('coords'); ranks.className = 'ranks';
  const files = document.createElement('coords'); files.className = 'files';
  const ro = S.orientation === 'white' ? [8,7,6,5,4,3,2,1] : [1,2,3,4,5,6,7,8];
  const fo = S.orientation === 'white' ? FILES : [...FILES].reverse();
  ro.forEach(r => {{ const c = document.createElement('coord'); c.textContent = r; ranks.appendChild(c); }});
  fo.forEach(f => {{ const c = document.createElement('coord'); c.textContent = f; files.appendChild(c); }});
  container.appendChild(ranks); container.appendChild(files);
}}

function handlePieceClick(sq, color) {{
  if (S.promoState) return;
  // If clicking a legal destination that happens to have an enemy piece
  if (S.selected && (S.dests[S.selected] || []).includes(sq)) {{
    doMove(sq); return;
  }}
  if (color !== S.turnColor) {{ S.selected = null; render(); return; }}
  S.selected = S.selected === sq ? null : sq;
  render();
}}

function doMove(to) {{
  if (!S.selected) return;
  const from = S.selected;
  const pieces = parseFen(S.fen);
  const piece = pieces[from];
  const isPromo = piece && piece.type === 'pawn' &&
    ((piece.color==='white' && to[1]==='8') || (piece.color==='black' && to[1]==='1'));

  if (isPromo) {{
    S.promoState = {{ from, to, color: piece.color }};
    showPromo(piece.color); return;
  }}
  sendMove(from, to, null);
}}

function sendMove(from, to, promo) {{
  S.selected = null; S.promoState = null;
  // Communicate move back to Streamlit via URL hash + storage event trick
  // Use the simplest reliable method: set the move in the iframe's own input
  // and trigger a custom event that Streamlit can pick up via components
  const uci = from + to + (promo || '');
  // Post to parent window (Streamlit)
  window.parent.postMessage({{ type: 'chess_move', uci }}, '*');
  // Also update local display optimistically
  S.lastMove = [from, to];
  render();
}}

function showPromo(color) {{
  const modal = document.getElementById('promo-modal');
  const row = document.getElementById('promo-row');
  row.innerHTML = '';
  [['q','queen'],['r','rook'],['b','bishop'],['n','knight']].forEach(([letter, type]) => {{
    const btn = document.createElement('div');
    btn.className = 'promo-piece';
    btn.style.backgroundImage =
      `url('https://lichess1.org/assets/piece/cburnett/${{color==='white'?'w':'b'}}${{letter.toUpperCase()}}.svg')`;
    btn.addEventListener('click', () => {{
      modal.classList.remove('show');
      sendMove(S.promoState.from, S.promoState.to, letter);
    }});
    row.appendChild(btn);
  }});
  modal.classList.add('show');
}}

render();
</script>
</body>
</html>"""


# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.markdown("<h2 style='color:#c9a84c;font-family:Cinzel,serif;'>⚙️ Settings</h2>", unsafe_allow_html=True)
branching_factor = st.sidebar.slider("Avg. Branching Factor (b)", 2, 40, 35)
max_depth = st.sidebar.slider("Simulation Depth (d)", 1, 8, 4)
orientation = st.sidebar.radio("Board orientation", ["white", "black"], horizontal=True)

st.sidebar.markdown("---")
st.sidebar.markdown("<h3 style='color:#c9a84c;font-family:Cinzel,serif;'>📋 PGN Input</h3>", unsafe_allow_html=True)
pgn_input = st.sidebar.text_area("Paste PGN (optional)", height=130, placeholder="1. e4 e5 2. Nf3 ...")
if pgn_input and st.sidebar.button("Load PGN"):
    try:
        pgn_stream = io.StringIO(pgn_input)
        game = chess.pgn.read_game(pgn_stream)
        if game:
            new_board = game.board()
            san_list = []
            for move in game.mainline_moves():
                san_list.append(new_board.san(move))
                new_board.push(move)
            st.session_state.board = new_board
            st.session_state.move_history_san = san_list
            st.rerun()
    except Exception as e:
        st.sidebar.error(f"PGN error: {e}")

# ── Title ─────────────────────────────────────────────────────────────────────
st.markdown(
    "<h1 style='color:#c9a84c;text-align:center;margin-bottom:4px;'>♟ Chess Engine · Big O Visualizer</h1>",
    unsafe_allow_html=True
)
st.markdown(
    "<p style='color:#a7a9be;text-align:center;font-size:1.05rem;margin-bottom:18px;'>"
    "Lichess Chessground board · Minimax O(bᵈ) vs Alpha-Beta O(b^d/2)</p>",
    unsafe_allow_html=True
)

# ── Layout ────────────────────────────────────────────────────────────────────
col_board, col_analysis = st.columns([1, 1.3], gap="large")
board_obj = st.session_state.board

with col_board:
    st.markdown("<h3 style='color:#c9a84c;font-family:Cinzel,serif;margin-bottom:8px;'>Interactive Board</h3>", unsafe_allow_html=True)

    status_text, status_color = get_status(board_obj)
    st.markdown(
        f'<div class="status-bar"><span style="color:{status_color};font-size:1rem;font-weight:600;">'
        f'{"♔" if board_obj.turn==chess.WHITE else "♚"} {status_text}</span></div>',
        unsafe_allow_html=True
    )

    # Build board params
    dests_js  = get_dests_js(board_obj)
    move_stack = list(board_obj.move_stack)
    last_move = (
        [chess.square_name(move_stack[-1].from_square), chess.square_name(move_stack[-1].to_square)]
        if move_stack else []
    )

    board_html = build_board_html(board_obj.fen(), dests_js, last_move, orientation)
    components.html(board_html, height=470, scrolling=False)

    # ── Move input: accepts UCI from user typing or copy-paste ────────────────
    st.markdown(
        "<small style='color:#a7a9be;'>💡 Board interaction works via the input below — "
        "type a move in UCI format (e.g. <code>e2e4</code>). "
        "The board above shows legal move dots when you click a piece image "
        "— your browser console will show the UCI string to copy.</small>",
        unsafe_allow_html=True
    )

    # We inject JS that listens for postMessage and fills a hidden streamlit component
    # The cleanest approach: show a text_input that the user fills from the board's JS output
    # Plus add a JS snippet that auto-fills it via the Streamlit component trick

    move_col, btn_col = st.columns([3, 1])
    with move_col:
        move_input = st.text_input(
            "Enter move (UCI)",
            value=st.session_state.pending_move,
            key="uci_input",
            label_visibility="collapsed",
            placeholder="Type move e.g. e2e4, g1f3 ..."
        )
    with btn_col:
        submit = st.button("▶ Play", use_container_width=True)

    if submit and move_input.strip():
        raw = move_input.strip().lower()
        try:
            move = chess.Move.from_uci(raw)
            if move in board_obj.legal_moves:
                san = board_obj.san(move)
                board_obj.push(move)
                st.session_state.move_history_san.append(san)
                st.session_state.pending_move = ""
                st.rerun()
            else:
                st.error(f"Illegal move: {raw}")
        except Exception:
            st.error(f"Invalid UCI: {raw}")

    # ── JS listener that captures postMessage from the iframe ─────────────────
    # This injects a tiny script into the Streamlit page that catches the chess_move
    # message from the iframe and fills the text input automatically.
    components.html("""
    <script>
    window.addEventListener('message', function(e) {
      if (e.data && e.data.type === 'chess_move') {
        // Find Streamlit's text input and set its value
        const inputs = window.parent.document.querySelectorAll('input[type="text"]');
        for (const inp of inputs) {
          if (inp.placeholder && inp.placeholder.includes('e2e4')) {
            const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
              window.parent.HTMLInputElement.prototype, 'value').set;
            nativeInputValueSetter.call(inp, e.data.uci);
            inp.dispatchEvent(new Event('input', { bubbles: true }));
            inp.dispatchEvent(new Event('change', { bubbles: true }));
            break;
          }
        }
      }
    });
    </script>
    """, height=0)

    # Controls
    c1, c2 = st.columns(2)
    with c1:
        if st.button("↺ Reset Board", use_container_width=True):
            st.session_state.board = chess.Board()
            st.session_state.move_history_san = []
            st.session_state.pending_move = ""
            st.rerun()
    with c2:
        if st.button("↩ Undo Move", use_container_width=True):
            if board_obj.move_stack:
                board_obj.pop()
                if st.session_state.move_history_san:
                    st.session_state.move_history_san.pop()
                st.rerun()

    # Move history
    if st.session_state.move_history_san:
        history = st.session_state.move_history_san
        pairs = []
        for i in range(0, len(history), 2):
            w = history[i]
            b = history[i + 1] if i + 1 < len(history) else "…"
            pairs.append(f"{i // 2 + 1}. {w} {b}")
        st.markdown(
            f'<div class="move-history" style="color:#fffffe;">{" &nbsp;|&nbsp; ".join(pairs[-10:])}</div>',
            unsafe_allow_html=True
        )

# ── Analysis Column ───────────────────────────────────────────────────────────
with col_analysis:
    st.markdown("<h3 style='color:#c9a84c;font-family:Cinzel,serif;margin-bottom:8px;'>Complexity Analysis</h3>", unsafe_allow_html=True)

    actual_b = board_obj.legal_moves.count()
    m_nodes  = calc_nodes(branching_factor, max_depth, "Minimax")
    a_nodes  = calc_nodes(branching_factor, max_depth, "Alpha-Beta")
    reduction = (m_nodes - a_nodes) / m_nodes * 100 if m_nodes > 0 else 0

    mc1, mc2, mc3, mc4 = st.columns(4)
    for col, (label, value, color) in zip(
        [mc1, mc2, mc3, mc4],
        [
            ("MINIMAX NODES",    fmt_nodes(m_nodes),  "#ff6b6b"),
            ("ALPHA-BETA NODES", fmt_nodes(a_nodes),  "#69ff9a"),
            ("NODE REDUCTION",   f"{reduction:.1f}%", "#c9a84c"),
            ("LEGAL MOVES NOW",  str(actual_b),        "#7eb5ff"),
        ]
    ):
        with col:
            st.markdown(
                f'<div class="metric-box">'
                f'<div class="metric-label">{label}</div>'
                f'<div class="metric-value" style="color:{color}">{value}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

    st.markdown("<br/>", unsafe_allow_html=True)

    depths = list(range(1, max_depth + 1))
    chart_df = pd.DataFrame({
        "Depth": depths,
        "Minimax O(bᵈ)":      [calc_nodes(branching_factor, d, "Minimax")     for d in depths],
        "Alpha-Beta O(b^d/2)": [calc_nodes(branching_factor, d, "Alpha-Beta") for d in depths],
    }).set_index("Depth")
    st.line_chart(chart_df, color=["#ff6b6b", "#69ff9a"])

    st.markdown("---")
    t1, t2 = st.columns(2)
    with t1:
        st.markdown(f"""
**🔴 Minimax: O(bᵈ)**

Every node in the game tree is visited. With **b={branching_factor}** and **d={max_depth}**:

- **~{fmt_nodes(m_nodes)} nodes** evaluated
- Each extra ply multiplies work by **{branching_factor}×**
- Grows **exponentially** — impractical beyond depth 6
        """)
    with t2:
        st.markdown(f"""
**🟢 Alpha-Beta: O(b^d/2)**

Prunes branches that can't affect the result:

- **~{fmt_nodes(a_nodes)} nodes** in best case
- **{reduction:.0f}% fewer** nodes than Minimax
- Searches **twice as deep** for same compute cost
        """)

    st.markdown("---")
    st.caption("Chessground UI by lichess.org (GPL-3.0) · Pieces: cburnett SVG set · Theoretical values assume optimal Alpha-Beta move ordering.")
