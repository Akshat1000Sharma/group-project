import streamlit as st
import copy
import time
from typing import List, Tuple

BOARD_SIZE = 8
INITIAL_BOARD = [
    [0] * BOARD_SIZE for _ in range(BOARD_SIZE)
]
INITIAL_BOARD[3][3] = -1  # White
INITIAL_BOARD[3][4] = 1   # Black
INITIAL_BOARD[4][3] = 1   # Black
INITIAL_BOARD[4][4] = -1  # White

class Othello:
    def __init__(self):
        self.board = copy.deepcopy(INITIAL_BOARD)
        self.current_player = 1  # Human starts (black)
        self.game_over = False

    def get_valid_moves(self, player: int) -> List[Tuple[int, int]]:
        moves = []
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if self.board[r][c] == 0:
                    for dr, dc in directions:
                        if self._is_valid_flip(r, c, dr, dc, player):
                            moves.append((r, c))
                            break
        return list(set(moves))

    def _is_valid_flip(self, r: int, c: int, dr: int, dc: int, player: int) -> bool:
        r += dr
        c += dc
        if not (0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE) or self.board[r][c] != -player:
            return False
        while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE:
            if self.board[r][c] == player:
                return True
            if self.board[r][c] == 0:
                return False
            r += dr
            c += dc
        return False

    def make_move(self, r: int, c: int, player: int) -> bool:
        if (r, c) not in self.get_valid_moves(player):
            return False
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        self.board[r][c] = player
        for dr, dc in directions:
            if self._is_valid_flip(r, c, dr, dc, player):
                nr, nc = r + dr, c + dc
                while 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and self.board[nr][nc] == -player:
                    self.board[nr][nc] = player
                    nr += dr
                    nc += dc
        self.current_player = -player
        return True

    def evaluate_board(self, player: int) -> int:
        score = 0
        black_pieces = sum(1 for row in self.board for cell in row if cell == 1)
        white_pieces = sum(1 for row in self.board for cell in row if cell == -1)
        score += (black_pieces - white_pieces) * (1 if player == 1 else -1)
        black_moves = len(self.get_valid_moves(1))
        white_moves = len(self.get_valid_moves(-1))
        score += (black_moves - white_moves) * (2 if player == 1 else -2)
        return score

    def is_terminal(self) -> bool:
        return len(self.get_valid_moves(self.current_player)) == 0 and \
               len(self.get_valid_moves(-self.current_player)) == 0

    def get_winner(self) -> int:
        black = sum(1 for row in self.board for cell in row if cell == 1)
        white = sum(1 for row in self.board for cell in row if cell == -1)
        if black > white:
            return 1
        elif white > black:
            return -1
        return 0

def minimax(game: Othello, depth: int, alpha: float, beta: float, maximizing_player: bool) -> int:
    if depth == 0 or game.is_terminal():
        return game.evaluate_board(1)
    moves = game.get_valid_moves(game.current_player)
    if len(moves) == 0:
        if len(game.get_valid_moves(-game.current_player)) == 0:
            return game.evaluate_board(1)
        current = game.current_player
        game.current_player = -current
        val = minimax(game, depth - 1, alpha, beta, not maximizing_player)
        game.current_player = current
        return val
    if maximizing_player:
        max_eval = float('-inf')
        for r, c in moves:
            new_game = copy.deepcopy(game)
            new_game.make_move(r, c, game.current_player)
            eval_score = minimax(new_game, depth - 1, alpha, beta, False)
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for r, c in moves:
            new_game = copy.deepcopy(game)
            new_game.make_move(r, c, game.current_player)
            eval_score = minimax(new_game, depth - 1, alpha, beta, True)
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval

def ai_move(game: Othello, depth: int = 4) -> Tuple[int, int] | None:
    moves = game.get_valid_moves(game.current_player)
    if not moves:
        return None
    best_score = float('inf')
    best_move = None
    for r, c in moves:
        new_game = copy.deepcopy(game)
        new_game.make_move(r, c, game.current_player)
        score = minimax(new_game, depth - 1, float('-inf'), float('inf'), True)
        if score < best_score:
            best_score = score
            best_move = (r, c)
    if best_move:
        game.make_move(best_move[0], best_move[1], game.current_player)
    return best_move

