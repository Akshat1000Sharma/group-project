# main.py
import copy
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Tuple
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

BOARD_SIZE = 8
INITIAL_BOARD = [[0] * BOARD_SIZE for _ in range(BOARD_SIZE)]
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

class Othello:
    def __init__(self, mode='ai'):
        self.board = copy.deepcopy(INITIAL_BOARD)
        self.current_player = 1  # Human starts (black)
        self.game_over = False
        self.mode = mode

    def get_valid_moves(self, player: int) -> List[Tuple[int, int]]:
        """Find all valid moves for the player."""
        moves = []
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if self.board[r][c] == 0:  # Empty cell
                    for dr, dc in directions:
                        if self._is_valid_flip(r, c, dr, dc, player):
                            moves.append((r, c))
                            break  # Valid if at least one direction flips
        return list(set(moves))  # Remove duplicates

    def _is_valid_flip(self, r: int, c: int, dr: int, dc: int, player: int) -> bool:
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

    def make_move(self, r: int, c: int, player: int) -> bool:
        """Place piece and flip opponents."""
        if (r, c) not in self.get_valid_moves(player):
            return False
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
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

    def evaluate_board(self, player: int) -> int:
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

    def is_terminal(self) -> bool:
        """Check if game over (no moves for both players)."""
        return len(self.get_valid_moves(self.current_player)) == 0 and \
               len(self.get_valid_moves(-self.current_player)) == 0

    def get_winner(self) -> int:
        """Return winner: 1 black, -1 white, 0 draw."""
        black = sum(1 for row in self.board for cell in row if cell == 1)
        white = sum(1 for row in self.board for cell in row if cell == -1)
        if black > white:
            return 1
        elif white > black:
            return -1
        return 0

def minimax(game: Othello, depth: int, alpha: float, beta: float, maximizing_player: bool) -> int:
    """Minimax with Alpha-Beta Pruning. Evaluation from black's (1) perspective."""
    if depth == 0 or game.is_terminal():
        return game.evaluate_board(1)

    moves = game.get_valid_moves(game.current_player)
    if len(moves) == 0:
        # Skip turn (other player has moves, since not terminal)
        current = game.current_player
        game.current_player = -current
        val = minimax(game, depth, alpha, beta, not maximizing_player)
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
    """AI selects best move using Minimax (AI is white, minimizes black's score)."""
    best_score = float('inf')
    best_move = None
    moves = game.get_valid_moves(game.current_player)  # -1 for white
    for r, c in moves:
        new_game = copy.deepcopy(game)
        new_game.make_move(r, c, game.current_player)  # Now black's turn
        score = minimax(new_game, depth - 1, float('-inf'), float('inf'), True)  # Black maximizes
        if score < best_score:
            best_score = score
            best_move = (r, c)
    if best_move:
        game.make_move(best_move[0], best_move[1], game.current_player)
    return best_move

# Global game instance
game = Othello()

class Move(BaseModel):
    row: int
    col: int

class NewGameRequest(BaseModel):
    mode: str

def get_status() -> dict:
    winner = game.get_winner() if game.game_over else None
    valid_moves = game.get_valid_moves(game.current_player)
    black_count = sum(1 for row in game.board for cell in row if cell == 1)
    white_count = sum(1 for row in game.board for cell in row if cell == -1)
    return {
        "board": game.board,
        "current_player": game.current_player,
        "game_over": game.game_over,
        "winner": winner,
        "valid_moves": valid_moves,
        "black_pieces": black_count,
        "white_pieces": white_count
    }

@app.get("/status")
async def status():
    return get_status()

@app.post("/move")
async def make_move(move: Move):
    if game.mode == 'ai' and game.current_player != 1:
        raise HTTPException(status_code=403, detail="Not your turn")
    success = game.make_move(move.row, move.col, game.current_player)
    if not success:
        raise HTTPException(status_code=400, detail="Invalid move")
    
    # Handle skips and AI turns
    while not game.is_terminal():
        next_player = game.current_player
        valid_moves_count = len(game.get_valid_moves(next_player))
        if valid_moves_count == 0:
            game.current_player = -next_player
            continue
        if game.mode == 'ai' and next_player == -1:
            ai_move(game)
        else:
            break  # Human's turn next
    
    game.game_over = game.is_terminal()
    return get_status()

@app.post("/new_game")
async def new_game(request: NewGameRequest):
    global game
    game = Othello(mode=request.mode)
    return {"message": f"New game started in {request.mode} mode"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)