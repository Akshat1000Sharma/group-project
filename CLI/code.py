import copy
import random
import time
from typing import Optional, Tuple

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

POSITION_WEIGHTS = [
    [100, -20, 10, 5, 5, 10, -20, 100],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [10, -2, 0, 0, 0, 0, -2, 10],
    [5, -2, 0, 0, 0, 0, -2, 5],
    [5, -2, 0, 0, 0, 0, -2, 5],
    [10, -2, 0, 0, 0, 0, -2, 10],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [100, -20, 10, 5, 5, 10, -20, 100],
]

# Zobrist hashing setup for transposition table
random.seed(0xC0FFEE)
ZOBRIST_TABLE = [[[random.getrandbits(64) for _ in range(2)] for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
ZOBRIST_PLAYER = random.getrandbits(64)

class Othello:
    def __init__(self):
        self.board = copy.deepcopy(INITIAL_BOARD)
        self.current_player = 1  # Human starts (black)
        self.game_over = False

    def display_board(self):
        print("  ", end="")
        for col in range(BOARD_SIZE):
            print(f" {col} ", end="")
        print()
        for row in range(BOARD_SIZE):
            print(f"{row} ", end="")
            for cell in self.board[row]:
                if cell == 1:
                    print(" B ", end="")
                elif cell == -1:
                    print(" W ", end="")
                else:
                    print(" . ", end="")
            print()
        print()

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
        """Place piece and flip opponents. Returns number of flipped pieces (used for heuristic)."""
        if (r, c) not in self.get_valid_moves(player):
            return False
        directions = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
        self.board[r][c] = player
        total_flipped = 0
        for dr, dc in directions:
            if self._is_valid_flip(r, c, dr, dc, player):
                nr, nc = r + dr, c + dc
                while 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and self.board[nr][nc] == -player:
                    self.board[nr][nc] = player
                    total_flipped += 1
                    nr += dr
                    nc += dc
        self.current_player = -player
        return total_flipped

    def evaluate_board(self, player: int) -> int:
        """
        Composite heuristic:
         - piece difference
         - mobility
         - positional weights
        Evaluation returned is from BLACK'S perspective (player == 1).
        """
        score = 0
        black_pieces = sum(1 for row in self.board for cell in row if cell == 1)
        white_pieces = sum(1 for row in self.board for cell in row if cell == -1)
        score += (black_pieces - white_pieces) * (1 if player == 1 else -1)

        # Mobility
        black_moves = len(self.get_valid_moves(1))
        white_moves = len(self.get_valid_moves(-1))
        score += (black_moves - white_moves) * (2 if player == 1 else -2)

        # Positional weights
        pos_score = 0
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if self.board[r][c] == 1:
                    pos_score += POSITION_WEIGHTS[r][c]
                elif self.board[r][c] == -1:
                    pos_score -= POSITION_WEIGHTS[r][c]
        score += pos_score * (1 if player == 1 else -1)

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

    def zobrist_key(self):
        """Compute Zobrist key for transposition table."""
        h = 0
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                cell = self.board[r][c]
                if cell == 1:
                    h ^= ZOBRIST_TABLE[r][c][0]
                elif cell == -1:
                    h ^= ZOBRIST_TABLE[r][c][1]
        if self.current_player == -1:
            h ^= ZOBRIST_PLAYER
        return h

# Global transposition table (simple)
# stores: key -> (depth, value)
TT = {}

# Time management for iterative deepening
class SearchTimer:
    def __init__(self, time_limit: float):
        self.time_limit = time_limit
        self.start = 0.0

    def start_timer(self):
        self.start = time.perf_counter()

    def time_up(self) -> bool:
        return (time.perf_counter() - self.start) >= self.time_limit

def order_moves(game: Othello, moves, player):
    """Order moves: corners first, then by number of flips (descending), then positional weight."""
    corners = {(0,0),(0,7),(7,0),(7,7)}
    scored = []
    for (r, c) in moves:
        score = 0
        if (r, c) in corners:
            score += 10000
        # simple local gain: how many pieces flipped
        tmp = copy.deepcopy(game)
        flipped = tmp.make_move(r, c, player)
        score += flipped * 10
        score += POSITION_WEIGHTS[r][c]
        scored.append(((r, c), score))
    scored.sort(key=lambda x: x[1], reverse=True)
    return [m for (m, _) in scored]

def minimax_ab(game: Othello, depth: int, alpha: int, beta: int, timer: SearchTimer) -> int:
    """
    Alpha-beta minimax with transposition table and time checks.
    Returns evaluation from BLACK's perspective.
    """
    # Time check
    if timer.time_up():
        # when time's up, fallback to static eval
        return game.evaluate_board(1)

    key = game.zobrist_key()
    tt_entry = TT.get(key)
    if tt_entry is not None:
        tt_depth, tt_value = tt_entry
        if tt_depth >= depth:
            return tt_value

    if depth == 0 or game.is_terminal():
        val = game.evaluate_board(1)
        TT[key] = (depth, val)
        return val

    moves = game.get_valid_moves(game.current_player)
    if not moves:
        # skip turn
        newg = copy.deepcopy(game)
        newg.current_player = -newg.current_player
        val = minimax_ab(newg, depth, alpha, beta, timer)
        TT[key] = (depth, val)
        return val

    # move ordering
    moves = order_moves(game, moves, game.current_player)

    if game.current_player == 1:
        value = float('-inf')
        for (r, c) in moves:
            newg = copy.deepcopy(game)
            newg.make_move(r, c, 1)
            val = minimax_ab(newg, depth - 1, alpha, beta, timer)
            if val > value:
                value = val
            if value > alpha:
                alpha = value
            if alpha >= beta:
                break
        TT[key] = (depth, value)
        return value
    else:
        value = float('inf')
        for (r, c) in moves:
            newg = copy.deepcopy(game)
            newg.make_move(r, c, -1)
            val = minimax_ab(newg, depth - 1, alpha, beta, timer)
            if val < value:
                value = val
            if value < beta:
                beta = value
            if alpha >= beta:
                break
        TT[key] = (depth, value)
        return value

def ai_move(game: Othello, time_limit: float = 0.25) -> Optional[Tuple[int,int]]:
    """
    Iterative deepening with time limit. Returns best move found within time_limit seconds.
    Default time_limit is 0.25s (negligible waiting).
    """
    start_time = time.perf_counter()
    timer = SearchTimer(time_limit)
    timer.start_timer()
    TT.clear()

    moves = game.get_valid_moves(game.current_player)
    if not moves:
        return None

    best_move = moves[0]
    best_score = float('inf')  # AI (-1) minimizes black's eval
    depth = 1

    # iterative deepening loop
    try:
        while True:
            if timer.time_up():
                break
            current_best_move = None
            current_best_score = float('inf')
            # order top-level moves first to improve alpha-beta
            ordered = order_moves(game, moves, game.current_player)
            for (r, c) in ordered:
                if timer.time_up():
                    break
                newg = copy.deepcopy(game)
                newg.make_move(r, c, -1)
                score = minimax_ab(newg, depth - 1, float('-inf'), float('inf'), timer)
                # AI is minimizing
                if score < current_best_score:
                    current_best_score = score
                    current_best_move = (r, c)
            # if we completed this depth search (time not up immediately), accept results
            if not timer.time_up() and current_best_move is not None:
                best_move = current_best_move
                best_score = current_best_score
            depth += 1
            # safety cap to avoid runaway depth
            if depth > 60:
                break
    except Exception:
        # any unexpected error -> fallback to best found
        pass

    # Apply chosen move
    if best_move:
        game.make_move(best_move[0], best_move[1], game.current_player)
    return best_move

# Game Loop
def play_game():
    game = Othello()
    while not game.is_terminal():
        game.display_board()
        if game.current_player == 1:  # Human
            valid = game.get_valid_moves(1)
            if not valid:
                print("No moves for Human (Black). Skipping turn.")
                game.current_player = -1
                continue
            print("Your turn (black). Enter row col (e.g., 2 3): ")
            try:
                r, c = map(int, input().split())
                if (r, c) not in valid:
                    print("Invalid move! Try again.")
                    continue
                game.make_move(r, c, 1)
            except Exception as e:
                print("Invalid input!", e)
                continue
        else:  # AI
            valid = game.get_valid_moves(-1)
            if not valid:
                print("No moves for AI (White). Skipping turn.")
                game.current_player = 1
                continue
            print("AI thinking ...")
            # DEFAULT: 0.25s for negligible waiting. Increase if you want stronger AI.
            move = ai_move(game, time_limit=0.25)
            print(f"AI moves to {move}")

    game.display_board()
    winner = game.get_winner()
    if winner == 1:
        print("Human (Black) wins!")
    elif winner == -1:
        print("AI (White) wins!")
    else:
        print("Draw!")

if __name__ == "__main__":
    play_game()
