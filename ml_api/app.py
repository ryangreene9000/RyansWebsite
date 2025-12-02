"""
Ryan Greene Portfolio - Housing Price Estimator API
Flask REST API for ML-powered housing price predictions.

This API:
- Uses ONLY single-family residential (SFR) sold listings
- Filters strictly by ZIP code
- Requires minimum 50 comparable homes
- Trains/uses KNN model on ZIP-specific SFR data
"""

import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np

# Try to import ML libraries
try:
    import joblib
    import pandas as pd
    from sklearn.neighbors import KNeighborsRegressor
    from sklearn.preprocessing import StandardScaler
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    pd = None
    print("Warning: ML libraries not available. Using fallback estimation.")

# ============================================
# Flask App Configuration
# ============================================

app = Flask(__name__)

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
# Configuration Constants
# ============================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(SCRIPT_DIR, 'housing_data.csv')
MODEL_PATH = os.path.join(SCRIPT_DIR, 'knn_model.pkl')
SCALER_PATH = os.path.join(SCRIPT_DIR, 'scaler.pkl')
METADATA_PATH = os.path.join(SCRIPT_DIR, 'model_metadata.json')
SUPPORTED_ZIPS_PATH = os.path.join(os.path.dirname(SCRIPT_DIR), 'data', 'supported_zipcodes.json')

# Minimum comparable homes for reliable estimate
MIN_COMPARABLE_HOMES = 50

# Property type filters
INCLUDE_PROPERTY_TYPES = [
    "single family", "single family residence", "single family residential",
    "residential", "house", "sfr", "detached"
]

EXCLUDE_PROPERTY_TYPES = [
    "condo", "condominium", "townhome", "townhouse", "apartment", "apt",
    "multi", "multi-family", "multifamily", "duplex", "triplex", "fourplex",
    "quadplex", "mobile", "manufactured", "land", "lot", "commercial"
]

# Data quality bounds
MIN_PRICE = 150000
MAX_PRICE = 10000000
MIN_SQFT = 300
MAX_SQFT = 10000
MAX_BEDS = 8
MAX_BATHS = 8

# ============================================
# Data and Model Loading
# ============================================

housing_df = None
global_model = None
global_scaler = None
model_metadata = None
supported_zips = set()


def load_supported_zips():
    """Load supported ZIP codes from JSON file or extract from data."""
    global supported_zips
    
    # Try loading from JSON file
    if os.path.exists(SUPPORTED_ZIPS_PATH):
        try:
            with open(SUPPORTED_ZIPS_PATH, 'r') as f:
                data = json.load(f)
                supported_zips = set(data.get('zip_codes', []))
                print(f"✅ Loaded {len(supported_zips)} supported ZIP codes from JSON")
                return supported_zips
        except Exception as e:
            print(f"Error loading supported ZIPs: {e}")
    
    return supported_zips


def load_housing_data():
    """Load the cleaned housing dataset."""
    global housing_df, supported_zips
    
    if not ML_AVAILABLE or pd is None:
        print("Pandas not available.")
        return None
    
    if os.path.exists(DATA_PATH):
        try:
            housing_df = pd.read_csv(DATA_PATH)
            
            # Pre-process property type for filtering
            if 'property_type' in housing_df.columns:
                housing_df['property_type_clean'] = (
                    housing_df['property_type']
                    .astype(str).str.lower().str.strip()
                )
            
            # Extract supported ZIP codes from data
            if 'zip_code' in housing_df.columns:
                supported_zips = set(housing_df['zip_code'].dropna().unique().astype(int).tolist())
                print(f"✅ Found {len(supported_zips)} unique ZIP codes in dataset")
            
            print(f"✅ Loaded {len(housing_df)} SFR records from {DATA_PATH}")
            return housing_df
        except Exception as e:
            print(f"Error loading data: {e}")
            return None
    else:
        print(f"Data file not found: {DATA_PATH}")
        return None


def load_model():
    """Load the trained model and scaler."""
    global global_model, global_scaler, model_metadata
    
    if not ML_AVAILABLE:
        return None, None
    
    try:
        if os.path.exists(MODEL_PATH):
            global_model = joblib.load(MODEL_PATH)
            print(f"✅ Model loaded from {MODEL_PATH}")
        
        if os.path.exists(SCALER_PATH):
            global_scaler = joblib.load(SCALER_PATH)
            print(f"✅ Scaler loaded from {SCALER_PATH}")
        
        if os.path.exists(METADATA_PATH):
            with open(METADATA_PATH, 'r') as f:
                model_metadata = json.load(f)
            print(f"✅ Metadata loaded: {model_metadata.get('total_samples', 0)} samples")
        
        return global_model, global_scaler
    except Exception as e:
        print(f"Error loading model: {e}")
        return None, None