# Streamlit app
def main():
    st.set_page_config(page_title="Othello Game", page_icon="⚫", layout="wide")
    
    # Custom CSS
    st.markdown("""
    <style>
    .label-cell {
        width: 80px !important;
        height: 80px !important;
        background-color: #2E7D32 !important;
        color: white !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        font-weight: bold !important;
        font-size: 1.5em !important;
        border: 1px solid #1B5E20 !important;
    }
    .board-cell {
        width: 80px !important;
        height: 80px !important;
        background-color: #66BB6A !important;
        border: 1px solid white !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    .piece-black {
        color: #000 !important;
        font-size: 3em !important;
        text-shadow: 1px 1px 2px rgba(255,255,255,0.5) !important;
    }
    .piece-white {
        color: #FFF !important;
        font-size: 3em !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.5) !important;
    }
    .stButton > button {
        width: 80px !important;
        height: 80px !important;
        background-color: #FFECB3 !important;
        border: 2px solid #FFD700 !important;
        color: #FF8F00 !important;
        font-size: 2.5em !important;
        border-radius: 0 !important;
        box-shadow: inset 0 0 10px rgba(255,215,0,0.5) !important;
    }
    .stButton > button:hover {
        background-color: #FFE082 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("🎮 Othello")

    if 'game' not in st.session_state:
        st.session_state.game = Othello()

    game = st.session_state.game

    # Scores
    black_pieces = sum(1 for row in game.board for cell in row if cell == 1)
    white_pieces = sum(1 for row in game.board for cell in row if cell == -1)
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Black (You)", black_pieces)
    with col2:
        st.metric("White (AI)", white_pieces)

    # Game over
    if game.is_terminal():
        winner = game.get_winner()
        if winner == 1:
            st.success("🏆 Black (You) Win!")
        elif winner == -1:
            st.error("🤖 White (AI) Wins!")
        else:
            st.info("🤝 It's a Draw!")
        if st.button("🔄 New Game"):
            st.session_state.game = Othello()
            st.rerun()
        return

    # Current status
    current_player = game.current_player
    valid_moves = game.get_valid_moves(current_player)
    if current_player == 1:
        if len(valid_moves) == 0:
            st.warning("No valid moves for you. Skipping to AI's turn.")
            game.current_player = -1
            st.rerun()
        else:
            st.success("**Your Turn (Black)**")
    else:
        st.info("**AI's Turn (White)**")

    # Board
    st.subheader("Game Board")

    # Header row
    cols = st.columns(9)
    with cols[0]:
        st.markdown('<div class="label-cell"></div>', unsafe_allow_html=True)
    for c in range(8):
        with cols[c + 1]:
            st.markdown(f'<div class="label-cell">{c}</div>', unsafe_allow_html=True)

    # Game rows
    for r in range(8):
        cols = st.columns(9)
        with cols[0]:
            st.markdown(f'<div class="label-cell">{r}</div>', unsafe_allow_html=True)
        for c in range(8):
            with cols[c + 1]:
                cell_val = game.board[r][c]
                if cell_val == 1:
                    st.markdown('<div class="board-cell piece-black">⚫</div>', unsafe_allow_html=True)
                elif cell_val == -1:
                    st.markdown('<div class="board-cell piece-white">⚪</div>', unsafe_allow_html=True)
                else:
                    is_valid = current_player == 1 and (r, c) in valid_moves
                    if is_valid:
                        if st.button('○', key=f'move_{r}_{c}'):
                            if game.make_move(r, c, 1):
                                st.rerun()
                    else:
                        st.markdown('<div class="board-cell"></div>', unsafe_allow_html=True)

    # Handle AI turn with delay
    if game.current_player == -1:
        st.info("AI is thinking...")
        time.sleep(2)
        with st.spinner("AI is making its move..."):
            ai_move(game)
        # Check for skips after AI move
        if len(game.get_valid_moves(game.current_player)) == 0 and not game.is_terminal():
            st.info("No valid moves for you. Skipping your turn.")
            game.current_player = -1
        st.rerun()

    # New Game
    if st.button("🔄 New Game"):
        st.session_state.game = Othello()
        st.rerun()

if __name__ == "__main__":
    main()