/**
 * Tetris Game
 * A fully playable Tetris clone in vanilla JavaScript
 * 
 * Features:
 * - Classic gameplay with 7 tetromino types
 * - Rotation, soft drop, hard drop
 * - Line clearing and scoring
 * - Level progression with increasing speed
 * - Next piece preview
 * - Mobile touch controls
 */

(function() {
    'use strict';

    // ============================================
    // Configuration
    // ============================================
    
    const COLS = 10;
    const ROWS = 20;
    const BLOCK_SIZE = 30;
    const PREVIEW_BLOCK_SIZE = 25;
    
    // Colors for each piece type
    const COLORS = {
        I: '#00f5ff',  // Cyan
        O: '#ffd700',  // Yellow
        T: '#9b59b6',  // Purple
        S: '#2ecc71',  // Green
        Z: '#e74c3c',  // Red
        J: '#3498db',  // Blue
        L: '#e67e22'   // Orange
    };

    // Tetromino shapes (rotations)
    const SHAPES = {
        I: [
            [[0,0,0,0], [1,1,1,1], [0,0,0,0], [0,0,0,0]],
            [[0,0,1,0], [0,0,1,0], [0,0,1,0], [0,0,1,0]],
            [[0,0,0,0], [0,0,0,0], [1,1,1,1], [0,0,0,0]],
            [[0,1,0,0], [0,1,0,0], [0,1,0,0], [0,1,0,0]]
        ],
        O: [
            [[1,1], [1,1]],
            [[1,1], [1,1]],
            [[1,1], [1,1]],
            [[1,1], [1,1]]
        ],
        T: [
            [[0,1,0], [1,1,1], [0,0,0]],
            [[0,1,0], [0,1,1], [0,1,0]],
            [[0,0,0], [1,1,1], [0,1,0]],
            [[0,1,0], [1,1,0], [0,1,0]]
        ],
        S: [
            [[0,1,1], [1,1,0], [0,0,0]],
            [[0,1,0], [0,1,1], [0,0,1]],
            [[0,0,0], [0,1,1], [1,1,0]],
            [[1,0,0], [1,1,0], [0,1,0]]
        ],
        Z: [
            [[1,1,0], [0,1,1], [0,0,0]],
            [[0,0,1], [0,1,1], [0,1,0]],
            [[0,0,0], [1,1,0], [0,1,1]],
            [[0,1,0], [1,1,0], [1,0,0]]
        ],
        J: [
            [[1,0,0], [1,1,1], [0,0,0]],
            [[0,1,1], [0,1,0], [0,1,0]],
            [[0,0,0], [1,1,1], [0,0,1]],
            [[0,1,0], [0,1,0], [1,1,0]]
        ],
        L: [
            [[0,0,1], [1,1,1], [0,0,0]],
            [[0,1,0], [0,1,0], [0,1,1]],
            [[0,0,0], [1,1,1], [1,0,0]],
            [[1,1,0], [0,1,0], [0,1,0]]
        ]
    };

    const PIECE_TYPES = ['I', 'O', 'T', 'S', 'Z', 'J', 'L'];

    // Scoring
    const POINTS = {
        1: 100,    // Single
        2: 300,    // Double
        3: 500,    // Triple
        4: 800     // Tetris
    };

    const SOFT_DROP_POINTS = 1;
    const HARD_DROP_POINTS = 2;

    // Speed (ms per drop) by level
    const SPEEDS = [
        800, 720, 630, 550, 470, 380, 300, 220, 130, 100,
        80, 80, 80, 70, 70, 70, 50, 50, 50, 30
    ];

    // ============================================
    // Game State
    // ============================================
    
    let canvas, ctx;
    let nextCanvas, nextCtx;
    let board = [];
    let currentPiece = null;
    let nextPiece = null;
    let score = 0;
    let level = 1;
    let lines = 0;
    let gameRunning = false;
    let gamePaused = false;
    let gameOver = false;
    let dropInterval = null;
    let lastDropTime = 0;

    // ============================================
    // DOM Elements
    // ============================================
    
    const overlay = document.getElementById('game-overlay');
    const overlayTitle = document.getElementById('overlay-title');
    const overlayMessage = document.getElementById('overlay-message');
    const startBtn = document.getElementById('start-btn');
    const pauseBtn = document.getElementById('pause-btn');
    const restartBtn = document.getElementById('restart-btn');
    const scoreEl = document.getElementById('score');
    const levelEl = document.getElementById('level');
    const linesEl = document.getElementById('lines');

    // ============================================
    // Initialization
    // ============================================
    
    function init() {
        canvas = document.getElementById('tetris-canvas');
        ctx = canvas.getContext('2d');
        nextCanvas = document.getElementById('next-canvas');
        nextCtx = nextCanvas.getContext('2d');

        // Set canvas size based on device
        resizeCanvas();
        window.addEventListener('resize', resizeCanvas);

        // Event listeners
        document.addEventListener('keydown', handleKeyDown);
        startBtn.addEventListener('click', startGame);
        pauseBtn.addEventListener('click', togglePause);
        restartBtn.addEventListener('click', restartGame);

        // Mobile controls
        setupMobileControls();

        // Initial draw
        drawBoard();
    }

    function resizeCanvas() {
        const maxWidth = Math.min(window.innerWidth - 40, 300);
        const scale = maxWidth / (COLS * BLOCK_SIZE);
        
        if (window.innerWidth <= 768) {
            canvas.style.width = maxWidth + 'px';
            canvas.style.height = (maxWidth * 2) + 'px';
        }
    }

    function createBoard() {
        board = [];
        for (let row = 0; row < ROWS; row++) {
            board.push(new Array(COLS).fill(0));
        }
    }

    // ============================================
    // Game Loop
    // ============================================
    
    function startGame() {
        createBoard();
        score = 0;
        level = 1;
        lines = 0;
        gameOver = false;
        gamePaused = false;
        gameRunning = true;

        updateStats();
        spawnPiece();
        hideOverlay();
        
        lastDropTime = Date.now();
        gameLoop();
    }

    function gameLoop() {
        if (!gameRunning || gamePaused || gameOver) return;

        const now = Date.now();
        const speed = SPEEDS[Math.min(level - 1, SPEEDS.length - 1)];

        if (now - lastDropTime >= speed) {
            dropPiece();
            lastDropTime = now;
        }

        drawBoard();
        requestAnimationFrame(gameLoop);
    }

    function restartGame() {
        startGame();
    }

    function togglePause() {
        if (!gameRunning || gameOver) return;

        gamePaused = !gamePaused;
        pauseBtn.textContent = gamePaused ? 'Resume' : 'Pause';

        if (gamePaused) {
            showOverlay('Paused', 'Press P or Resume to continue', 'Resume');
            startBtn.onclick = togglePause;
        } else {
            hideOverlay();
            startBtn.onclick = startGame;
            lastDropTime = Date.now();
            gameLoop();
        }
    }

    function endGame() {
        gameOver = true;
        gameRunning = false;
        showOverlay('Game Over', `Final Score: ${score}`, 'Play Again');
        startBtn.onclick = startGame;
    }

    // ============================================
    // Piece Management
    // ============================================
    
    function createPiece(type) {
        return {
            type: type,
            shape: SHAPES[type][0],
            rotation: 0,
            x: Math.floor(COLS / 2) - Math.floor(SHAPES[type][0][0].length / 2),
            y: 0,
            color: COLORS[type]
        };
    }

    function getRandomPiece() {
        const type = PIECE_TYPES[Math.floor(Math.random() * PIECE_TYPES.length)];
        return createPiece(type);
    }

    function spawnPiece() {
        currentPiece = nextPiece || getRandomPiece();
        nextPiece = getRandomPiece();

        // Check if spawn position is valid
        if (!isValidPosition(currentPiece.x, currentPiece.y, currentPiece.shape)) {
            endGame();
            return;
        }

        drawNextPiece();
    }

    // ============================================
    // Movement & Collision
    // ============================================
    
    function isValidPosition(x, y, shape) {
        for (let row = 0; row < shape.length; row++) {
            for (let col = 0; col < shape[row].length; col++) {
                if (shape[row][col]) {
                    const newX = x + col;
                    const newY = y + row;

                    // Check bounds
                    if (newX < 0 || newX >= COLS || newY >= ROWS) {
                        return false;
                    }

                    // Check collision with placed pieces
                    if (newY >= 0 && board[newY][newX]) {
                        return false;
                    }
                }
            }
        }
        return true;
    }

    function movePiece(dx, dy) {
        if (!currentPiece || !gameRunning || gamePaused) return false;

        const newX = currentPiece.x + dx;
        const newY = currentPiece.y + dy;

        if (isValidPosition(newX, newY, currentPiece.shape)) {
            currentPiece.x = newX;
            currentPiece.y = newY;
            return true;
        }
        return false;
    }

    function rotatePiece() {
        if (!currentPiece || !gameRunning || gamePaused) return;

        const newRotation = (currentPiece.rotation + 1) % 4;
        const newShape = SHAPES[currentPiece.type][newRotation];

        // Try rotation, then wall kicks
        const kicks = [0, 1, -1, 2, -2];
        for (const kick of kicks) {
            if (isValidPosition(currentPiece.x + kick, currentPiece.y, newShape)) {
                currentPiece.x += kick;
                currentPiece.rotation = newRotation;
                currentPiece.shape = newShape;
                return;
            }
        }
    }

    function dropPiece() {
        if (!movePiece(0, 1)) {
            lockPiece();
        }
    }

    function hardDrop() {
        if (!currentPiece || !gameRunning || gamePaused) return;

        let dropDistance = 0;
        while (movePiece(0, 1)) {
            dropDistance++;
        }
        score += dropDistance * HARD_DROP_POINTS;
        updateStats();
        lockPiece();
    }

    function softDrop() {
        if (movePiece(0, 1)) {
            score += SOFT_DROP_POINTS;
            updateStats();
        }
    }

    function lockPiece() {
        // Place piece on board
        for (let row = 0; row < currentPiece.shape.length; row++) {
            for (let col = 0; col < currentPiece.shape[row].length; col++) {
                if (currentPiece.shape[row][col]) {
                    const boardY = currentPiece.y + row;
                    const boardX = currentPiece.x + col;
                    if (boardY >= 0) {
                        board[boardY][boardX] = currentPiece.color;
                    }
                }
            }
        }

        // Clear lines
        clearLines();

        // Spawn next piece
        spawnPiece();
    }

    // ============================================
    // Line Clearing
    // ============================================
    
    function clearLines() {
        let clearedLines = 0;

        for (let row = ROWS - 1; row >= 0; row--) {
            if (board[row].every(cell => cell !== 0)) {
                // Remove line
                board.splice(row, 1);
                // Add empty line at top
                board.unshift(new Array(COLS).fill(0));
                clearedLines++;
                row++; // Check same row again
            }
        }

        if (clearedLines > 0) {
            // Update score
            const points = POINTS[clearedLines] || 100;
            score += points * level;
            lines += clearedLines;

            // Level up every 10 lines
            const newLevel = Math.floor(lines / 10) + 1;
            if (newLevel > level) {
                level = Math.min(newLevel, 20);
            }

            updateStats();
        }
    }

    // ============================================
    // Drawing
    // ============================================
    
    function drawBoard() {
        // Clear canvas
        ctx.fillStyle = '#1a1a2e';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // Draw grid
        ctx.strokeStyle = '#2a2a4e';
        ctx.lineWidth = 0.5;
        for (let row = 0; row <= ROWS; row++) {
            ctx.beginPath();
            ctx.moveTo(0, row * BLOCK_SIZE);
            ctx.lineTo(COLS * BLOCK_SIZE, row * BLOCK_SIZE);
            ctx.stroke();
        }
        for (let col = 0; col <= COLS; col++) {
            ctx.beginPath();
            ctx.moveTo(col * BLOCK_SIZE, 0);
            ctx.lineTo(col * BLOCK_SIZE, ROWS * BLOCK_SIZE);
            ctx.stroke();
        }

        // Draw placed pieces
        for (let row = 0; row < ROWS; row++) {
            for (let col = 0; col < COLS; col++) {
                if (board[row][col]) {
                    drawBlock(ctx, col, row, board[row][col], BLOCK_SIZE);
                }
            }
        }

        // Draw current piece
        if (currentPiece && !gameOver) {
            // Draw ghost piece
            drawGhostPiece();

            // Draw actual piece
            for (let row = 0; row < currentPiece.shape.length; row++) {
                for (let col = 0; col < currentPiece.shape[row].length; col++) {
                    if (currentPiece.shape[row][col]) {
                        drawBlock(
                            ctx,
                            currentPiece.x + col,
                            currentPiece.y + row,
                            currentPiece.color,
                            BLOCK_SIZE
                        );
                    }
                }
            }
        }
    }

    function drawBlock(context, x, y, color, size) {
        const padding = 2;
        
        // Main block
        context.fillStyle = color;
        context.fillRect(
            x * size + padding,
            y * size + padding,
            size - padding * 2,
            size - padding * 2
        );

        // Highlight (top-left)
        context.fillStyle = 'rgba(255, 255, 255, 0.3)';
        context.fillRect(
            x * size + padding,
            y * size + padding,
            size - padding * 2,
            3
        );
        context.fillRect(
            x * size + padding,
            y * size + padding,
            3,
            size - padding * 2
        );

        // Shadow (bottom-right)
        context.fillStyle = 'rgba(0, 0, 0, 0.3)';
        context.fillRect(
            x * size + padding,
            y * size + size - padding - 3,
            size - padding * 2,
            3
        );
        context.fillRect(
            x * size + size - padding - 3,
            y * size + padding,
            3,
            size - padding * 2
        );
    }

    function drawGhostPiece() {
        if (!currentPiece) return;

        // Find ghost position
        let ghostY = currentPiece.y;
        while (isValidPosition(currentPiece.x, ghostY + 1, currentPiece.shape)) {
            ghostY++;
        }

        // Draw ghost
        ctx.globalAlpha = 0.3;
        for (let row = 0; row < currentPiece.shape.length; row++) {
            for (let col = 0; col < currentPiece.shape[row].length; col++) {
                if (currentPiece.shape[row][col]) {
                    drawBlock(
                        ctx,
                        currentPiece.x + col,
                        ghostY + row,
                        currentPiece.color,
                        BLOCK_SIZE
                    );
                }
            }
        }
        ctx.globalAlpha = 1;
    }

    function drawNextPiece() {
        // Clear
        nextCtx.fillStyle = '#1a1a2e';
        nextCtx.fillRect(0, 0, nextCanvas.width, nextCanvas.height);

        if (!nextPiece) return;

        // Center the piece
        const shape = nextPiece.shape;
        const offsetX = (nextCanvas.width - shape[0].length * PREVIEW_BLOCK_SIZE) / 2;
        const offsetY = (nextCanvas.height - shape.length * PREVIEW_BLOCK_SIZE) / 2;

        for (let row = 0; row < shape.length; row++) {
            for (let col = 0; col < shape[row].length; col++) {
                if (shape[row][col]) {
                    const x = offsetX / PREVIEW_BLOCK_SIZE + col;
                    const y = offsetY / PREVIEW_BLOCK_SIZE + row;
                    
                    nextCtx.fillStyle = nextPiece.color;
                    nextCtx.fillRect(
                        x * PREVIEW_BLOCK_SIZE + 2,
                        y * PREVIEW_BLOCK_SIZE + 2,
                        PREVIEW_BLOCK_SIZE - 4,
                        PREVIEW_BLOCK_SIZE - 4
                    );
                }
            }
        }
    }

    // ============================================
    // UI Updates
    // ============================================
    
    function updateStats() {
        scoreEl.textContent = score.toLocaleString();
        levelEl.textContent = level;
        linesEl.textContent = lines;
    }

    function showOverlay(title, message, buttonText) {
        overlayTitle.textContent = title;
        overlayMessage.textContent = message;
        startBtn.textContent = buttonText;
        overlay.classList.remove('hidden');
    }

    function hideOverlay() {
        overlay.classList.add('hidden');
    }

    // ============================================
    // Input Handling
    // ============================================
    
    function handleKeyDown(e) {
        if (!gameRunning) return;

        switch (e.key) {
            case 'ArrowLeft':
            case 'a':
            case 'A':
                e.preventDefault();
                movePiece(-1, 0);
                drawBoard();
                break;
            case 'ArrowRight':
            case 'd':
            case 'D':
                e.preventDefault();
                movePiece(1, 0);
                drawBoard();
                break;
            case 'ArrowDown':
            case 's':
            case 'S':
                e.preventDefault();
                softDrop();
                drawBoard();
                break;
            case 'ArrowUp':
            case 'w':
            case 'W':
                e.preventDefault();
                rotatePiece();
                drawBoard();
                break;
            case ' ':
                e.preventDefault();
                hardDrop();
                drawBoard();
                break;
            case 'p':
            case 'P':
                e.preventDefault();
                togglePause();
                break;
        }
    }

    function setupMobileControls() {
        const mobileLeft = document.getElementById('mobile-left');
        const mobileRight = document.getElementById('mobile-right');
        const mobileDown = document.getElementById('mobile-down');
        const mobileRotate = document.getElementById('mobile-rotate');
        const mobileDrop = document.getElementById('mobile-drop');

        if (mobileLeft) {
            mobileLeft.addEventListener('touchstart', (e) => {
                e.preventDefault();
                movePiece(-1, 0);
                drawBoard();
            });
        }

        if (mobileRight) {
            mobileRight.addEventListener('touchstart', (e) => {
                e.preventDefault();
                movePiece(1, 0);
                drawBoard();
            });
        }

        if (mobileDown) {
            mobileDown.addEventListener('touchstart', (e) => {
                e.preventDefault();
                softDrop();
                drawBoard();
            });
        }

        if (mobileRotate) {
            mobileRotate.addEventListener('touchstart', (e) => {
                e.preventDefault();
                rotatePiece();
                drawBoard();
            });
        }

        if (mobileDrop) {
            mobileDrop.addEventListener('touchstart', (e) => {
                e.preventDefault();
                hardDrop();
                drawBoard();
            });
        }
    }

    // ============================================
    // Start
    // ============================================
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();

