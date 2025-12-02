/**
 * Snake Game
 * A fully playable Snake clone in vanilla JavaScript
 * 
 * Features:
 * - Classic snake gameplay
 * - Arrow keys and WASD controls
 * - Score tracking with high score persistence
 * - Multiple speed settings
 * - Mobile touch controls
 * - Smooth animations
 */

(function() {
    'use strict';

    // ============================================
    // Configuration
    // ============================================
    
    const GRID_SIZE = 20;
    const CELL_SIZE = 20;
    const CANVAS_SIZE = GRID_SIZE * CELL_SIZE;
    
    // Colors
    const COLORS = {
        background: '#1a1a2e',
        grid: '#2a2a4e',
        snakeHead: '#22c55e',
        snakeBody: '#16a34a',
        snakeGlow: 'rgba(34, 197, 94, 0.3)',
        food: '#ef4444',
        foodGlow: 'rgba(239, 68, 68, 0.4)'
    };

    // Speed settings (ms per tick)
    const SPEEDS = {
        slow: 150,
        normal: 100,
        fast: 60
    };

    // Directions
    const DIRECTIONS = {
        UP: { x: 0, y: -1 },
        DOWN: { x: 0, y: 1 },
        LEFT: { x: -1, y: 0 },
        RIGHT: { x: 1, y: 0 }
    };

    // ============================================
    // Game State
    // ============================================
    
    let canvas, ctx;
    let snake = [];
    let food = null;
    let direction = DIRECTIONS.RIGHT;
    let nextDirection = DIRECTIONS.RIGHT;
    let score = 0;
    let highScore = 0;
    let gameRunning = false;
    let gamePaused = false;
    let gameOver = false;
    let gameLoop = null;
    let currentSpeed = 'normal';

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
    const highScoreEl = document.getElementById('high-score');
    const lengthEl = document.getElementById('length');
    const speedButtons = document.querySelectorAll('.speed-btn');

    // ============================================
    // Initialization
    // ============================================
    
    function init() {
        canvas = document.getElementById('snake-canvas');
        ctx = canvas.getContext('2d');
        
        // Set canvas size
        canvas.width = CANVAS_SIZE;
        canvas.height = CANVAS_SIZE;

        // Load high score from localStorage
        const savedHighScore = localStorage.getItem('snakeHighScore');
        if (savedHighScore) {
            highScore = parseInt(savedHighScore, 10);
            updateStats();
        }

        // Event listeners
        document.addEventListener('keydown', handleKeyDown);
        startBtn.addEventListener('click', startGame);
        pauseBtn.addEventListener('click', togglePause);
        restartBtn.addEventListener('click', restartGame);

        // Speed buttons
        speedButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const speed = btn.dataset.speed;
                setSpeed(speed);
            });
        });

        // Mobile controls
        setupMobileControls();

        // Initial draw
        drawGrid();
    }

    function setSpeed(speed) {
        currentSpeed = speed;
        speedButtons.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.speed === speed);
        });

        // Restart game loop with new speed if running
        if (gameRunning && !gamePaused && !gameOver) {
            clearInterval(gameLoop);
            gameLoop = setInterval(update, SPEEDS[currentSpeed]);
        }
    }

    function createSnake() {
        const startX = Math.floor(GRID_SIZE / 2);
        const startY = Math.floor(GRID_SIZE / 2);
        snake = [
            { x: startX, y: startY },
            { x: startX - 1, y: startY },
            { x: startX - 2, y: startY }
        ];
        direction = DIRECTIONS.RIGHT;
        nextDirection = DIRECTIONS.RIGHT;
    }

    function spawnFood() {
        let newFood;
        do {
            newFood = {
                x: Math.floor(Math.random() * GRID_SIZE),
                y: Math.floor(Math.random() * GRID_SIZE)
            };
        } while (isSnakeCell(newFood.x, newFood.y));
        food = newFood;
    }

    function isSnakeCell(x, y) {
        return snake.some(segment => segment.x === x && segment.y === y);
    }

    // ============================================
    // Game Loop
    // ============================================
    
    function startGame() {
        createSnake();
        spawnFood();
        score = 0;
        gameOver = false;
        gamePaused = false;
        gameRunning = true;

        updateStats();
        hideOverlay();
        
        gameLoop = setInterval(update, SPEEDS[currentSpeed]);
    }

    function update() {
        if (!gameRunning || gamePaused || gameOver) return;

        // Update direction
        direction = nextDirection;

        // Calculate new head position
        const head = snake[0];
        const newHead = {
            x: head.x + direction.x,
            y: head.y + direction.y
        };

        // Check for collisions
        if (checkCollision(newHead)) {
            endGame();
            return;
        }

        // Add new head
        snake.unshift(newHead);

        // Check if food eaten
        if (newHead.x === food.x && newHead.y === food.y) {
            score += 10;
            updateStats();
            spawnFood();
        } else {
            // Remove tail if no food eaten
            snake.pop();
        }

        // Draw
        draw();
    }

    function checkCollision(pos) {
        // Wall collision
        if (pos.x < 0 || pos.x >= GRID_SIZE || pos.y < 0 || pos.y >= GRID_SIZE) {
            return true;
        }

        // Self collision (skip head)
        for (let i = 0; i < snake.length; i++) {
            if (snake[i].x === pos.x && snake[i].y === pos.y) {
                return true;
            }
        }

        return false;
    }

    function restartGame() {
        clearInterval(gameLoop);
        startGame();
    }

    function togglePause() {
        if (!gameRunning || gameOver) return;

        gamePaused = !gamePaused;
        pauseBtn.textContent = gamePaused ? 'Resume' : 'Pause';

        if (gamePaused) {
            clearInterval(gameLoop);
            showOverlay('Paused', 'Press P or Resume to continue', 'Resume');
            startBtn.onclick = togglePause;
        } else {
            hideOverlay();
            startBtn.onclick = startGame;
            gameLoop = setInterval(update, SPEEDS[currentSpeed]);
        }
    }

    function endGame() {
        gameOver = true;
        gameRunning = false;
        clearInterval(gameLoop);

        // Update high score
        if (score > highScore) {
            highScore = score;
            localStorage.setItem('snakeHighScore', highScore);
            updateStats();
            showOverlay('New High Score!', `Score: ${score}`, 'Play Again');
        } else {
            showOverlay('Game Over', `Score: ${score}`, 'Play Again');
        }
        startBtn.onclick = startGame;
    }

    // ============================================
    // Drawing
    // ============================================
    
    function draw() {
        // Clear canvas
        ctx.fillStyle = COLORS.background;
        ctx.fillRect(0, 0, CANVAS_SIZE, CANVAS_SIZE);

        // Draw grid
        drawGrid();

        // Draw food with glow
        drawFood();

        // Draw snake
        drawSnake();
    }

    function drawGrid() {
        ctx.strokeStyle = COLORS.grid;
        ctx.lineWidth = 0.5;

        for (let i = 0; i <= GRID_SIZE; i++) {
            // Vertical lines
            ctx.beginPath();
            ctx.moveTo(i * CELL_SIZE, 0);
            ctx.lineTo(i * CELL_SIZE, CANVAS_SIZE);
            ctx.stroke();

            // Horizontal lines
            ctx.beginPath();
            ctx.moveTo(0, i * CELL_SIZE);
            ctx.lineTo(CANVAS_SIZE, i * CELL_SIZE);
            ctx.stroke();
        }
    }

    function drawSnake() {
        snake.forEach((segment, index) => {
            const x = segment.x * CELL_SIZE;
            const y = segment.y * CELL_SIZE;
            const padding = 1;

            if (index === 0) {
                // Head - with glow
                ctx.shadowColor = COLORS.snakeGlow;
                ctx.shadowBlur = 10;
                ctx.fillStyle = COLORS.snakeHead;
                ctx.beginPath();
                ctx.roundRect(
                    x + padding,
                    y + padding,
                    CELL_SIZE - padding * 2,
                    CELL_SIZE - padding * 2,
                    4
                );
                ctx.fill();
                ctx.shadowBlur = 0;

                // Eyes
                drawEyes(x, y);
            } else {
                // Body
                const brightness = Math.max(0.6, 1 - (index * 0.03));
                ctx.fillStyle = `rgba(22, 163, 74, ${brightness})`;
                ctx.beginPath();
                ctx.roundRect(
                    x + padding + 1,
                    y + padding + 1,
                    CELL_SIZE - padding * 2 - 2,
                    CELL_SIZE - padding * 2 - 2,
                    3
                );
                ctx.fill();
            }
        });
    }

    function drawEyes(x, y) {
        const eyeSize = 3;
        const eyeOffset = 5;
        ctx.fillStyle = '#fff';

        // Position eyes based on direction
        let eye1X, eye1Y, eye2X, eye2Y;

        if (direction === DIRECTIONS.RIGHT) {
            eye1X = x + CELL_SIZE - eyeOffset - eyeSize;
            eye1Y = y + eyeOffset;
            eye2X = x + CELL_SIZE - eyeOffset - eyeSize;
            eye2Y = y + CELL_SIZE - eyeOffset - eyeSize;
        } else if (direction === DIRECTIONS.LEFT) {
            eye1X = x + eyeOffset;
            eye1Y = y + eyeOffset;
            eye2X = x + eyeOffset;
            eye2Y = y + CELL_SIZE - eyeOffset - eyeSize;
        } else if (direction === DIRECTIONS.UP) {
            eye1X = x + eyeOffset;
            eye1Y = y + eyeOffset;
            eye2X = x + CELL_SIZE - eyeOffset - eyeSize;
            eye2Y = y + eyeOffset;
        } else {
            eye1X = x + eyeOffset;
            eye1Y = y + CELL_SIZE - eyeOffset - eyeSize;
            eye2X = x + CELL_SIZE - eyeOffset - eyeSize;
            eye2Y = y + CELL_SIZE - eyeOffset - eyeSize;
        }

        ctx.beginPath();
        ctx.arc(eye1X + eyeSize/2, eye1Y + eyeSize/2, eyeSize/2, 0, Math.PI * 2);
        ctx.arc(eye2X + eyeSize/2, eye2Y + eyeSize/2, eyeSize/2, 0, Math.PI * 2);
        ctx.fill();
    }

    function drawFood() {
        if (!food) return;

        const x = food.x * CELL_SIZE;
        const y = food.y * CELL_SIZE;
        const centerX = x + CELL_SIZE / 2;
        const centerY = y + CELL_SIZE / 2;
        const radius = (CELL_SIZE / 2) - 2;

        // Glow effect
        ctx.shadowColor = COLORS.foodGlow;
        ctx.shadowBlur = 15;

        // Food (apple-like)
        ctx.fillStyle = COLORS.food;
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);
        ctx.fill();

        ctx.shadowBlur = 0;

        // Highlight
        ctx.fillStyle = 'rgba(255, 255, 255, 0.3)';
        ctx.beginPath();
        ctx.arc(centerX - 2, centerY - 2, radius / 3, 0, Math.PI * 2);
        ctx.fill();
    }

    // ============================================
    // UI Updates
    // ============================================
    
    function updateStats() {
        scoreEl.textContent = score;
        highScoreEl.textContent = highScore;
        lengthEl.textContent = snake.length;
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
        // Prevent scrolling
        if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', ' '].includes(e.key)) {
            e.preventDefault();
        }

        if (!gameRunning) return;

        switch (e.key) {
            case 'ArrowUp':
            case 'w':
            case 'W':
                if (direction !== DIRECTIONS.DOWN) {
                    nextDirection = DIRECTIONS.UP;
                }
                break;
            case 'ArrowDown':
            case 's':
            case 'S':
                if (direction !== DIRECTIONS.UP) {
                    nextDirection = DIRECTIONS.DOWN;
                }
                break;
            case 'ArrowLeft':
            case 'a':
            case 'A':
                if (direction !== DIRECTIONS.RIGHT) {
                    nextDirection = DIRECTIONS.LEFT;
                }
                break;
            case 'ArrowRight':
            case 'd':
            case 'D':
                if (direction !== DIRECTIONS.LEFT) {
                    nextDirection = DIRECTIONS.RIGHT;
                }
                break;
            case 'p':
            case 'P':
                togglePause();
                break;
            case 'r':
            case 'R':
                restartGame();
                break;
        }
    }

    function setupMobileControls() {
        const mobileUp = document.getElementById('mobile-up');
        const mobileDown = document.getElementById('mobile-down');
        const mobileLeft = document.getElementById('mobile-left');
        const mobileRight = document.getElementById('mobile-right');

        if (mobileUp) {
            mobileUp.addEventListener('touchstart', (e) => {
                e.preventDefault();
                if (direction !== DIRECTIONS.DOWN) {
                    nextDirection = DIRECTIONS.UP;
                }
            });
        }

        if (mobileDown) {
            mobileDown.addEventListener('touchstart', (e) => {
                e.preventDefault();
                if (direction !== DIRECTIONS.UP) {
                    nextDirection = DIRECTIONS.DOWN;
                }
            });
        }

        if (mobileLeft) {
            mobileLeft.addEventListener('touchstart', (e) => {
                e.preventDefault();
                if (direction !== DIRECTIONS.RIGHT) {
                    nextDirection = DIRECTIONS.LEFT;
                }
            });
        }

        if (mobileRight) {
            mobileRight.addEventListener('touchstart', (e) => {
                e.preventDefault();
                if (direction !== DIRECTIONS.LEFT) {
                    nextDirection = DIRECTIONS.RIGHT;
                }
            });
        }

        // Swipe controls
        let touchStartX = 0;
        let touchStartY = 0;

        canvas.addEventListener('touchstart', (e) => {
            touchStartX = e.touches[0].clientX;
            touchStartY = e.touches[0].clientY;
        });

        canvas.addEventListener('touchend', (e) => {
            if (!gameRunning) return;

            const touchEndX = e.changedTouches[0].clientX;
            const touchEndY = e.changedTouches[0].clientY;
            const dx = touchEndX - touchStartX;
            const dy = touchEndY - touchStartY;

            if (Math.abs(dx) > Math.abs(dy)) {
                // Horizontal swipe
                if (dx > 30 && direction !== DIRECTIONS.LEFT) {
                    nextDirection = DIRECTIONS.RIGHT;
                } else if (dx < -30 && direction !== DIRECTIONS.RIGHT) {
                    nextDirection = DIRECTIONS.LEFT;
                }
            } else {
                // Vertical swipe
                if (dy > 30 && direction !== DIRECTIONS.UP) {
                    nextDirection = DIRECTIONS.DOWN;
                } else if (dy < -30 && direction !== DIRECTIONS.DOWN) {
                    nextDirection = DIRECTIONS.UP;
                }
            }
        });
    }

    // ============================================
    // Polyfill for roundRect
    // ============================================
    
    if (!CanvasRenderingContext2D.prototype.roundRect) {
        CanvasRenderingContext2D.prototype.roundRect = function(x, y, w, h, r) {
            if (w < 2 * r) r = w / 2;
            if (h < 2 * r) r = h / 2;
            this.moveTo(x + r, y);
            this.arcTo(x + w, y, x + w, y + h, r);
            this.arcTo(x + w, y + h, x, y + h, r);
            this.arcTo(x, y + h, x, y, r);
            this.arcTo(x, y, x + w, y, r);
            this.closePath();
            return this;
        };
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

