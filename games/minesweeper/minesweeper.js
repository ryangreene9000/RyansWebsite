/**
 * Minesweeper Game - JavaScript/Canvas Implementation
 * A complete Minesweeper clone for browser play
 * By Ryan Greene
 * 
 * Features:
 * - Randomized board and mine generation
 * - Neighbor mine-count algorithm
 * - Recursive flood-fill reveal
 * - Flagging system
 * - Win/Loss detection
 * - Timer
 * - Multiple difficulty levels
 */

(function() {
    'use strict';

    // ============================================
    // Configuration
    // ============================================
    const CONFIG = {
        TILE_SIZE: 32,
        HEADER_HEIGHT: 60,
        DIFFICULTIES: {
            easy: { cols: 9, rows: 9, mines: 10, name: 'Easy' },
            medium: { cols: 16, rows: 16, mines: 40, name: 'Medium' },
            hard: { cols: 24, rows: 16, mines: 70, name: 'Hard' }
        },
        COLORS: {
            hidden: '#c0c0c0',
            hiddenLight: '#ffffff',
            hiddenDark: '#808080',
            revealed: '#bdbdbd',
            revealedBorder: '#7d7d7d',
            mine: '#ff0000',
            flag: '#ff0000',
            numbers: ['#0000ff', '#008000', '#ff0000', '#000080', '#800000', '#008080', '#000000', '#808080'],
            header: '#c0c0c0',
            headerBorder: '#808080',
            display: '#000000',
            displayText: '#ff0000'
        }
    };

    // ============================================
    // Tile Class
    // ============================================
    class Tile {
        constructor() {
            this.hasMine = false;
            this.state = 'hidden'; // 'hidden', 'revealed', 'flagged'
            this.neighborMines = 0;
        }

        isHidden() { return this.state === 'hidden'; }
        isRevealed() { return this.state === 'revealed'; }
        isFlagged() { return this.state === 'flagged'; }
    }

    // ============================================
    // Board Class
    // ============================================
    class Board {
        constructor(cols, rows, mineCount) {
            this.cols = cols;
            this.rows = rows;
            this.mineCount = mineCount;
            this.tiles = [];
            this.revealedCount = 0;
            this.flagCount = 0;
            this.gameOver = false;
            this.gameWon = false;
            this.firstClick = true;
            this.reset();
        }

        reset() {
            this.tiles = [];
            for (let i = 0; i < this.cols * this.rows; i++) {
                this.tiles.push(new Tile());
            }
            this.revealedCount = 0;
            this.flagCount = 0;
            this.gameOver = false;
            this.gameWon = false;
            this.firstClick = true;
        }

        generateMines(safeX, safeY) {
            // Create list of all positions except safe zone (3x3 around first click)
            const positions = [];
            for (let i = 0; i < this.cols * this.rows; i++) {
                const x = i % this.cols;
                const y = Math.floor(i / this.cols);
                if (Math.abs(x - safeX) > 1 || Math.abs(y - safeY) > 1) {
                    positions.push(i);
                }
            }

            // Shuffle using Fisher-Yates
            for (let i = positions.length - 1; i > 0; i--) {
                const j = Math.floor(Math.random() * (i + 1));
                [positions[i], positions[j]] = [positions[j], positions[i]];
            }

            // Place mines
            const minesToPlace = Math.min(this.mineCount, positions.length);
            for (let i = 0; i < minesToPlace; i++) {
                this.tiles[positions[i]].hasMine = true;
            }

            // Calculate neighbor counts
            this.calculateNeighborCounts();
            this.firstClick = false;
        }

        calculateNeighborCounts() {
            for (let y = 0; y < this.rows; y++) {
                for (let x = 0; x < this.cols; x++) {
                    if (!this.getTile(x, y).hasMine) {
                        let count = 0;
                        for (let dy = -1; dy <= 1; dy++) {
                            for (let dx = -1; dx <= 1; dx++) {
                                if (dx === 0 && dy === 0) continue;
                                const nx = x + dx, ny = y + dy;
                                if (this.isValid(nx, ny) && this.getTile(nx, ny).hasMine) {
                                    count++;
                                }
                            }
                        }
                        this.getTile(x, y).neighborMines = count;
                    }
                }
            }
        }

        reveal(x, y) {
            if (!this.isValid(x, y)) return;

            const tile = this.getTile(x, y);
            if (tile.isRevealed() || tile.isFlagged()) return;

            // First click - generate mines
            if (this.firstClick) {
                this.generateMines(x, y);
            }

            tile.state = 'revealed';
            this.revealedCount++;

            // Hit a mine - game over
            if (tile.hasMine) {
                this.gameOver = true;
                this.revealAllMines();
                return;
            }

            // Flood fill for empty tiles
            if (tile.neighborMines === 0) {
                for (let dy = -1; dy <= 1; dy++) {
                    for (let dx = -1; dx <= 1; dx++) {
                        if (dx === 0 && dy === 0) continue;
                        this.reveal(x + dx, y + dy);
                    }
                }
            }

            // Check win condition
            this.checkWin();
        }

        toggleFlag(x, y) {
            if (!this.isValid(x, y)) return;

            const tile = this.getTile(x, y);
            if (tile.isRevealed()) return;

            if (tile.isFlagged()) {
                tile.state = 'hidden';
                this.flagCount--;
            } else {
                tile.state = 'flagged';
                this.flagCount++;
            }
        }

        chord(x, y) {
            if (!this.isValid(x, y)) return;

            const tile = this.getTile(x, y);
            if (!tile.isRevealed() || tile.neighborMines === 0) return;

            // Count adjacent flags
            let flaggedCount = 0;
            for (let dy = -1; dy <= 1; dy++) {
                for (let dx = -1; dx <= 1; dx++) {
                    if (dx === 0 && dy === 0) continue;
                    const nx = x + dx, ny = y + dy;
                    if (this.isValid(nx, ny) && this.getTile(nx, ny).isFlagged()) {
                        flaggedCount++;
                    }
                }
            }

            // If flags match neighbor count, reveal all unflagged neighbors
            if (flaggedCount === tile.neighborMines) {
                for (let dy = -1; dy <= 1; dy++) {
                    for (let dx = -1; dx <= 1; dx++) {
                        if (dx === 0 && dy === 0) continue;
                        const nx = x + dx, ny = y + dy;
                        if (this.isValid(nx, ny) && !this.getTile(nx, ny).isFlagged()) {
                            this.reveal(nx, ny);
                        }
                    }
                }
            }
        }

        revealAllMines() {
            for (const tile of this.tiles) {
                if (tile.hasMine) {
                    tile.state = 'revealed';
                }
            }
        }

        checkWin() {
            const safeTiles = this.cols * this.rows - this.mineCount;
            if (this.revealedCount >= safeTiles) {
                this.gameWon = true;
                this.gameOver = true;
                // Flag all remaining mines
                for (const tile of this.tiles) {
                    if (tile.hasMine && !tile.isFlagged()) {
                        tile.state = 'flagged';
                        this.flagCount++;
                    }
                }
            }
        }

        isValid(x, y) {
            return x >= 0 && x < this.cols && y >= 0 && y < this.rows;
        }

        getTile(x, y) {
            return this.tiles[y * this.cols + x];
        }
    }

    // ============================================
    // Game Class
    // ============================================
    class Game {
        constructor(canvasId, difficulty = 'medium') {
            this.canvas = document.getElementById(canvasId);
            this.ctx = this.canvas.getContext('2d');
            this.difficulty = CONFIG.DIFFICULTIES[difficulty];
            this.board = new Board(this.difficulty.cols, this.difficulty.rows, this.difficulty.mines);
            this.gameTime = 0;
            this.timerRunning = false;
            this.timerInterval = null;
            this.mouseDown = false;

            this.resize();
            this.setupEventListeners();
            this.render();
        }

        resize() {
            const width = this.difficulty.cols * CONFIG.TILE_SIZE;
            const height = this.difficulty.rows * CONFIG.TILE_SIZE + CONFIG.HEADER_HEIGHT;
            this.canvas.width = width;
            this.canvas.height = height;
            
            // Update wrapper size if it exists
            const wrapper = document.getElementById('game-wrapper');
            if (wrapper) {
                wrapper.style.width = width + 8 + 'px';
            }
        }

        setupEventListeners() {
            // Prevent context menu
            this.canvas.addEventListener('contextmenu', e => e.preventDefault());

            // Mouse events
            this.canvas.addEventListener('mousedown', e => this.handleMouseDown(e));
            this.canvas.addEventListener('mouseup', e => this.handleMouseUp(e));

            // Touch events for mobile
            this.canvas.addEventListener('touchstart', e => this.handleTouchStart(e));
            this.canvas.addEventListener('touchend', e => this.handleTouchEnd(e));

            // Keyboard
            document.addEventListener('keydown', e => this.handleKeyDown(e));
        }

        handleMouseDown(e) {
            this.mouseDown = true;
        }

        handleMouseUp(e) {
            if (!this.mouseDown) return;
            this.mouseDown = false;

            const rect = this.canvas.getBoundingClientRect();
            const scaleX = this.canvas.width / rect.width;
            const scaleY = this.canvas.height / rect.height;
            const mouseX = (e.clientX - rect.left) * scaleX;
            const mouseY = (e.clientY - rect.top) * scaleY;

            this.handleClick(mouseX, mouseY, e.button);
        }

        handleTouchStart(e) {
            e.preventDefault();
            this.touchStartTime = Date.now();
        }

        handleTouchEnd(e) {
            e.preventDefault();
            const touch = e.changedTouches[0];
            const rect = this.canvas.getBoundingClientRect();
            const scaleX = this.canvas.width / rect.width;
            const scaleY = this.canvas.height / rect.height;
            const touchX = (touch.clientX - rect.left) * scaleX;
            const touchY = (touch.clientY - rect.top) * scaleY;

            // Long press = flag, short tap = reveal
            const holdTime = Date.now() - this.touchStartTime;
            const button = holdTime > 500 ? 2 : 0;

            this.handleClick(touchX, touchY, button);
        }

        handleClick(x, y, button) {
            // Header click - check for face button (restart)
            if (y < CONFIG.HEADER_HEIGHT) {
                const centerX = this.canvas.width / 2;
                if (Math.abs(x - centerX) < 25) {
                    this.reset();
                }
                return;
            }

            if (this.board.gameOver) return;

            const tileX = Math.floor(x / CONFIG.TILE_SIZE);
            const tileY = Math.floor((y - CONFIG.HEADER_HEIGHT) / CONFIG.TILE_SIZE);

            // Start timer on first click
            if (!this.timerRunning && this.board.firstClick) {
                this.startTimer();
            }

            if (button === 0) {
                // Left click - reveal
                this.board.reveal(tileX, tileY);
            } else if (button === 2) {
                // Right click - flag
                this.board.toggleFlag(tileX, tileY);
            } else if (button === 1) {
                // Middle click - chord
                this.board.chord(tileX, tileY);
            }

            if (this.board.gameOver) {
                this.stopTimer();
            }

            this.render();
        }

        handleKeyDown(e) {
            if (e.key === 'r' || e.key === 'R') {
                this.reset();
            } else if (e.key === '1') {
                this.changeDifficulty('easy');
            } else if (e.key === '2') {
                this.changeDifficulty('medium');
            } else if (e.key === '3') {
                this.changeDifficulty('hard');
            }
        }

        reset() {
            this.board.reset();
            this.gameTime = 0;
            this.stopTimer();
            this.render();
        }

        changeDifficulty(difficulty) {
            this.difficulty = CONFIG.DIFFICULTIES[difficulty];
            this.board = new Board(this.difficulty.cols, this.difficulty.rows, this.difficulty.mines);
            this.resize();
            this.reset();
        }

        startTimer() {
            this.timerRunning = true;
            this.timerInterval = setInterval(() => {
                this.gameTime++;
                if (this.gameTime > 999) this.gameTime = 999;
                this.renderHeader();
            }, 1000);
        }

        stopTimer() {
            this.timerRunning = false;
            if (this.timerInterval) {
                clearInterval(this.timerInterval);
                this.timerInterval = null;
            }
        }

        render() {
            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
            this.renderHeader();
            this.renderBoard();
        }

        renderHeader() {
            const ctx = this.ctx;
            const width = this.canvas.width;

            // Background
            ctx.fillStyle = CONFIG.COLORS.header;
            ctx.fillRect(0, 0, width, CONFIG.HEADER_HEIGHT);

            // Border
            ctx.strokeStyle = CONFIG.COLORS.headerBorder;
            ctx.lineWidth = 2;
            ctx.strokeRect(0, 0, width, CONFIG.HEADER_HEIGHT);

            // Mine counter (left)
            this.renderDigits(this.board.mineCount - this.board.flagCount, 10, 15);

            // Face button (center)
            const centerX = width / 2 - 20;
            ctx.fillStyle = '#ddd';
            ctx.fillRect(centerX, 10, 40, 40);
            ctx.strokeStyle = CONFIG.COLORS.headerBorder;
            ctx.strokeRect(centerX, 10, 40, 40);

            // Face emoji
            ctx.fillStyle = '#000';
            ctx.font = 'bold 24px Arial';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            let face = '🙂';
            if (this.board.gameOver) {
                face = this.board.gameWon ? '😎' : '😵';
            }
            ctx.fillText(face, centerX + 20, 30);

            // Timer (right)
            this.renderDigits(this.gameTime, width - 70, 15);
        }

        renderDigits(value, x, y) {
            const ctx = this.ctx;

            // Background
            ctx.fillStyle = CONFIG.COLORS.display;
            ctx.fillRect(x, y, 60, 34);

            // Text
            ctx.fillStyle = CONFIG.COLORS.displayText;
            ctx.font = 'bold 26px "Courier New", monospace';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            const displayValue = Math.max(-99, Math.min(999, value));
            const text = displayValue.toString().padStart(3, '0');
            ctx.fillText(text, x + 30, y + 17);
        }

        renderBoard() {
            for (let y = 0; y < this.board.rows; y++) {
                for (let x = 0; x < this.board.cols; x++) {
                    this.renderTile(x, y);
                }
            }
        }

        renderTile(x, y) {
            const ctx = this.ctx;
            const tile = this.board.getTile(x, y);
            const px = x * CONFIG.TILE_SIZE;
            const py = y * CONFIG.TILE_SIZE + CONFIG.HEADER_HEIGHT;
            const size = CONFIG.TILE_SIZE;

            if (tile.isRevealed()) {
                // Revealed tile
                ctx.fillStyle = CONFIG.COLORS.revealed;
                ctx.fillRect(px, py, size, size);
                ctx.strokeStyle = CONFIG.COLORS.revealedBorder;
                ctx.lineWidth = 1;
                ctx.strokeRect(px + 0.5, py + 0.5, size - 1, size - 1);

                if (tile.hasMine) {
                    // Draw mine
                    ctx.fillStyle = this.board.gameWon ? '#000' : CONFIG.COLORS.mine;
                    ctx.beginPath();
                    ctx.arc(px + size / 2, py + size / 2, size / 4, 0, Math.PI * 2);
                    ctx.fill();

                    // Mine spikes
                    ctx.strokeStyle = '#000';
                    ctx.lineWidth = 2;
                    for (let i = 0; i < 8; i++) {
                        const angle = (i * Math.PI) / 4;
                        ctx.beginPath();
                        ctx.moveTo(px + size / 2, py + size / 2);
                        ctx.lineTo(
                            px + size / 2 + Math.cos(angle) * size / 3,
                            py + size / 2 + Math.sin(angle) * size / 3
                        );
                        ctx.stroke();
                    }
                } else if (tile.neighborMines > 0) {
                    // Draw number
                    ctx.fillStyle = CONFIG.COLORS.numbers[tile.neighborMines - 1];
                    ctx.font = 'bold 20px Arial';
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.fillText(tile.neighborMines.toString(), px + size / 2, py + size / 2 + 2);
                }
            } else {
                // Hidden tile with 3D effect
                ctx.fillStyle = CONFIG.COLORS.hidden;
                ctx.fillRect(px, py, size, size);

                // Highlight (top-left)
                ctx.strokeStyle = CONFIG.COLORS.hiddenLight;
                ctx.lineWidth = 2;
                ctx.beginPath();
                ctx.moveTo(px + 1, py + size - 1);
                ctx.lineTo(px + 1, py + 1);
                ctx.lineTo(px + size - 1, py + 1);
                ctx.stroke();

                // Shadow (bottom-right)
                ctx.strokeStyle = CONFIG.COLORS.hiddenDark;
                ctx.beginPath();
                ctx.moveTo(px + size - 1, py + 1);
                ctx.lineTo(px + size - 1, py + size - 1);
                ctx.lineTo(px + 1, py + size - 1);
                ctx.stroke();

                if (tile.isFlagged()) {
                    // Draw flag
                    ctx.fillStyle = CONFIG.COLORS.flag;
                    ctx.font = 'bold 18px Arial';
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.fillText('🚩', px + size / 2, py + size / 2 + 1);
                }
            }
        }
    }

    // ============================================
    // Initialize Game
    // ============================================
    window.MinesweeperGame = Game;

    // Auto-initialize if canvas exists
    document.addEventListener('DOMContentLoaded', () => {
        const canvas = document.getElementById('game-canvas');
        if (canvas) {
            // Hide loading, show canvas
            const loadingOverlay = document.getElementById('loading-overlay');
            const demoNotice = document.getElementById('demo-notice');
            
            if (loadingOverlay) loadingOverlay.classList.add('hidden');
            if (demoNotice) demoNotice.classList.add('hidden');
            canvas.style.display = 'block';

            // Initialize game
            window.game = new Game('game-canvas', 'medium');

            // Add difficulty buttons if they exist
            document.querySelectorAll('[data-difficulty]').forEach(btn => {
                btn.addEventListener('click', () => {
                    window.game.changeDifficulty(btn.dataset.difficulty);
                });
            });
        }
    });

})();

