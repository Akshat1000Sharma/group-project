import streamlit as st
import copy
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Circle
import numpy as np

# Board representation: 8x8 grid, 0=empty, 1=black (human), -1=white (AI)
BOARD_SIZE = 8
INITIAL_BOARD = [
    [0] * BOARD_SIZE for _ in range(BOARD_SIZE)
]
# Corrected starting position: Diagonals
INITIAL_BOARD[3][3] = -1  # White
INITIAL_BOARD[3][4] = 1   # Black
INITIAL_BOARD[4][3] = 1   # Black
INITIAL_BOARD[4][4] = -1  # White

class Othello:
    def __init__(self):
        self.board = copy.deepcopy(INITIAL_BOARD)
        self.current_player = 1  # Human starts (black)
        self.game_over = False
    
    def get_valid_moves(self, player):
        """Find all valid moves for the player."""
        moves = []
        directions = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if self.board[r][c] == 0:  # Empty cell
                    for dr, dc in directions:
                        if self._is_valid_flip(r, c, dr, dc, player):
                            moves.append((r, c))
                            break  # Valid if at least one direction flips
        return list(set(moves))  # Remove duplicates
    
    def _is_valid_flip(self, r, c, dr, dc, player):
        """Check if placing at (r,c) flips in direction (dr,dc)."""
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
    
    def make_move(self, r, c, player):
        """Place piece and flip opponents."""
        if (r, c) not in self.get_valid_moves(player):
            return False
        directions = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
        self.board[r][c] = player
        for dr, dc in directions:
            if self._is_valid_flip(r, c, dr, dc, player):
                nr, nc = r + dr, c + dc
                while self.board[nr][nc] == -player:
                    self.board[nr][nc] = player
                    nr += dr
                    nc += dc
        self.current_player = -player
        return True
    
    def evaluate_board(self, player):
        """Heuristic: Pieces + Mobility (valid moves)."""
        score = 0
        # Piece count
        black_pieces = sum(1 for row in self.board for cell in row if cell == 1)
        white_pieces = sum(1 for row in self.board for cell in row if cell == -1)
        score += (black_pieces - white_pieces) * (1 if player == 1 else -1)
        
        # Mobility
        black_moves = len(self.get_valid_moves(1))
        white_moves = len(self.get_valid_moves(-1))
        score += (black_moves - white_moves) * (2 if player == 1 else -2)
        
        return score
    
    def is_terminal(self):
        """Check if game over (no moves for both players)."""
        return len(self.get_valid_moves(self.current_player)) == 0 and \
               len(self.get_valid_moves(-self.current_player)) == 0
    
    def get_winner(self):
        """Return winner: 1 black, -1 white, 0 draw."""
        black = sum(1 for row in self.board for cell in row if cell == 1)
        white = sum(1 for row in self.board for cell in row if cell == -1)
        if black > white:
            return 1
        elif white > black:
            return -1
        return 0

def minimax(game, depth, alpha, beta, maximizing_player):
    """Minimax with Alpha-Beta Pruning."""
    if depth == 0 or game.is_terminal():
        return game.evaluate_board(1)  # Evaluate from black's perspective
    
    moves = game.get_valid_moves(game.current_player)
    if not moves:
        game.current_player = -game.current_player  # Skip turn
        val = minimax(game, depth, alpha, beta, maximizing_player)
        game.current_player = -game.current_player  # Revert
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

def ai_move(game, depth=4):
    """AI selects best move using Minimax."""
    best_score = float('-inf')
    best_move = None
    moves = game.get_valid_moves(game.current_player)
    for r, c in moves:
        new_game = copy.deepcopy(game)
        new_game.make_move(r, c, game.current_player)
        score = minimax(new_game, depth - 1, float('-inf'), float('inf'), False)
        if score > best_score:
            best_score = score
            best_move = (r, c)
    if best_move:
        game.make_move(best_move[0], best_move[1], game.current_player)
    return best_move

def st_display_board(game, valid_moves=None):
    """Display the board graphically in Streamlit using matplotlib."""
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.set_xlim(0, BOARD_SIZE)
    ax.set_ylim(0, BOARD_SIZE)
    ax.set_aspect('equal')
    ax.axis('off')
    
    # Draw grid lines
    for i in range(BOARD_SIZE + 1):
        ax.axhline(i, color='black', linewidth=1)
        ax.axvline(i, color='black', linewidth=1)
    
    # Draw cells
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            # Default green cell
            cell_color = 'green'
            if valid_moves and (r, c) in valid_moves:
                cell_color = 'yellow'
            
            rect = patches.Rectangle((c, BOARD_SIZE - 1 - r), 1, 1, 
                                   linewidth=0, facecolor=cell_color, alpha=0.3)
            ax.add_patch(rect)
            
            # Draw piece if present
            cell = game.board[r][c]
            if cell != 0:
                center_x = c + 0.5
                center_y = BOARD_SIZE - 0.5 - r
                circle = Circle((center_x, center_y), 0.4, 
                              facecolor='black' if cell == 1 else 'white',
                              edgecolor='black', linewidth=1)
                ax.add_patch(circle)
    
    st.pyplot(fig)
    plt.close(fig)

# Streamlit App
st.title("🖤 Othello 🕶️")

if "game" not in st.session_state:
    st.session_state.game = Othello()

game = st.session_state.game

# Calculate scores
black_count = sum(1 for row in game.board for cell in row if cell == 1)
white_count = sum(1 for row in game.board for cell in row if cell == -1)

col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    st.metric("🖤 Black (You)", black_count)

with col3:
    st.metric("⚪ White (AI)", white_count)

# Turn indicator
if game.current_player == 1:
    st.success("🚀 Your Turn (Black)")
else:
    st.info("🤖 AI's Turn (White)")

st_display_board(game)

if game.is_terminal():
    st.subheader("🏁 Game Over!")
    winner = game.get_winner()
    if winner == 1:
        st.balloons()
        st.success("🏆 You win! (Black)")
    elif winner == -1:
        st.error("🤖 AI wins! (White)")
    else:
        st.info("🤝 It's a draw!")
    
    if st.button("🔄 New Game"):
        st.session_state.game = Othello()
        st.rerun()
else:
    if game.current_player == 1:
        # Human turn
        valid_moves = game.get_valid_moves(1)
        if not valid_moves:
            st.warning("No valid moves for you. Skipping your turn.")
            game.current_player = -game.current_player
            st.rerun()
        
        col1, col2 = st.columns(2)
        with col1:
            row = st.selectbox("Row (0-7)", options=list(range(8)), key="row_select")
        with col2:
            col_ = st.selectbox("Column (0-7)", options=list(range(8)), key="col_select")
        
        if st.button("🚀 Make Move"):
            success = game.make_move(row, col_, 1)
            if success:
                st.success("✅ Move made!")
                if len(game.get_valid_moves(game.current_player)) == 0:
                    st.info("AI has no moves. Your turn again!")
                    game.current_player = -game.current_player
                st.rerun()
            else:
                st.error("❌ Invalid move!")
    else:
        # AI turn
        with st.spinner("🤖 AI thinking..."):
            move = ai_move(game)
        if move:
            st.success(f"AI moves to ({move[0]}, {move[1]})")
            if len(game.get_valid_moves(game.current_player)) == 0:
                st.info("You have no moves. AI's turn again!")
                game.current_player = -game.current_player
        else:
            st.info("AI has no moves. Your turn!")
            game.current_player = -game.current_player
        st.rerun()