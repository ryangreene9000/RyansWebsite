# Minesweeper — JavaScript Canvas Game

A complete Minesweeper game built in JavaScript using HTML5 Canvas, playable directly in the browser.

## 🎮 Play Now

Visit `/games/minesweeper/` on the website to play!

## Features

- 💣 Classic Minesweeper gameplay
- 🎲 Randomized board and mine generation
- 🔢 Neighbor mine-count algorithm
- 🌊 Recursive flood-fill reveal
- 🚩 Flagging system
- ✅ Win/Loss detection
- ⏱️ Built-in timer
- 📊 Three difficulty levels (Easy, Medium, Hard)
- 📱 Mobile-friendly (touch support)

## Game Controls

### Desktop
| Action | Control |
|--------|---------|
| Reveal tile | Left Click |
| Flag/unflag tile | Right Click |
| Chord (reveal neighbors) | Middle Click |
| Restart game | Press R |
| Easy difficulty | Press 1 |
| Medium difficulty | Press 2 |
| Hard difficulty | Press 3 |

### Mobile
| Action | Control |
|--------|---------|
| Reveal tile | Tap |
| Flag tile | Long press (hold > 0.5s) |

## Difficulty Levels

| Level | Board Size | Mines |
|-------|------------|-------|
| Easy | 9 × 9 | 10 |
| Medium | 16 × 16 | 40 |
| Hard | 24 × 16 | 70 |

## How to Play

1. **Goal**: Reveal all tiles that don't contain mines
2. **Numbers**: Each number shows how many mines are in the 8 adjacent tiles
3. **Flagging**: Right-click to mark suspected mines with flags
4. **Chording**: Middle-click on a number to reveal all unflagged neighbors (if correct number of flags are placed)
5. **First click**: The first click is always safe (no mine will be there)

## Technical Details

### Files
```
games/minesweeper/
├── index.html        # Game page with UI
├── minesweeper.js    # Complete game logic
├── README.md         # This file
└── src/
    └── main.cpp      # C++ reference implementation (SFML)
```

### Architecture

The game is built with three main classes:

1. **Tile**: Represents a single cell
   - States: hidden, revealed, flagged
   - Properties: hasMine, neighborMines

2. **Board**: Manages the game state
   - Mine generation with safe zone
   - Neighbor counting algorithm
   - Flood-fill reveal logic
   - Win/loss detection

3. **Game**: Handles rendering and input
   - Canvas drawing
   - Mouse/touch events
   - Timer management
   - Difficulty switching

### Algorithms

**Mine Generation**
- Uses Fisher-Yates shuffle for random placement
- Excludes a 3×3 safe zone around the first click
- Ensures the first click never hits a mine

**Flood Fill**
- When revealing a tile with 0 neighbors, recursively reveals all adjacent tiles
- Stops at numbered tiles (tiles adjacent to mines)

**Chording**
- Counts flags around a revealed number tile
- If flag count matches the number, reveals all unflagged neighbors
- Can trigger a loss if flags are incorrectly placed

## C++ Reference Implementation

The `/src/main.cpp` file contains a C++ implementation using SFML for desktop builds. To build:

```bash
# Install SFML
brew install sfml  # macOS
sudo apt install libsfml-dev  # Ubuntu

# Build
mkdir build && cd build
cmake ..
make

# Run
./minesweeper
```

## License

MIT License - Part of Ryan Greene's Portfolio

## Author

**Ryan Greene**
- GitHub: [github.com/ryangreene9000](https://github.com/ryangreene9000)
- LinkedIn: [linkedin.com/in/ryancgreene1](https://linkedin.com/in/ryancgreene1)
- Website: [ryangreenedev.com](https://ryangreenedev.com)
