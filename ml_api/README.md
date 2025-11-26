# Housing Price Estimator API

A Flask REST API that provides ML-powered housing price predictions using a K-Nearest Neighbors regression model.

## Overview

This API is part of Ryan Greene's portfolio website. It receives property features (square footage, bedrooms, bathrooms, and age) and returns a predicted housing price.

## Features

- 🏠 Housing price predictions based on property features
- 🤖 K-Nearest Neighbors regression model
- 🔄 Automatic fallback estimation when model is unavailable
- 🌐 CORS-enabled for frontend integration
- 📊 Input validation and error handling

## API Endpoints

### `GET /`
Health check endpoint. Returns API status.

**Response:**
```json
{
  "status": "API running",
  "version": "1.0.0",
  "model_loaded": true,
  "ml_available": true,
  "endpoints": {
    "GET /": "Health check",
    "POST /predict": "Get housing price prediction",
    "GET /health": "Detailed health check"
  }
}
```

### `GET /health`
Detailed health check for monitoring.

**Response:**
```json
{
  "status": "healthy",
  "model_status": "loaded",
  "ml_libraries": "available"
}
```

### `POST /predict`
Main prediction endpoint.

**Request Body:**
```json
{
  "sqft": 1800,
  "beds": 3,
  "baths": 2,
  "age": 15
}
```

**Response:**
```json
{
  "estimate": 425000.00,
  "method": "model",
  "input": {
    "sqft": 1800,
    "beds": 3,
    "baths": 2,
    "age": 15
  }
}
```

**Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| sqft | float | Yes | Square footage (100-100,000) |
| beds | int | Yes | Number of bedrooms (0-20) |
| baths | float | Yes | Number of bathrooms (0-20) |
| age | int | Yes | Age of home in years (0-500) |

## Local Development

### Prerequisites
- Python 3.10+
- pip

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/ryangreene9000/RyansWebsite.git
cd RyansWebsite/ml_api
```

2. **Create a virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Run the development server:**
```bash
python app.py
```

The API will be available at `http://localhost:5000`.

### Testing the API

Using curl:
```bash
# Health check
curl http://localhost:5000/

# Get prediction
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"sqft": 1800, "beds": 3, "baths": 2, "age": 15}'
```

Using Python:
```python
import requests

response = requests.post(
    'http://localhost:5000/predict',
    json={'sqft': 1800, 'beds': 3, 'baths': 2, 'age': 15}
)
print(response.json())
```

## Deployment to Render

### Step 1: Create a New Web Service

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure the service:
   - **Name:** `housing-estimator-api` (or your preferred name)
   - **Root Directory:** `ml_api`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`

### Step 2: Environment Variables (Optional)

| Variable | Description |
|----------|-------------|
| `PORT` | Port to run on (Render sets this automatically) |
| `FLASK_DEBUG` | Set to `false` for production |

### Step 3: Deploy

Click "Create Web Service" and wait for deployment to complete.

Your API will be available at:
```
https://your-service-name.onrender.com
```

### Step 4: Update Frontend

Update the `API_URL` constant in `/scripts/estimator.js`:
```javascript
const API_URL = 'https://your-service-name.onrender.com';
const DEMO_MODE = false;
```

## Adding Your Trained Model

To use a trained model instead of the fallback estimation:

1. **Train your KNN model:**
```python
from sklearn.neighbors import KNeighborsRegressor
import joblib
import pandas as pd

# Load and prepare your training data
# X should have columns: sqft, beds, baths, age
# y should be the prices

model = KNeighborsRegressor(n_neighbors=5)
model.fit(X, y)

# Save the model
joblib.dump(model, 'knn_model.pkl')
```

2. **Add the model file:**
   - Place `knn_model.pkl` in the `ml_api` directory
   - Commit and push to GitHub
   - Render will automatically redeploy

## Project Structure

```
ml_api/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── runtime.txt         # Python version for Render
├── README.md           # This file
└── knn_model.pkl       # Trained model (add this later)
```

## Error Handling

The API returns appropriate HTTP status codes and error messages:

| Status | Description |
|--------|-------------|
| 200 | Success |
| 400 | Bad request (invalid input) |
| 404 | Endpoint not found |
| 500 | Server error |

## License

MIT License - Part of Ryan Greene's Portfolio

## Contact

- **Email:** Ryangreene2091@gmail.com
- **LinkedIn:** [linkedin.com/in/ryancgreene1](https://linkedin.com/in/ryancgreene1)
- **GitHub:** [github.com/ryangreene9000](https://github.com/ryangreene9000)

