"""
Ryan Greene Portfolio - Housing Price Estimator API
Flask REST API for ML-powered housing price predictions

This API provides housing price estimates based on property features
using a K-Nearest Neighbors regression model.
"""

import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np

# Try to import ML libraries
try:
    import joblib
    import pandas as pd
    from sklearn.neighbors import KNeighborsRegressor
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    print("Warning: ML libraries not available. Using fallback estimation.")

# ============================================
# Flask App Configuration
# ============================================

app = Flask(__name__)

# Enable CORS for all routes (allows frontend to call API)
CORS(app, resources={
    r"/*": {
        "origins": [
            "http://localhost:*",
            "http://127.0.0.1:*",
            "https://ryangreenedev.com",
            "https://*.github.io",
            "https://*.pages.dev"
        ],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# ============================================
# Model Loading
# ============================================

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'knn_model.pkl')
model = None

def load_model():
    """Load the trained KNN model from disk."""
    global model
    
    if not ML_AVAILABLE:
        print("ML libraries not available. Using fallback.")
        return None
    
    if os.path.exists(MODEL_PATH):
        try:
            model = joblib.load(MODEL_PATH)
            print(f"Model loaded successfully from {MODEL_PATH}")
            return model
        except Exception as e:
            print(f"Error loading model: {e}")
            return None
    else:
        print(f"Model file not found at {MODEL_PATH}. Using fallback estimation.")
        return None

# Try to load model on startup
load_model()

# ============================================
# Fallback Estimation (when model not available)
# ============================================

def fallback_estimate(sqft, beds, baths, age):
    """
    Generate a fallback estimate when the ML model is not available.
    Uses a simple formula based on typical housing market factors.
    
    Args:
        sqft: Square footage of the property
        beds: Number of bedrooms
        baths: Number of bathrooms
        age: Age of the home in years
    
    Returns:
        Estimated price (float)
    """
    # Base price per square foot (national average approximation)
    base_price_per_sqft = 200
    
    # Calculate base estimate
    estimate = sqft * base_price_per_sqft
    
    # Bedroom adjustment (+$12,000 per bedroom after 2)
    if beds > 2:
        estimate += (beds - 2) * 12000
    elif beds < 2:
        estimate -= (2 - beds) * 10000
    
    # Bathroom adjustment (+$8,000 per bathroom after 1.5)
    if baths > 1.5:
        estimate += (baths - 1.5) * 8000
    elif baths < 1.5:
        estimate -= (1.5 - baths) * 6000
    
    # Age depreciation (-0.4% per year, max 25%)
    age_factor = max(1 - (age * 0.004), 0.75)
    estimate *= age_factor
    
    # Ensure minimum reasonable value
    estimate = max(estimate, 50000)
    
    return round(estimate, 2)

# ============================================
# API Routes
# ============================================

@app.route('/', methods=['GET'])
def index():
    """
    Health check endpoint.
    Returns API status and availability information.
    """
    return jsonify({
        'status': 'API running',
        'version': '1.0.0',
        'model_loaded': model is not None,
        'ml_available': ML_AVAILABLE,
        'endpoints': {
            'GET /': 'Health check (this endpoint)',
            'POST /predict': 'Get housing price prediction',
            'GET /health': 'Detailed health check'
        }
    })


@app.route('/health', methods=['GET'])
def health():
    """
    Detailed health check endpoint.
    Useful for monitoring and deployment verification.
    """
    return jsonify({
        'status': 'healthy',
        'model_status': 'loaded' if model else 'using fallback',
        'ml_libraries': 'available' if ML_AVAILABLE else 'not installed'
    })


@app.route('/predict', methods=['POST'])
def predict():
    """
    Main prediction endpoint.
    
    Expects JSON body with:
        - sqft (required): Square footage of the property
        - beds (required): Number of bedrooms
        - baths (required): Number of bathrooms
        - age (required): Age of the home in years
    
    Returns JSON with:
        - estimate: Predicted price
        - confidence: Model confidence (if available)
        - method: 'model' or 'fallback'
    """
    try:
        # Parse request data
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No data provided',
                'message': 'Please send JSON data with sqft, beds, baths, and age fields'
            }), 400
        
        # Extract and validate required fields
        required_fields = ['sqft', 'beds', 'baths', 'age']
        missing_fields = [f for f in required_fields if f not in data]
        
        if missing_fields:
            return jsonify({
                'error': 'Missing required fields',
                'missing': missing_fields,
                'message': f'Please provide: {", ".join(missing_fields)}'
            }), 400
        
        # Parse and validate numeric values
        try:
            sqft = float(data['sqft'])
            beds = int(data['beds'])
            baths = float(data['baths'])
            age = int(data['age'])
        except (ValueError, TypeError) as e:
            return jsonify({
                'error': 'Invalid data types',
                'message': 'All fields must be numeric values'
            }), 400
        
        # Validate ranges
        if sqft < 100 or sqft > 100000:
            return jsonify({
                'error': 'Invalid sqft value',
                'message': 'Square footage must be between 100 and 100,000'
            }), 400
        
        if beds < 0 or beds > 20:
            return jsonify({
                'error': 'Invalid beds value',
                'message': 'Bedrooms must be between 0 and 20'
            }), 400
        
        if baths < 0 or baths > 20:
            return jsonify({
                'error': 'Invalid baths value',
                'message': 'Bathrooms must be between 0 and 20'
            }), 400
        
        if age < 0 or age > 500:
            return jsonify({
                'error': 'Invalid age value',
                'message': 'Age must be between 0 and 500 years'
            }), 400
        
        # Generate prediction
        if model is not None:
            # Use ML model
            try:
                features = np.array([[sqft, beds, baths, age]])
                prediction = model.predict(features)[0]
                estimate = round(float(prediction), 2)
                method = 'model'
            except Exception as e:
                print(f"Model prediction error: {e}")
                estimate = fallback_estimate(sqft, beds, baths, age)
                method = 'fallback'
        else:
            # Use fallback estimation
            estimate = fallback_estimate(sqft, beds, baths, age)
            method = 'fallback'
        
        # Return prediction result
        return jsonify({
            'estimate': estimate,
            'method': method,
            'input': {
                'sqft': sqft,
                'beds': beds,
                'baths': baths,
                'age': age
            }
        })
    
    except Exception as e:
        print(f"Prediction error: {e}")
        return jsonify({
            'error': 'Prediction failed',
            'message': 'An unexpected error occurred. Please try again.'
        }), 500


@app.route('/predict', methods=['OPTIONS'])
def predict_options():
    """Handle CORS preflight requests."""
    return '', 204


# ============================================
# Error Handlers
# ============================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Not found',
        'message': 'The requested endpoint does not exist'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500


# ============================================
# Main Entry Point
# ============================================

if __name__ == '__main__':
    # Get port from environment variable (for deployment)
    port = int(os.environ.get('PORT', 5000))
    
    # Run the Flask app
    app.run(
        host='0.0.0.0',
        port=port,
        debug=os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    )

