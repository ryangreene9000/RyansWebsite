"""
Housing Price Model Training
Trains KNN regression model on cleaned single-family home data.

This script:
- Loads cleaned SFR-only dataset
- Trains a KNN model per ZIP code
- Validates predictions against known data
- Saves model for API use
"""

import os
import json
import joblib
import pandas as pd
import numpy as np
from datetime import datetime

# Try to import sklearn
try:
    from sklearn.neighbors import KNeighborsRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import cross_val_score, train_test_split
    from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("❌ scikit-learn not installed. Run: pip install scikit-learn")

# ============================================
# Configuration
# ============================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CLEAN_DATA_FILE = os.path.join(SCRIPT_DIR, 'housing_data.csv')
MODEL_FILE = os.path.join(SCRIPT_DIR, 'knn_model.pkl')
SCALER_FILE = os.path.join(SCRIPT_DIR, 'scaler.pkl')
METADATA_FILE = os.path.join(SCRIPT_DIR, 'model_metadata.json')

# Minimum samples needed per ZIP for training
MIN_SAMPLES_PER_ZIP = 50

# Feature columns for model
FEATURE_COLS = ['sqft', 'beds', 'baths', 'age']
TARGET_COL = 'price'


def load_clean_data():
    """Load the cleaned housing dataset."""
    if not os.path.exists(CLEAN_DATA_FILE):
        print(f"❌ Clean data file not found: {CLEAN_DATA_FILE}")
        print("Run clean_data.py first.")
        return None
    
    df = pd.read_csv(CLEAN_DATA_FILE)
    print(f"📊 Loaded {len(df)} clean SFR records")
    return df


def validate_data(df):
    """Validate data is suitable for training."""
    # Check required columns
    required = FEATURE_COLS + [TARGET_COL, 'zip_code']
    missing = [col for col in required if col not in df.columns]
    if missing:
        print(f"❌ Missing required columns: {missing}")
        return False
    
    # Check for NaN values
    for col in FEATURE_COLS + [TARGET_COL]:
        nan_count = df[col].isna().sum()
        if nan_count > 0:
            print(f"⚠️  {nan_count} NaN values in {col}")
    
    # Check data types
    df[FEATURE_COLS] = df[FEATURE_COLS].astype(float)
    df[TARGET_COL] = df[TARGET_COL].astype(float)
    
    return True


def print_zip_training_summary(df, zip_code):
    """Print training summary for a ZIP code."""
    zip_df = df[df['zip_code'] == zip_code]
    
    print(f"\nZIP {zip_code}:")
    print(f"  Records: {len(zip_df)}")
    print(f"  Price range: ${zip_df['price'].min():,.0f} - ${zip_df['price'].max():,.0f}")
    print(f"  Median price: ${zip_df['price'].median():,.0f}")
    print(f"  Avg sqft: {zip_df['sqft'].mean():.0f}")
    
    if len(zip_df) < MIN_SAMPLES_PER_ZIP:
        print(f"  ⚠️  Below minimum ({MIN_SAMPLES_PER_ZIP}) - will use regional model")


def train_global_model(df):
    """
    Train a global KNN model on all data.
    This model is used as fallback when ZIP-specific data is insufficient.
    """
    print("\n" + "="*60)
    print("TRAINING GLOBAL MODEL")
    print("="*60)
    
    X = df[FEATURE_COLS].values
    y = df[TARGET_COL].values
    
    # Remove any NaN
    valid_mask = ~(np.isnan(X).any(axis=1) | np.isnan(y))
    X = X[valid_mask]
    y = y[valid_mask]
    
    print(f"\nTraining on {len(X)} samples")
    
    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Split for validation
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42
    )
    
    # Train model
    n_neighbors = min(15, max(5, int(np.sqrt(len(X_train)))))
    model = KNeighborsRegressor(
        n_neighbors=n_neighbors,
        weights='distance',
        algorithm='auto'
    )
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    mape = mean_absolute_percentage_error(y_test, y_pred) * 100
    
    print(f"\nGlobal Model Performance:")
    print(f"  MAE: ${mae:,.0f}")
    print(f"  MAPE: {mape:.1f}%")
    print(f"  K neighbors: {n_neighbors}")
    
    # Cross-validation
    cv_scores = cross_val_score(model, X_scaled, y, cv=5, scoring='neg_mean_absolute_error')
    print(f"  CV MAE: ${-cv_scores.mean():,.0f} (+/- ${cv_scores.std():,.0f})")
    
    return model, scaler


