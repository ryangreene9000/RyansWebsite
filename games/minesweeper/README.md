# Minesweeper — C++ / SFML / WebAssembly

A complete Minesweeper game built from scratch in modern C++ using SFML, with WebAssembly support for browser play.

## Features

- 🎮 Classic Minesweeper gameplay
- 💣 Randomized board and mine generation
- 🔢 Neighbor mine-count algorithm
- 🌊 Recursive flood-fill reveal
- 🚩 Flagging system
- ✅ Win/Loss detection
- ⏱️ Built-in timer
- 📊 Multiple difficulty levels (Easy, Medium, Hard)
- 🌐 WebAssembly build for browser play

## Game Controls

| Action | Control |
|--------|---------|
| Reveal tile | Left Click |
| Flag/unflag tile | Right Click |
| Chord (reveal neighbors) | Middle Click |
| Restart game | Press R |
| Quit | Press Escape |

## Building the Game

### Prerequisites

#### For Native Build:
- CMake 3.15+
- C++17 compatible compiler (GCC 7+, Clang 5+, MSVC 2017+)
- SFML 2.5+ development libraries

#### For WebAssembly Build:
- Emscripten SDK
- CMake 3.15+

### Native Build (SFML)

```bash
# Install SFML (Ubuntu/Debian)
sudo apt install libsfml-dev

# Install SFML (macOS)
brew install sfml

# Build
cd games/minesweeper
mkdir build && cd build
cmake ..
make

# Run
./minesweeper
```

### WebAssembly Build (Emscripten)

```bash
# Install Emscripten (if not installed)
git clone https://github.com/emscripten-core/emsdk.git
cd emsdk
./emsdk install latest
./emsdk activate latest
source ./emsdk_env.sh

# Build
cd games/minesweeper
mkdir build-wasm && cd build-wasm
emcmake cmake ..
emmake make

# The output files will be:
# - minesweeper.js
# - minesweeper.wasm
# - minesweeper.data (assets)
```

### Deploying the WebAssembly Build

After building, copy the generated files to the game directory:

```bash
cp minesweeper.js minesweeper.wasm minesweeper.data ../
```

The game will automatically load when you visit `/games/minesweeper/` on the website.

## Project Structure

```
games/minesweeper/
├── src/
│   └── main.cpp          # Main game source code
├── assets/
│   └── font.ttf          # Game font (add your own)
├── CMakeLists.txt        # CMake build configuration
├── index.html            # WebAssembly loader page
├── minesweeper.js        # Generated WASM glue code (after build)
├── minesweeper.wasm      # Generated WebAssembly binary (after build)
└── README.md             # This file
```

## Game Architecture

### Classes

- **`Tile`**: Represents a single tile on the board
  - States: Hidden, Revealed, Flagged
  - Properties: hasMine, neighborMines

- **`Board`**: Manages the game board
  - Mine generation with safe zone around first click
  - Neighbor counting algorithm
  - Recursive flood-fill reveal
  - Win/loss detection

- **`Game`**: Main game loop and rendering
  - SFML window management
  - Input handling
  - Timer system
  - Rendering tiles, header, and numbers

### Algorithms

1. **Mine Generation**: Uses Fisher-Yates shuffle to randomly place mines, excluding a 3x3 safe zone around the first click.

2. **Neighbor Counting**: For each non-mine tile, counts adjacent mines in all 8 directions.

3. **Flood-Fill Reveal**: When revealing a tile with 0 neighbors, recursively reveals all adjacent tiles until reaching numbered tiles.

4. **Chording**: When clicking a revealed number tile with the correct number of adjacent flags, reveals all unflagged neighbors.

## Customization

### Changing Difficulty

Edit the difficulty settings in `src/main.cpp`:

```cpp
const Difficulty EASY = {9, 9, 10, "Easy"};      // 9x9, 10 mines
const Difficulty MEDIUM = {16, 16, 40, "Medium"};  // 16x16, 40 mines
const Difficulty HARD = {30, 16, 99, "Hard"};    // 30x16, 99 mines
```

### Adding Custom Assets

1. Place a TrueType font file at `assets/font.ttf`
2. The game will automatically use it for rendering numbers and text

## License

MIT License - Part of Ryan Greene's Portfolio

## Author

**Ryan Greene**
- GitHub: [github.com/ryangreene9000](https://github.com/ryangreene9000)
- LinkedIn: [linkedin.com/in/ryancgreene1](https://linkedin.com/in/ryancgreene1)
- Website: [ryangreenedev.com](https://ryangreenedev.com)

