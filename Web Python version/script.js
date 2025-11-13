// script.js
const API_BASE = 'https://fastapi-eta-seven.vercel.app';
let currentState = null;

async function fetchStatus() {
    try {
        const response = await fetch(`${API_BASE}/status`);
        if (!response.ok) {
            throw new Error('Failed to fetch status');
        }
        currentState = await response.json();
        renderBoard();
        updateUI();
    } catch (error) {
        console.error('Error fetching status:', error);
        document.getElementById('game-message').textContent = 'Connection error. Please start the server.';
    }
}

function renderBoard() {
    const boardEl = document.getElementById('board');
    boardEl.innerHTML = '';
    for (let r = 0; r < 8; r++) {
        const rowEl = document.createElement('div');
        rowEl.className = 'row';
        for (let c = 0; c < 8; c++) {
            const cellEl = document.createElement('div');
            cellEl.className = 'cell';
            cellEl.dataset.row = r;
            cellEl.dataset.col = c;

            const val = currentState.board[r][c];
            if (val === 1) {
                cellEl.classList.add('black');
            } else if (val === -1) {
                cellEl.classList.add('white');
            } else {
                cellEl.classList.add('empty');
            }

            if (currentState.valid_moves && currentState.valid_moves.some(([mr, mc]) => mr === r && mc === c)) {
                cellEl.classList.add('valid');
            }

            cellEl.addEventListener('click', handleCellClick);
            rowEl.appendChild(cellEl);
        }
        boardEl.appendChild(rowEl);
    }
}

function handleCellClick(event) {
    const row = parseInt(event.target.dataset.row);
    const col = parseInt(event.target.dataset.col);
    if (currentState.game_over || currentState.current_player !== 1) return;
    if (!currentState.valid_moves.some(([mr, mc]) => mr === row && mc === col)) return;

    makeMove(row, col);
}

async function makeMove(row, col) {
    try {
        const response = await fetch(`${API_BASE}/move`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ row, col })
        });
        if (!response.ok) {
            const error = await response.json();
            alert(error.error || 'Invalid move');
            return;
        }
        currentState = await response.json();
        renderBoard();
        updateUI();
    } catch (error) {
        console.error('Error making move:', error);
    }
}

function updateUI() {
    if (!currentState) return;

    document.getElementById('black-count').textContent = currentState.black_pieces;
    document.getElementById('white-count').textContent = currentState.white_pieces;

    const playerName = currentState.current_player === 1 ? 'Black' : 'White (AI thinking...)';
    document.getElementById('current-player').textContent = `Current player: ${playerName}`;

    const messageEl = document.getElementById('game-message');
    if (currentState.game_over) {
        let message = '';
        if (currentState.winner === 1) {
            message = 'Black (You) win!';
        } else if (currentState.winner === -1) {
            message = 'White (AI) wins!';
        } else {
            message = 'It\'s a draw!';
        }
        messageEl.textContent = message;
    } else {
        messageEl.textContent = '';
    }
}

document.getElementById('new-game').addEventListener('click', async () => {
    try {
        await fetch(`${API_BASE}/new_game`, { method: 'POST' });
        fetchStatus();
    } catch (error) {
        console.error('Error starting new game:', error);
    }
});

// Initialize
fetchStatus();