# Load on startup
load_supported_zips()
load_housing_data()
load_model()

# ============================================
# Data Filtering Functions
# ============================================

def is_single_family(property_type):
    """Check if property type is single-family residential."""
    if not property_type:
        return False
    
    prop_lower = str(property_type).lower().strip()
    
    # Exclude non-SFR types
    for exc in EXCLUDE_PROPERTY_TYPES:
        if exc in prop_lower:
            return False
    
    # Include only valid SFR types
    for inc in INCLUDE_PROPERTY_TYPES:
        if inc in prop_lower:
            return True
    
    return False


def filter_sfr_only(df):
    """Filter to single-family residential only."""
    if 'property_type_clean' not in df.columns and 'property_type' not in df.columns:
        return df
    
    df = df.copy()
    
    if 'property_type_clean' not in df.columns:
        df['property_type_clean'] = df['property_type'].astype(str).str.lower().str.strip()
    
    # Exclude non-SFR
    exclude_mask = df['property_type_clean'].apply(
        lambda x: any(exc in x for exc in EXCLUDE_PROPERTY_TYPES)
    )
    df = df[~exclude_mask]
    
    # Include only SFR
    include_mask = df['property_type_clean'].apply(
        lambda x: any(inc in x for inc in INCLUDE_PROPERTY_TYPES)
    )
    df = df[include_mask]
    
    return df


def get_zip_data(zip_code):
    """
    Get filtered SFR data for a specific ZIP code.
    Returns (dataframe, error_code).
    """
    global housing_df
    
    if housing_df is None:
        return None, "no_data"
    
    # STRICT ZIP code match
    zip_df = housing_df[housing_df['zip_code'] == zip_code].copy()
    
    if zip_df.empty:
        return None, "no_homes_in_zip"
    
    # Filter to SFR only
    sfr_df = filter_sfr_only(zip_df)
    
    if sfr_df.empty:
        return None, "no_sfr_in_zip"
    
    # Check minimum samples
    if len(sfr_df) < MIN_COMPARABLE_HOMES:
        return sfr_df, "not_enough_comparables"
    
    # Apply quality filters
    sfr_df = sfr_df[
        (sfr_df['price'] >= MIN_PRICE) & 
        (sfr_df['price'] <= MAX_PRICE) &
        (sfr_df['sqft'] >= MIN_SQFT) &
        (sfr_df['sqft'] <= MAX_SQFT) &
        (sfr_df['beds'] <= MAX_BEDS) &
        (sfr_df['baths'] <= MAX_BATHS)
    ]
    
    # Sort by price
    sfr_df = sfr_df.sort_values('price')
    
    # Debug output
    print(f"\nZIP {zip_code} SUMMARY:")
    print(sfr_df['price'].describe())
    if 'property_type' in sfr_df.columns:
        print(sfr_df['property_type'].value_counts())
    print(f"Total records used: {len(sfr_df)}")
    
    return sfr_df, None


# ============================================
# ML Prediction Functions
# ============================================

def train_zip_model(zip_df):
    """Train KNN model on ZIP-specific SFR data."""
    if not ML_AVAILABLE or len(zip_df) < MIN_COMPARABLE_HOMES:
        return None, None
    
    try:
        feature_cols = ['sqft', 'beds', 'baths', 'age']
        
        # Validate columns exist
        for col in feature_cols + ['price']:
            if col not in zip_df.columns:
                return None, None
        
        X = zip_df[feature_cols].values
        y = zip_df['price'].values
        
        # Remove NaN
        valid = ~(np.isnan(X).any(axis=1) | np.isnan(y))
        X, y = X[valid], y[valid]
        
        if len(X) < MIN_COMPARABLE_HOMES:
            return None, None
        
        # Scale and train
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        k = min(15, max(3, int(np.sqrt(len(X)))))
        model = KNeighborsRegressor(n_neighbors=k, weights='distance')
        model.fit(X_scaled, y)
        
        return model, scaler
    except Exception as e:
        print(f"Training error: {e}")
        return None, None


