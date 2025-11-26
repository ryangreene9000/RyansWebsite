# Ryan Greene - Developer Portfolio

A modern, recruiter-ready developer portfolio website with a Flask ML API backend.

🌐 **Live Site:** [ryangreenedev.com](https://ryangreenedev.com)

## Overview

This repository contains:
- **Static Frontend** - Modern portfolio website (HTML/CSS/JS) for GitHub Pages
- **Flask ML API** - Housing price estimator backend for Render deployment
- **Minesweeper Game** - C++ game with WebAssembly for browser play

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
│   └── placeholder.svg     # Placeholder image
│
├── games/
│   └── minesweeper/        # Minesweeper game
│       ├── src/main.cpp    # C++ source
│       ├── CMakeLists.txt  # Build config
│       ├── index.html      # Game loader
│       └── README.md       # Build instructions
│
└── ml_api/
    ├── app.py              # Flask API
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
| **Games** | Playable games including Minesweeper |
| **Estimator** | ML-powered housing price estimator |
| **Contact** | Contact info and message form |

## Customization Points

### 1. Update API URL
Edit `scripts/estimator.js` and update:
```javascript
const API_URL = 'https://your-api-name.onrender.com';
const DEMO_MODE = false;
```

### 2. Update Project Links
In `projects.html`, update the GitHub links to point to your actual repositories.

### 3. Add Resume PDF
Place your resume at `assets/Ryan_Greene_Resume.pdf`

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

### Game
- C++17
- SFML 2.5+
- WebAssembly (Emscripten)

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

Built with 💚 by Ryan Greene
