/**
 * Minesweeper Game
 * A complete Minesweeper clone built in modern C++ with SFML
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

#include <SFML/Graphics.hpp>
#include <SFML/Window.hpp>
#include <vector>
#include <random>
#include <chrono>
#include <string>
#include <algorithm>

// ============================================
// Game Constants
// ============================================
namespace Config {
    const int TILE_SIZE = 32;
    const int HEADER_HEIGHT = 60;
    
    // Difficulty settings: {cols, rows, mines}
    struct Difficulty {
        int cols;
        int rows;
        int mines;
        const char* name;
    };
    
    const Difficulty EASY = {9, 9, 10, "Easy"};
    const Difficulty MEDIUM = {16, 16, 40, "Medium"};
    const Difficulty HARD = {30, 16, 99, "Hard"};
}

// ============================================
// Tile Class
// ============================================
class Tile {
public:
    enum class State {
        Hidden,
        Revealed,
        Flagged
    };
    
    Tile() : hasMine(false), state(State::Hidden), neighborMines(0) {}
    
    bool hasMine;
    State state;
    int neighborMines;
    
    bool isHidden() const { return state == State::Hidden; }
    bool isRevealed() const { return state == State::Revealed; }
    bool isFlagged() const { return state == State::Flagged; }
};

// ============================================
// Board Class
// ============================================
class Board {
public:
    Board(int cols, int rows, int mineCount)
        : cols(cols), rows(rows), mineCount(mineCount),
          tiles(cols * rows), revealedCount(0), flagCount(0),
          gameOver(false), gameWon(false), firstClick(true) {}
    
    void reset() {
        tiles.assign(cols * rows, Tile());
        revealedCount = 0;
        flagCount = 0;
        gameOver = false;
        gameWon = false;
        firstClick = true;
    }
    
    void generateMines(int safeX, int safeY) {
        // Create list of all positions except safe zone
        std::vector<int> positions;
        for (int i = 0; i < cols * rows; ++i) {
            int x = i % cols;
            int y = i / cols;
            // Safe zone is 3x3 around first click
            if (std::abs(x - safeX) > 1 || std::abs(y - safeY) > 1) {
                positions.push_back(i);
            }
        }
        
        // Shuffle and place mines
        std::random_device rd;
        std::mt19937 gen(rd());
        std::shuffle(positions.begin(), positions.end(), gen);
        
        int minesToPlace = std::min(mineCount, static_cast<int>(positions.size()));
        for (int i = 0; i < minesToPlace; ++i) {
            tiles[positions[i]].hasMine = true;
        }
        
        // Calculate neighbor counts
        calculateNeighborCounts();
        firstClick = false;
    }
    
    void calculateNeighborCounts() {
        for (int y = 0; y < rows; ++y) {
            for (int x = 0; x < cols; ++x) {
                if (!getTile(x, y).hasMine) {
                    int count = 0;
                    for (int dy = -1; dy <= 1; ++dy) {
                        for (int dx = -1; dx <= 1; ++dx) {
                            if (dx == 0 && dy == 0) continue;
                            int nx = x + dx, ny = y + dy;
                            if (isValid(nx, ny) && getTile(nx, ny).hasMine) {
                                ++count;
                            }
                        }
                    }
                    getTile(x, y).neighborMines = count;
                }
            }
        }
    }
    
    void reveal(int x, int y) {
        if (!isValid(x, y)) return;
        
        Tile& tile = getTile(x, y);
        if (tile.isRevealed() || tile.isFlagged()) return;
        
        // First click - generate mines
        if (firstClick) {
            generateMines(x, y);
        }
        
        tile.state = Tile::State::Revealed;
        ++revealedCount;
        
        // Hit a mine - game over
        if (tile.hasMine) {
            gameOver = true;
            revealAllMines();
            return;
        }
        
        // Flood fill for empty tiles
        if (tile.neighborMines == 0) {
            for (int dy = -1; dy <= 1; ++dy) {
                for (int dx = -1; dx <= 1; ++dx) {
                    if (dx == 0 && dy == 0) continue;
                    reveal(x + dx, y + dy);
                }
            }
        }
        
        // Check win condition
        checkWin();
    }
    
    void toggleFlag(int x, int y) {
        if (!isValid(x, y)) return;
        
        Tile& tile = getTile(x, y);
        if (tile.isRevealed()) return;
        
        if (tile.isFlagged()) {
            tile.state = Tile::State::Hidden;
            --flagCount;
        } else {
            tile.state = Tile::State::Flagged;
            ++flagCount;
        }
    }
    
    void chord(int x, int y) {
        if (!isValid(x, y)) return;
        
        Tile& tile = getTile(x, y);
        if (!tile.isRevealed() || tile.neighborMines == 0) return;
        
        // Count adjacent flags
        int flaggedCount = 0;
        for (int dy = -1; dy <= 1; ++dy) {
            for (int dx = -1; dx <= 1; ++dx) {
                if (dx == 0 && dy == 0) continue;
                int nx = x + dx, ny = y + dy;
                if (isValid(nx, ny) && getTile(nx, ny).isFlagged()) {
                    ++flaggedCount;
                }
            }
        }
        
        // If flags match neighbor count, reveal all unflagged neighbors
        if (flaggedCount == tile.neighborMines) {
            for (int dy = -1; dy <= 1; ++dy) {
                for (int dx = -1; dx <= 1; ++dx) {
                    if (dx == 0 && dy == 0) continue;
                    int nx = x + dx, ny = y + dy;
                    if (isValid(nx, ny) && !getTile(nx, ny).isFlagged()) {
                        reveal(nx, ny);
                    }
                }
            }
        }
    }
    
    void revealAllMines() {
        for (auto& tile : tiles) {
            if (tile.hasMine) {
                tile.state = Tile::State::Revealed;
            }
        }
    }
    
    void checkWin() {
        int safeTiles = cols * rows - mineCount;
        if (revealedCount >= safeTiles) {
            gameWon = true;
            gameOver = true;
            // Flag all remaining mines
            for (auto& tile : tiles) {
                if (tile.hasMine && !tile.isFlagged()) {
                    tile.state = Tile::State::Flagged;
                    ++flagCount;
                }
            }
        }
    }
    
    bool isValid(int x, int y) const {
        return x >= 0 && x < cols && y >= 0 && y < rows;
    }
    
    Tile& getTile(int x, int y) {
        return tiles[y * cols + x];
    }
    
    const Tile& getTile(int x, int y) const {
        return tiles[y * cols + x];
    }
    
    int getCols() const { return cols; }
    int getRows() const { return rows; }
    int getMineCount() const { return mineCount; }
    int getFlagCount() const { return flagCount; }
    bool isGameOver() const { return gameOver; }
    bool isGameWon() const { return gameWon; }
    
private:
    int cols, rows, mineCount;
    std::vector<Tile> tiles;
    int revealedCount;
    int flagCount;
    bool gameOver;
    bool gameWon;
    bool firstClick;
};

// ============================================
// Game Class
// ============================================
class Game {
public:
    Game(const Config::Difficulty& difficulty)
        : difficulty(difficulty),
          board(difficulty.cols, difficulty.rows, difficulty.mines),
          window(sf::VideoMode(difficulty.cols * Config::TILE_SIZE, 
                              difficulty.rows * Config::TILE_SIZE + Config::HEADER_HEIGHT),
                "Minesweeper - Ryan Greene"),
          gameTime(0), timerRunning(false) {
        
        window.setFramerateLimit(60);
        loadAssets();
        reset();
    }
    
    void run() {
        while (window.isOpen()) {
            handleEvents();
            update();
            render();
        }
    }
    
private:
    void loadAssets() {
        // Load font
        if (!font.loadFromFile("assets/font.ttf")) {
            // Fallback to system font
            font.loadFromFile("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf");
        }
    }
    
    void reset() {
        board.reset();
        gameTime = 0;
        timerRunning = false;
        startTime = std::chrono::steady_clock::now();
    }
    
    void handleEvents() {
        sf::Event event;
        while (window.pollEvent(event)) {
            if (event.type == sf::Event::Closed) {
                window.close();
            }
            else if (event.type == sf::Event::KeyPressed) {
                if (event.key.code == sf::Keyboard::R) {
                    reset();
                }
                else if (event.key.code == sf::Keyboard::Escape) {
                    window.close();
                }
            }
            else if (event.type == sf::Event::MouseButtonPressed) {
                handleClick(event.mouseButton);
            }
        }
    }
    
    void handleClick(const sf::Event::MouseButtonEvent& mouse) {
        int x = mouse.x / Config::TILE_SIZE;
        int y = (mouse.y - Config::HEADER_HEIGHT) / Config::TILE_SIZE;
        
        // Header click - restart
        if (mouse.y < Config::HEADER_HEIGHT) {
            int centerX = window.getSize().x / 2;
            if (std::abs(mouse.x - centerX) < 25) {
                reset();
            }
            return;
        }
        
        if (board.isGameOver()) return;
        
        // Start timer on first click
        if (!timerRunning) {
            startTime = std::chrono::steady_clock::now();
            timerRunning = true;
        }
        
        if (mouse.button == sf::Mouse::Left) {
            board.reveal(x, y);
        }
        else if (mouse.button == sf::Mouse::Right) {
            board.toggleFlag(x, y);
        }
        else if (mouse.button == sf::Mouse::Middle) {
            board.chord(x, y);
        }
    }
    
    void update() {
        if (timerRunning && !board.isGameOver()) {
            auto now = std::chrono::steady_clock::now();
            gameTime = std::chrono::duration_cast<std::chrono::seconds>(now - startTime).count();
            if (gameTime > 999) gameTime = 999;
        }
    }
    
    void render() {
        window.clear(sf::Color(192, 192, 192));
        
        renderHeader();
        renderBoard();
        
        window.display();
    }
    
    void renderHeader() {
        // Background
        sf::RectangleShape header(sf::Vector2f(window.getSize().x, Config::HEADER_HEIGHT));
        header.setFillColor(sf::Color(192, 192, 192));
        header.setOutlineThickness(2);
        header.setOutlineColor(sf::Color(128, 128, 128));
        window.draw(header);
        
        // Mine counter (left)
        renderDigits(board.getMineCount() - board.getFlagCount(), 10, 15);
        
        // Face button (center)
        float centerX = window.getSize().x / 2.0f - 20;
        sf::RectangleShape faceBtn(sf::Vector2f(40, 40));
        faceBtn.setPosition(centerX, 10);
        faceBtn.setFillColor(sf::Color(220, 220, 220));
        faceBtn.setOutlineThickness(2);
        faceBtn.setOutlineColor(sf::Color(128, 128, 128));
        window.draw(faceBtn);
        
        // Face emoji
        sf::Text faceText;
        faceText.setFont(font);
        faceText.setCharacterSize(24);
        std::string face = board.isGameOver() ? (board.isGameWon() ? ":D" : "X(") : ":)";
        faceText.setString(face);
        faceText.setFillColor(sf::Color::Black);
        faceText.setPosition(centerX + 8, 14);
        window.draw(faceText);
        
        // Timer (right)
        renderDigits(gameTime, window.getSize().x - 65, 15);
    }
    
    void renderDigits(int value, float x, float y) {
        sf::RectangleShape bg(sf::Vector2f(55, 30));
        bg.setPosition(x, y);
        bg.setFillColor(sf::Color::Black);
        window.draw(bg);
        
        sf::Text text;
        text.setFont(font);
        text.setCharacterSize(22);
        
        char buffer[4];
        snprintf(buffer, 4, "%03d", std::max(-99, std::min(999, value)));
        text.setString(buffer);
        text.setFillColor(sf::Color::Red);
        text.setPosition(x + 5, y + 2);
        window.draw(text);
    }
    
    void renderBoard() {
        for (int y = 0; y < board.getRows(); ++y) {
            for (int x = 0; x < board.getCols(); ++x) {
                renderTile(x, y);
            }
        }
    }
    
    void renderTile(int x, int y) {
        const Tile& tile = board.getTile(x, y);
        float px = x * Config::TILE_SIZE;
        float py = y * Config::TILE_SIZE + Config::HEADER_HEIGHT;
        
        sf::RectangleShape rect(sf::Vector2f(Config::TILE_SIZE - 1, Config::TILE_SIZE - 1));
        rect.setPosition(px, py);
        
        if (tile.isRevealed()) {
            rect.setFillColor(sf::Color(189, 189, 189));
            rect.setOutlineThickness(1);
            rect.setOutlineColor(sf::Color(128, 128, 128));
            window.draw(rect);
            
            if (tile.hasMine) {
                // Draw mine
                sf::CircleShape mine(Config::TILE_SIZE / 4);
                mine.setFillColor(sf::Color::Black);
                mine.setPosition(px + Config::TILE_SIZE / 4, py + Config::TILE_SIZE / 4);
                window.draw(mine);
            } else if (tile.neighborMines > 0) {
                // Draw number
                sf::Text text;
                text.setFont(font);
                text.setCharacterSize(Config::TILE_SIZE - 8);
                text.setString(std::to_string(tile.neighborMines));
                text.setFillColor(getNumberColor(tile.neighborMines));
                
                sf::FloatRect bounds = text.getLocalBounds();
                text.setOrigin(bounds.width / 2, bounds.height / 2 + 4);
                text.setPosition(px + Config::TILE_SIZE / 2, py + Config::TILE_SIZE / 2);
                window.draw(text);
            }
        } else {
            // Hidden tile with 3D effect
            rect.setFillColor(sf::Color(192, 192, 192));
            window.draw(rect);
            
            // Highlight
            sf::Vertex highlight[] = {
                sf::Vertex(sf::Vector2f(px, py + Config::TILE_SIZE - 1), sf::Color::White),
                sf::Vertex(sf::Vector2f(px, py), sf::Color::White),
                sf::Vertex(sf::Vector2f(px + Config::TILE_SIZE - 1, py), sf::Color::White)
            };
            window.draw(highlight, 3, sf::LineStrip);
            
            // Shadow
            sf::Vertex shadow[] = {
                sf::Vertex(sf::Vector2f(px + Config::TILE_SIZE - 1, py + 1), sf::Color(128, 128, 128)),
                sf::Vertex(sf::Vector2f(px + Config::TILE_SIZE - 1, py + Config::TILE_SIZE - 1), sf::Color(128, 128, 128)),
                sf::Vertex(sf::Vector2f(px + 1, py + Config::TILE_SIZE - 1), sf::Color(128, 128, 128))
            };
            window.draw(shadow, 3, sf::LineStrip);
            
            if (tile.isFlagged()) {
                // Draw flag
                sf::Text flag;
                flag.setFont(font);
                flag.setCharacterSize(Config::TILE_SIZE - 12);
                flag.setString("F");
                flag.setFillColor(sf::Color::Red);
                flag.setStyle(sf::Text::Bold);
                
                sf::FloatRect bounds = flag.getLocalBounds();
                flag.setOrigin(bounds.width / 2, bounds.height / 2 + 4);
                flag.setPosition(px + Config::TILE_SIZE / 2, py + Config::TILE_SIZE / 2);
                window.draw(flag);
            }
        }
    }
    
    sf::Color getNumberColor(int num) {
        switch (num) {
            case 1: return sf::Color(0, 0, 255);       // Blue
            case 2: return sf::Color(0, 128, 0);       // Green
            case 3: return sf::Color(255, 0, 0);       // Red
            case 4: return sf::Color(0, 0, 128);       // Dark Blue
            case 5: return sf::Color(128, 0, 0);       // Dark Red
            case 6: return sf::Color(0, 128, 128);     // Cyan
            case 7: return sf::Color(0, 0, 0);         // Black
            case 8: return sf::Color(128, 128, 128);   // Gray
            default: return sf::Color::Black;
        }
    }
    
    Config::Difficulty difficulty;
    Board board;
    sf::RenderWindow window;
    sf::Font font;
    int gameTime;
    bool timerRunning;
    std::chrono::steady_clock::time_point startTime;
};

// ============================================
// Main Entry Point
// ============================================
int main() {
    Game game(Config::MEDIUM);
    game.run();
    return 0;
}