def predict_price(model, scaler, sqft, beds, baths, age):
    """Make price prediction using trained model."""
    if model is None or scaler is None:
        return None
    
    try:
        features = np.array([[sqft, beds, baths, age]])
        features_scaled = scaler.transform(features)
        return float(model.predict(features_scaled)[0])
    except Exception as e:
        print(f"Prediction error: {e}")
        return None


def estimate_by_zip(zip_code, sqft, beds, baths, age):
    """
    Main estimation function.
    Filters to ZIP-specific SFR data and trains model.
    """
    # Get filtered data
    zip_df, error = get_zip_data(zip_code)
    
    if error and error != "not_enough_comparables":
        return None, None, error, 0
    
    if zip_df is None or len(zip_df) == 0:
        return None, None, "no_data", 0
    
    comparables = len(zip_df)
    
    # Need minimum samples
    if comparables < MIN_COMPARABLE_HOMES:
        return None, None, "not_enough_comparables", comparables
    
    # Train model on this ZIP's SFR data
    model, scaler = train_zip_model(zip_df)
    
    if model is not None:
        estimate = predict_price(model, scaler, sqft, beds, baths, age)
        
        if estimate is not None:
            # Bound to reasonable range for this ZIP
            min_price = zip_df['price'].min() * 0.6
            max_price = zip_df['price'].max() * 1.4
            estimate = max(min_price, min(max_price, estimate))
            
            return round(estimate, 2), 'zip_ml_sfr', None, comparables
    
    # Fallback to price-per-sqft
    try:
        zip_df['ppsf'] = zip_df['price'] / zip_df['sqft']
        avg_ppsf = zip_df['ppsf'].mean()
        
        estimate = avg_ppsf * sqft
        
        # Adjustments
        if 'beds' in zip_df.columns:
            estimate += (beds - zip_df['beds'].mean()) * 15000
        if 'baths' in zip_df.columns:
            estimate += (baths - zip_df['baths'].mean()) * 10000
        if 'age' in zip_df.columns:
            age_adj = 1 - ((age - zip_df['age'].mean()) * 0.005)
            estimate *= max(0.7, min(1.3, age_adj))
        
        min_price = zip_df['price'].min() * 0.6
        max_price = zip_df['price'].max() * 1.4
        estimate = max(min_price, min(max_price, estimate))
        
        return round(estimate, 2), 'zip_avg_sfr', None, comparables
    except Exception as e:
        print(f"Fallback calc error: {e}")
        return None, None, "calculation_error", comparables


def fallback_estimate(zip_code, sqft, beds, baths, age):
    """Regional fallback when no ZIP data available."""
    zip_prefix = int(str(zip_code)[0]) if zip_code else 5
    
    # Regional price per sqft estimates
    regional = {
        0: 300, 1: 280, 2: 250, 3: 200, 4: 180,
        5: 190, 6: 170, 7: 180, 8: 220, 9: 400
    }
    
    ppsf = regional.get(zip_prefix, 220)
    estimate = sqft * ppsf
    
    if beds > 3:
        estimate += (beds - 3) * 15000
    if baths > 2:
        estimate += (baths - 2) * 10000
    
    age_factor = max(1 - (age * 0.004), 0.7)
    estimate *= age_factor
    
    return round(max(estimate, 100000), 2)


# ============================================
# API Routes
# ============================================

@app.route('/', methods=['GET'])
def index():
    """Health check."""
    return jsonify({
        'status': 'API running',
        'version': '3.0.0',
        'region': 'Bay Area, California',
        'data_loaded': housing_df is not None,
        'records': len(housing_df) if housing_df is not None else 0,
        'supported_zips': len(supported_zips),
        'model_loaded': global_model is not None,
        'min_comparables': MIN_COMPARABLE_HOMES
    })


@app.route('/health', methods=['GET'])
def health():
    """Detailed health check."""
    return jsonify({
        'status': 'healthy',
        'data': 'loaded' if housing_df is not None else 'missing',
        'model': 'loaded' if global_model is not None else 'missing',
        'ml_available': ML_AVAILABLE
    })


@app.route('/supported-zips', methods=['GET'])
def get_supported_zips():
    """
    Returns list of supported Bay Area ZIP codes.
    This model only works for these California ZIP codes.
    """
    zip_list = sorted(list(supported_zips)) if supported_zips else []
    
    return jsonify({
        'region': 'Bay Area, California',
        'total_zips': len(zip_list),
        'zip_codes': zip_list,
        'note': 'This estimator only supports Bay Area (California) ZIP codes.'
    })


