# Ryan Greene - Developer Portfolio

A modern, recruiter-ready developer portfolio website with a Flask ML API backend.

🌐 **Live Site:** [ryangreenedev.com](https://ryangreenedev.com)

## Overview

This repository contains:
- **Static Frontend** - Modern portfolio website (HTML/CSS/JS) for GitHub Pages
- **Flask ML API** - Housing price estimator backend for Render deployment
- **Browser Games** - Minesweeper and Tetris playable in the browser

## Quick Start

### Frontend (GitHub Pages)

The frontend is a static website ready for GitHub Pages deployment. Simply push to the `main` branch and enable GitHub Pages in your repository settings.

### ML API Backend (Render)

```bash
cd ml_api
pip install -r requirements.txt
python app.py
```

See [ml_api/README.md](ml_api/README.md) for deployment instructions.

## Project Structure

```
RyansWebsite/
├── index.html              # Home page
├── about.html              # About page
├── projects.html           # Projects showcase
├── games.html              # Games gallery
├── realestate.html         # ML Housing Estimator
├── contact.html            # Contact page
│
├── styles/
│   ├── global.css          # Global styles
│   └── home.css            # Home page styles
│
├── scripts/
│   ├── main.js             # Main JavaScript
│   └── estimator.js        # ML Estimator logic
│
├── assets/
│   ├── favicon.svg         # Site favicon
│   ├── tetris.svg          # Tetris thumbnail
│   └── placeholder.svg     # Placeholder image
│
├── games/
│   ├── minesweeper/        # Minesweeper game
│   │   ├── index.html      # Game page
│   │   └── minesweeper.js  # Game logic
│   │
│   └── tetris/             # Tetris game
│       ├── index.html      # Game page
│       ├── style.css       # Game styles
│       └── tetris.js       # Game logic
│
├── data/
│   ├── redfin_raw/              # Raw Redfin CSV exports
│   ├── redfin_clean/            # Cleaned per-ZIP CSVs
│   └── supported_zipcodes.json  # List of supported Bay Area ZIPs
│
└── ml_api/
    ├── app.py              # Flask API
    ├── redfin_import.py    # Redfin CSV import script
    ├── requirements.txt    # Dependencies
    ├── runtime.txt         # Python version
    └── README.md           # API documentation
```

## Pages

| Page | Description |
|------|-------------|
| **Home** | Hero section, featured projects, skills preview |
| **About** | Full bio, skills, education, experience, interests |
| **Projects** | Filterable project grid with detailed cards |
| **Games** | Playable games including Minesweeper and Tetris |
| **Estimator** | ML-powered housing price estimator |
| **Contact** | Contact info and message form |

## Projects

### AI-Powered Contract Change Detection Pipeline
🏆 **1st Place — FINRA 2025 Creatathon**

A serverless NLP pipeline that analyzes regulatory contracts, detects semantic changes, and automates compliance workflows. Uses AWS Lambda, Step Functions, DynamoDB, and OpenAI embeddings for semantic diffing. Reduced manual review time by 80%.

**Tech:** AWS Lambda, Step Functions, DynamoDB, S3, Python, OpenAI Embeddings

---

### AWS Serverless Valve Automation System
*Capstone Project*

A distributed AWS-based automation system for monitoring and validating utility valve states in real time. Designed for WSSC Water with workflow automation, email notifications, and audit logging.

**Tech:** Java, AWS Lambda, EC2, S3, DynamoDB, Step Functions

---

### Pipelined 32-bit CPU in Verilog

A fully synthesizable 5-stage pipelined CPU implementing a subset of MIPS with hazard detection, forwarding, and branch handling. Designed IF/ID/EX/MEM/WB pipeline stages, ALU, register file, and control unit.

**Tech:** Verilog, Vivado, FPGA, Digital Logic

---

### Real-Time Embedded Systems on HCS12

A collection of embedded programs for the HCS12 microcontroller including real-time 8kHz audio sampling, waveform synthesis, 7-segment display drivers, and UART command interfaces. Achieved deterministic timing with optimized ISR latencies.

**Tech:** HCS12 Assembly, Timers, RTI Interrupts, ADC, UART

---

### Raspberry Pi Networked Sensor Dashboard

A Python-based sensor visualization system on Raspberry Pi with real-time dashboard, joystick control, LED matrix output, and TCP/IP communication. Visualizes accelerometer, temperature, and humidity data.

**Tech:** Python, Tkinter, Raspberry Pi, SenseHAT, TCP Sockets

---

### CPU Microarchitecture Design-Space Exploration

A parametric performance study exploring 18 CPU tuning knobs including fetch width, ALU count, cache parameters, and branch predictors. Automated simulation experiments in SimpleScalar across hundreds of configurations.

**Tech:** C++, SimpleScalar, Shell Scripting, Performance Analysis

---

### Custom Memory Management System

A full custom allocator implementing malloc, calloc, free, and realloc using a simulated heap with 16-byte alignment. Features free-list management, block splitting, coalescing, and error handling.

**Tech:** C, Memory Management, Bitwise Operations

---

### Threaded Channel Synchronization System

A concurrency messaging system with blocking/non-blocking reads/writes using condition variables and mutex-protected queues. Inspired by Go's CSP model with FIFO ordering and deadlock prevention.

**Tech:** C, pthreads, Mutexes, Condition Variables

---

## Games

### Minesweeper

Classic mine-clearing puzzle game built with JavaScript and HTML5 Canvas.

**How to Play:**
- **Left Click** — Reveal a tile
- **Right Click** — Flag/unflag a suspected mine (long-press on mobile)
- **Numbers** — Show how many mines touch that tile
- **Goal** — Clear all safe tiles without hitting a mine

**Features:**
- Multiple difficulty levels (Easy, Medium, Hard)
- Recursive flood-fill reveal
- Timer and mine counter
- Win/loss detection

**Location:** `/games/minesweeper/`

---

### Tetris

Classic block-stacking puzzle game built with vanilla JavaScript and HTML5 Canvas.

**How to Play:**
- **← →** — Move piece left/right
- **↑** or **W** — Rotate piece
- **↓** — Soft drop (faster fall)
- **Space** — Hard drop (instant drop)
- **P** — Pause game

**Features:**
- All 7 tetromino shapes
- Ghost piece preview
- Next piece display
- Score, level, and line tracking
- Increasing speed with levels
- Mobile touch controls

**Location:** `/games/tetris/`

---

## Housing Price Estimator

### Supported ZIP Codes

This model is trained exclusively on **Bay Area (California)** housing data using CSV exports from Redfin. The estimator only supports ZIP codes present in the Bay Area, including but not limited to:

| Region | ZIP Code Range |
|--------|----------------|
| **San Francisco** | 94102–94134 |
| **San Mateo County** | 94002–94080 |
| **Santa Clara County** | 94022–95126 |
| **Alameda & Contra Costa** | 94501–94808 |

At runtime, the app automatically rejects unsupported ZIP codes and displays a friendly error message.

This ensures the model remains accurate because it is trained on **real sold-home data** from the region.

### Importing Redfin Data

To update the model with new Redfin data:

1. **Download a Redfin CSV:**
   - Go to [Redfin.com](https://www.redfin.com)
   - Search for homes in a Bay Area city
   - Filter to "Sold" homes
   - Click "Download All" to export CSV

2. **Place the CSV in the data folder:**
   ```bash
   cp ~/Downloads/redfin_*.csv data/redfin_raw/
   ```

3. **Run the import script:**
   ```bash
   cd ml_api
   python redfin_import.py
   ```

4. **Retrain the model (if train_model.py exists):**
   ```bash
   python train_model.py
   ```

The import script will:
- Filter to single-family homes only
- Filter to SOLD homes only
- Clean and validate data
- Generate `data/supported_zipcodes.json`
- Update `ml_api/housing_data.csv`

---

## Customization Points

### 1. Update API URL
Edit `scripts/estimator.js` and update:
```javascript
const API_URL = 'https://your-api-name.onrender.com';
const DEMO_MODE = false;
```

### 2. Update Project Links
In `projects.html`, update the GitHub links to point to your actual repositories.

### 3. Resume
Resume is located at `assets/RyangreeneResumeCurrent.pdf`

### 4. Add Profile Photo
Replace the emoji placeholder in `about.html` with an actual photo.

### 5. Game List
Add new games in `games.html` following the existing card pattern.

### 6. Project List
Add new projects in `projects.html` using the project card template.

## Tech Stack

### Frontend
- Pure HTML5, CSS3, JavaScript (no frameworks)
- CSS Grid & Flexbox for layouts
- CSS Custom Properties for theming
- Intersection Observer for scroll animations
- Responsive design (mobile-first)

### Backend
- Python 3.10
- Flask 2.2.5
- scikit-learn (KNN model)
- gunicorn (production server)
- Flask-CORS

### Games
- JavaScript (ES6+)
- HTML5 Canvas API
- CSS3 animations
- Responsive touch controls

## Deployment

### Frontend → GitHub Pages
1. Push to `main` branch
2. Go to Settings → Pages
3. Select "Deploy from a branch" → `main` → `/ (root)`
4. Custom domain: `ryangreenedev.com`

### Backend → Render
1. Create new Web Service on Render
2. Connect GitHub repo
3. Set root directory: `ml_api`
4. Build: `pip install -r requirements.txt`
5. Start: `gunicorn app:app`

## Contact

- **Email:** Ryangreene2091@gmail.com
- **Phone:** 650-454-4727
- **LinkedIn:** [linkedin.com/in/ryancgreene1](https://linkedin.com/in/ryancgreene1)
- **GitHub:** [github.com/ryangreene9000](https://github.com/ryangreene9000)

## License

MIT License

---

Built by Ryan Greene
