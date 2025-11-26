"""
Ryan Greene Portfolio - Housing Price Estimator API
Flask REST API for ML-powered housing price predictions

This API provides housing price estimates based on property features
using a K-Nearest Neighbors regression model with ZIP code filtering.
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
    pd = None
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
# Data and Model Loading
# ============================================

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'knn_model.pkl')
DATA_PATH = os.path.join(os.path.dirname(__file__), 'housing_data.csv')

model = None
housing_df = None

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

def load_housing_data():
    """Load the housing dataset for ZIP code filtering."""
    global housing_df
    
    if not ML_AVAILABLE or pd is None:
        print("Pandas not available. ZIP filtering disabled.")
        return None
    
    if os.path.exists(DATA_PATH):
        try:
            housing_df = pd.read_csv(DATA_PATH)
            print(f"Housing data loaded: {len(housing_df)} records")
            return housing_df
        except Exception as e:
            print(f"Error loading housing data: {e}")
            return None
    else:
        print(f"Housing data not found at {DATA_PATH}. Using fallback estimation.")
        return None

# Try to load model and data on startup
load_model()
load_housing_data()

# ============================================
# Property Type Constants
# ============================================

# Valid single-family home property types (lowercase for comparison)
SINGLE_FAMILY_TYPES = [
    'single family',
    'single-family',
    'singlefamily',
    'house',
    'sfh',
    'single family home',
    'single-family home',
    'detached',
    'single family residential',
    'residential'
]

# ============================================
# ZIP Code Based Estimation
# ============================================

def filter_single_family(df):
    """
    Filter DataFrame to include only single-family homes.
    
    Args:
        df: pandas DataFrame with property_type column
    
    Returns:
        Filtered DataFrame with only single-family homes
    """
    if 'property_type' not in df.columns:
        # If no property_type column, return as-is
        return df
    
    # Clean and normalize property type
    df = df.copy()
    df['property_type_clean'] = df['property_type'].astype(str).str.lower().str.strip()
    
    # Filter to single-family homes only
    filtered = df[df['property_type_clean'].isin(SINGLE_FAMILY_TYPES)]
    
    return filtered


def estimate_by_zip(zip_code, sqft, beds, baths, age):
    """
    Estimate home price using ZIP code filtered data.
    Only uses single-family homes (excludes condos, apartments, townhomes, etc.)
    
    Args:
        zip_code: ZIP code to filter by
        sqft: Square footage of the property
        beds: Number of bedrooms
        baths: Number of bathrooms
        age: Age of the home in years
    
    Returns:
        tuple: (estimate, method, error_message)
    """
    global housing_df
    
    if housing_df is None or not ML_AVAILABLE:
        return None, None, "no_data"
    
    try:
        # Step 1: Filter by ZIP code
        zip_filtered_df = housing_df[housing_df['zip_code'] == zip_code].copy()
        
        # Check if any homes exist for this ZIP
        if zip_filtered_df.empty:
            return None, None, "no_homes_in_zip"
        
        # Step 2: Filter to single-family homes only
        filtered_df = filter_single_family(zip_filtered_df)
        
        # Check if any single-family homes exist for this ZIP
        if filtered_df.empty:
            return None, None, "no_single_family_in_zip"
        
        # Step 3: Sort by price (optional, for consistency)
        if 'price' in filtered_df.columns:
            filtered_df = filtered_df.sort_values('price', ascending=True)
        
        # Step 4: Calculate price per sqft for filtered single-family homes
        if 'price' in filtered_df.columns and 'sqft' in filtered_df.columns:
            filtered_df['price_per_sqft'] = filtered_df['price'] / filtered_df['sqft']
            
            # Get average price per sqft for this ZIP (single-family only)
            avg_price_per_sqft = filtered_df['price_per_sqft'].mean()
            
            # Base estimate from price per sqft
            estimate = avg_price_per_sqft * sqft
            
            # Adjust for bedrooms (compare to ZIP average)
            if 'beds' in filtered_df.columns:
                avg_beds = filtered_df['beds'].mean()
                bed_diff = beds - avg_beds
                estimate += bed_diff * 15000  # $15k per bedroom difference
            
            # Adjust for bathrooms (compare to ZIP average)
            if 'baths' in filtered_df.columns:
                avg_baths = filtered_df['baths'].mean()
                bath_diff = baths - avg_baths
                estimate += bath_diff * 10000  # $10k per bathroom difference
            
            # Adjust for age (compare to ZIP average)
            if 'age' in filtered_df.columns:
                avg_age = filtered_df['age'].mean()
                age_diff = age - avg_age
                # Newer homes are worth more (-0.5% per year difference)
                age_adjustment = 1 - (age_diff * 0.005)
                age_adjustment = max(0.7, min(1.3, age_adjustment))  # Cap adjustment
                estimate *= age_adjustment
            
            # Ensure reasonable bounds based on single-family homes in ZIP
            min_price = filtered_df['price'].min() * 0.5
            max_price = filtered_df['price'].max() * 1.5
            estimate = max(min_price, min(max_price, estimate))
            
            return round(estimate, 2), 'zip_filtered_sfh', None
        else:
            return None, None, "missing_columns"
            
    except Exception as e:
        print(f"ZIP estimation error: {e}")
        return None, None, "estimation_error"

# ============================================
# Fallback Estimation (when data not available)
# ============================================

def fallback_estimate(zip_code, sqft, beds, baths, age):
    """
    Generate a fallback estimate when housing data is not available.
    Uses ZIP code prefix to estimate regional pricing.
    
    Args:
        zip_code: ZIP code (used for regional adjustment)
        sqft: Square footage of the property
        beds: Number of bedrooms
        baths: Number of bathrooms
        age: Age of the home in years
    
    Returns:
        Estimated price (float)
    """
    # Regional price adjustment based on ZIP code first digit
    # This is a rough approximation of regional cost differences
    zip_prefix = int(str(zip_code)[0]) if zip_code else 5
    
    # Base price per sqft varies by region (rough national estimates)
    regional_multipliers = {
        0: 280,  # Northeast (MA, CT, etc.)
        1: 250,  # Northeast (NY, NJ, PA)
        2: 220,  # Mid-Atlantic (DC, VA, MD)
        3: 180,  # Southeast (FL, GA)
        4: 160,  # Midwest (OH, MI, IN)
        5: 170,  # South (TX, LA)
        6: 150,  # Central (KS, MO)
        7: 160,  # South Central (TX, OK)
        8: 200,  # Mountain (CO, AZ)
        9: 350,  # West Coast (CA, WA, OR)
    }
    
    base_price_per_sqft = regional_multipliers.get(zip_prefix, 200)
    
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
        'version': '1.1.0',
        'model_loaded': model is not None,
        'data_loaded': housing_df is not None,
        'data_records': len(housing_df) if housing_df is not None else 0,
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
        'data_status': 'loaded' if housing_df is not None else 'not available',
        'ml_libraries': 'available' if ML_AVAILABLE else 'not installed'
    })


@app.route('/predict', methods=['POST'])
def predict():
    """
    Main prediction endpoint with ZIP code filtering.
    
    Expects JSON body with:
        - zip (required): ZIP code for filtering
        - sqft (required): Square footage of the property
        - beds (required): Number of bedrooms
        - baths (required): Number of bathrooms
        - age (required): Age of the home in years
    
    Returns JSON with:
        - estimate: Predicted price
        - method: 'zip_filtered', 'model', or 'fallback'
        - input: Echo of input values
    """
    try:
        # Parse request data
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No data provided',
                'message': 'Please send JSON data with zip, sqft, beds, baths, and age fields'
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
            # ZIP code (optional but recommended)
            zip_code = None
            if 'zip' in data or 'zipcode' in data or 'zip_code' in data:
                zip_raw = data.get('zip') or data.get('zipcode') or data.get('zip_code')
                zip_code = int(str(zip_raw).strip()[:5])  # Take first 5 digits
            
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
        
        # Validate ZIP code if provided
        if zip_code is not None and (zip_code < 501 or zip_code > 99950):
            return jsonify({
                'error': 'Invalid ZIP code',
                'message': 'Please enter a valid 5-digit US ZIP code'
            }), 400
        
        # Try ZIP-filtered estimation first
        estimate = None
        method = None
        
        if zip_code is not None and housing_df is not None:
            estimate, method, error = estimate_by_zip(zip_code, sqft, beds, baths, age)
            
            if error == "no_homes_in_zip":
                return jsonify({
                    'error': 'No homes found for this ZIP code',
                    'message': f'No housing data available for ZIP code {zip_code}. Try a nearby ZIP code.',
                    'zip_code': zip_code
                }), 400
            
            if error == "no_single_family_in_zip":
                return jsonify({
                    'error': 'No single-family home data found for this ZIP',
                    'message': f'No single-family homes found in ZIP code {zip_code}. Only condos/apartments may be available in this area.',
                    'zip_code': zip_code
                }), 400
        
        # Fall back to model prediction if ZIP estimation failed
        if estimate is None and model is not None:
            try:
                features = np.array([[sqft, beds, baths, age]])
                prediction = model.predict(features)[0]
                estimate = round(float(prediction), 2)
                method = 'model'
            except Exception as e:
                print(f"Model prediction error: {e}")
                estimate = None
        
        # Final fallback to formula-based estimation
        if estimate is None:
            estimate = fallback_estimate(zip_code, sqft, beds, baths, age)
            method = 'fallback'
        
        # Return prediction result
        return jsonify({
            'estimate': estimate,
            'method': method,
            'input': {
                'zip_code': zip_code,
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