@app.route('/predict', methods=['POST'])
def predict():
    """
    Main prediction endpoint.
    Uses ZIP-filtered SFR-only data for estimates.
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No data provided',
                'message': 'Send JSON with: zip, sqft, beds, baths, age'
            }), 400
        
        # Parse inputs
        try:
            zip_code = None
            for key in ['zip', 'zipcode', 'zip_code']:
                if key in data:
                    zip_code = int(str(data[key]).strip()[:5])
                    break
            
            sqft = float(data['sqft'])
            beds = int(data['beds'])
            baths = float(data['baths'])
            age = int(data.get('age', 30))
        except (ValueError, KeyError, TypeError) as e:
            return jsonify({
                'error': 'Invalid input',
                'message': str(e)
            }), 400
        
        # Validate ranges
        if sqft < 100 or sqft > 50000:
            return jsonify({'error': 'sqft must be 100-50000'}), 400
        if beds < 0 or beds > 10:
            return jsonify({'error': 'beds must be 0-10'}), 400
        if baths < 0 or baths > 10:
            return jsonify({'error': 'baths must be 0-10'}), 400
        if zip_code and (zip_code < 501 or zip_code > 99950):
            return jsonify({'error': 'Invalid ZIP code'}), 400
        
        # Validate ZIP is in supported Bay Area ZIP codes
        if zip_code and len(supported_zips) > 0 and zip_code not in supported_zips:
            return jsonify({
                'error': 'Unsupported ZIP code. This model only supports Bay Area (California) ZIP codes.',
                'zip_code': zip_code,
                'supported_count': len(supported_zips)
            }), 400
        
        # Get estimate
        estimate = None
        method = None
        comparables = 0
        
        if zip_code and housing_df is not None:
            estimate, method, error, comparables = estimate_by_zip(
                zip_code, sqft, beds, baths, age
            )
            
            if error == "no_homes_in_zip":
                return jsonify({
                    'error': 'No data for this ZIP code',
                    'zip_code': zip_code
                }), 400
            
            if error == "no_sfr_in_zip":
                return jsonify({
                    'error': 'No single-family homes in this ZIP',
                    'message': 'Only condos/apartments available',
                    'zip_code': zip_code
                }), 400
            
            if error == "not_enough_comparables":
                return jsonify({
                    'error': 'Not enough comparable single-family homes',
                    'message': f'Found {comparables}, need {MIN_COMPARABLE_HOMES}',
                    'zip_code': zip_code
                }), 400
        
        # Fallback
        if estimate is None:
            estimate = fallback_estimate(zip_code, sqft, beds, baths, age)
            method = 'regional_fallback'
        
        return jsonify({
            'estimate': estimate,
            'method': method,
            'comparables': comparables,
            'input': {
                'zip_code': zip_code,
                'sqft': sqft,
                'beds': beds,
                'baths': baths,
                'age': age
            }
        })
    
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'Prediction failed'}), 500


@app.route('/predict', methods=['OPTIONS'])
def predict_options():
    return '', 204


@app.route('/debug/<int:zip_code>', methods=['GET'])
def debug_zip(zip_code):
    """Debug endpoint to inspect ZIP data."""
    if housing_df is None:
        return jsonify({'error': 'No data loaded'}), 500
    
    zip_df, error = get_zip_data(zip_code)
    
    if error:
        return jsonify({'error': error, 'zip_code': zip_code}), 400
    
    return jsonify({
        'zip_code': zip_code,
        'total_records': len(zip_df),
        'price_stats': {
            'min': float(zip_df['price'].min()),
            'max': float(zip_df['price'].max()),
            'median': float(zip_df['price'].median()),
            'mean': float(zip_df['price'].mean())
        },
        'sqft_stats': {
            'min': float(zip_df['sqft'].min()),
            'max': float(zip_df['sqft'].max()),
            'mean': float(zip_df['sqft'].mean())
        },
        'property_types': zip_df['property_type'].value_counts().to_dict() if 'property_type' in zip_df.columns else {},
        'sample_listings': zip_df[['price', 'sqft', 'beds', 'baths']].head(10).to_dict('records')
    })


# ============================================
# Error Handlers
# ============================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Server error'}), 500


# ============================================
# Main
# ============================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