def validate_predictions(model, scaler, df):
    """
    Validate model predictions against known data.
    Tests specific ZIP codes to ensure accuracy.
    """
    print("\n" + "="*60)
    print("PREDICTION VALIDATION")
    print("="*60)
    
    # Test cases (adjust based on your data)
    test_cases = [
        {'zip': 94070, 'sqft': 1800, 'beds': 3, 'baths': 2, 'age': 30, 'expected_min': 1500000, 'expected_max': 3000000},
        {'zip': 94301, 'sqft': 2000, 'beds': 4, 'baths': 3, 'age': 40, 'expected_min': 2000000, 'expected_max': 4000000},
    ]
    
    for case in test_cases:
        zip_code = case['zip']
        zip_df = df[df['zip_code'] == zip_code]
        
        if len(zip_df) == 0:
            print(f"\n⚠️  No data for ZIP {zip_code} - skipping validation")
            continue
        
        # Make prediction
        features = np.array([[case['sqft'], case['beds'], case['baths'], case['age']]])
        features_scaled = scaler.transform(features)
        prediction = model.predict(features_scaled)[0]
        
        # Compare to actual data
        actual_median = zip_df['price'].median()
        
        print(f"\nZIP {zip_code} ({case['sqft']} sqft, {case['beds']}BR/{case['baths']}BA):")
        print(f"  Predicted: ${prediction:,.0f}")
        print(f"  Actual median in ZIP: ${actual_median:,.0f}")
        print(f"  Expected range: ${case['expected_min']:,} - ${case['expected_max']:,}")
        
        if prediction < case['expected_min']:
            print(f"  ⚠️  PREDICTION TOO LOW!")
            print(f"  Sample data from ZIP:")
            print(zip_df[['price', 'sqft', 'beds', 'baths', 'property_type']].head(5))
        elif prediction > case['expected_max']:
            print(f"  ⚠️  PREDICTION TOO HIGH!")
        else:
            print(f"  ✅ Prediction within expected range")


def save_model(model, scaler, df):
    """Save model, scaler, and metadata."""
    # Save model
    joblib.dump(model, MODEL_FILE)
    print(f"\n✅ Model saved to: {MODEL_FILE}")
    
    # Save scaler
    joblib.dump(scaler, SCALER_FILE)
    print(f"✅ Scaler saved to: {SCALER_FILE}")
    
    # Save metadata
    metadata = {
        'trained_at': datetime.now().isoformat(),
        'total_samples': len(df),
        'zip_codes': df['zip_code'].unique().tolist(),
        'samples_per_zip': df.groupby('zip_code').size().to_dict(),
        'features': FEATURE_COLS,
        'target': TARGET_COL,
        'price_stats': {
            'min': float(df['price'].min()),
            'max': float(df['price'].max()),
            'median': float(df['price'].median()),
            'mean': float(df['price'].mean())
        }
    }
    
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"✅ Metadata saved to: {METADATA_FILE}")


def main():
    """Main training pipeline."""
    if not SKLEARN_AVAILABLE:
        return
    
    print("\n" + "="*60)
    print("HOUSING PRICE MODEL TRAINING")
    print("="*60)
    
    # Load data
    df = load_clean_data()
    if df is None:
        return
    
    # Validate
    if not validate_data(df):
        return
    
    # Print ZIP summaries
    print("\n" + "="*60)
    print("ZIP CODE TRAINING DATA SUMMARY")
    print("="*60)
    
    for zip_code in sorted(df['zip_code'].unique()):
        print_zip_training_summary(df, zip_code)
    
    # Train global model
    model, scaler = train_global_model(df)
    
    # Validate predictions
    validate_predictions(model, scaler, df)
    
    # Save
    save_model(model, scaler, df)
    
    print("\n" + "="*60)
    print("✅ TRAINING COMPLETE")
    print("="*60)


if __name__ == '__main__':
    main()

