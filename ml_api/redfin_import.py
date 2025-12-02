#!/usr/bin/env python3
"""
Redfin CSV Import Script

This script processes CSV exports from Redfin and prepares them
for the housing price estimator model.

Usage:
    python redfin_import.py path/to/redfin_export.csv

The script will:
1. Load and normalize the Redfin CSV
2. Filter to single-family residential homes only
3. Filter to SOLD homes only
4. Extract relevant features (price, sqft, beds, baths, year_built, zip_code)
5. Clean and validate data
6. Export cleaned data per ZIP code to data/redfin_clean/
7. Generate data/supported_zipcodes.json listing all supported ZIP codes

Supported Redfin column variations:
- ZIP OR POSTAL CODE, ZIP CODE, POSTAL CODE -> zip_code
- SOLD PRICE, PRICE, CLOSE PRICE -> price
- SQUARE FEET, SQFT -> sqft
- BEDS, BEDROOMS -> beds
- BATHS, BATHROOMS -> baths
- YEAR BUILT -> year_built
- PROPERTY TYPE, HOME TYPE -> property_type
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime

# ============================================
# Configuration
# ============================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
RAW_DATA_DIR = os.path.join(PROJECT_ROOT, 'data', 'redfin_raw')
CLEAN_DATA_DIR = os.path.join(PROJECT_ROOT, 'data', 'redfin_clean')
SUPPORTED_ZIPS_PATH = os.path.join(PROJECT_ROOT, 'data', 'supported_zipcodes.json')
HOUSING_DATA_PATH = os.path.join(SCRIPT_DIR, 'housing_data.csv')

# Property type filters
INCLUDE_PROPERTY_TYPES = [
    "single family residential", "single family", "residential",
    "house", "detached", "single-family"
]

EXCLUDE_PROPERTY_TYPES = [
    "condo", "condominium", "townhome", "townhouse", "apartment", "apt",
    "multi", "multi-family", "multifamily", "duplex", "triplex", "fourplex",
    "quadplex", "mobile", "manufactured", "land", "lot", "commercial"
]

# Data quality bounds
MIN_PRICE = 150000
MAX_PRICE = 15000000  # Bay Area can have expensive homes
MIN_SQFT = 300
MAX_SQFT = 12000
MAX_BEDS = 10
MAX_BATHS = 10

# Column name mappings (Redfin variations)
COLUMN_MAPPINGS = {
    # ZIP code variations
    'zip or postal code': 'zip_code',
    'zip code': 'zip_code',
    'postal code': 'zip_code',
    'zip': 'zip_code',
    'zipcode': 'zip_code',
    
    # Price variations
    'sold price': 'price',
    'close price': 'price',
    'sale price': 'price',
    'price': 'price',
    'last sale price': 'price',
    
    # Size variations
    'square feet': 'sqft',
    'sqft': 'sqft',
    'sq ft': 'sqft',
    'living area': 'sqft',
    
    # Bedroom variations
    'beds': 'beds',
    'bedrooms': 'beds',
    'bed': 'beds',
    
    # Bathroom variations
    'baths': 'baths',
    'bathrooms': 'baths',
    'bath': 'baths',
    
    # Year built
    'year built': 'year_built',
    'built': 'year_built',
    
    # Property type
    'property type': 'property_type',
    'home type': 'property_type',
    'type': 'property_type',
    
    # Sale status
    'sale type': 'sale_type',
    'status': 'status',
}


# ============================================
# Helper Functions
# ============================================

def normalize_columns(df):
    """Normalize column names to standard format."""
    df.columns = df.columns.str.lower().str.strip()
    
    # Apply column mappings
    rename_map = {}
    for col in df.columns:
        if col in COLUMN_MAPPINGS:
            rename_map[col] = COLUMN_MAPPINGS[col]
    
    df = df.rename(columns=rename_map)
    return df


def is_single_family(property_type):
    """Check if property type is single-family residential."""
    if pd.isna(property_type) or not property_type:
        return False
    
    prop_lower = str(property_type).lower().strip()
    
    # Exclude non-SFR types first
    for exc in EXCLUDE_PROPERTY_TYPES:
        if exc in prop_lower:
            return False
    
    # Check for SFR types
    for inc in INCLUDE_PROPERTY_TYPES:
        if inc in prop_lower:
            return True
    
    return False


def clean_numeric(value):
    """Clean numeric value, removing currency symbols and commas."""
    if pd.isna(value):
        return None
    
    try:
        # Handle string values
        if isinstance(value, str):
            value = value.replace('$', '').replace(',', '').strip()
        return float(value)
    except (ValueError, TypeError):
        return None


def calculate_age(year_built):
    """Calculate home age from year built."""
    if pd.isna(year_built):
        return 30  # Default age
    
    try:
        current_year = datetime.now().year
        age = current_year - int(year_built)
        return max(0, min(150, age))  # Bound to reasonable range
    except (ValueError, TypeError):
        return 30


# ============================================
# Main Import Function
# ============================================

def import_redfin_csv(csv_path):
    """
    Import and clean a Redfin CSV file.
    
    Returns:
        tuple: (cleaned_df, zip_counts, error_message)
    """
    print(f"\n📁 Loading: {csv_path}")
    
    if not os.path.exists(csv_path):
        return None, None, f"File not found: {csv_path}"
    
    try:
        # Load CSV
        df = pd.read_csv(csv_path)
        print(f"   Raw records: {len(df)}")
        
        # Normalize column names
        df = normalize_columns(df)
        print(f"   Columns: {list(df.columns)}")
        
        # Check required columns
        required = ['price', 'sqft', 'beds', 'baths', 'zip_code']
        missing = [col for col in required if col not in df.columns]
        
        if missing:
            return None, None, f"Missing required columns: {missing}"
        
        # Filter to single-family homes only
        if 'property_type' in df.columns:
            df = df[df['property_type'].apply(is_single_family)]
            print(f"   After SFR filter: {len(df)}")
        else:
            print("   ⚠️ No property_type column - assuming all are SFR")
        
        # Filter to SOLD homes if status column exists
        if 'status' in df.columns:
            df = df[df['status'].str.lower().str.contains('sold', na=False)]
            print(f"   After SOLD filter: {len(df)}")
        
        if 'sale_type' in df.columns:
            # Keep only actual sales, not pending
            df = df[~df['sale_type'].str.lower().str.contains('pending|active', na=False)]
            print(f"   After sale_type filter: {len(df)}")
        
        # Clean numeric columns
        df['price'] = df['price'].apply(clean_numeric)
        df['sqft'] = df['sqft'].apply(clean_numeric)
        df['beds'] = df['beds'].apply(clean_numeric)
        df['baths'] = df['baths'].apply(clean_numeric)
        
        # Clean ZIP code
        df['zip_code'] = df['zip_code'].apply(lambda x: int(str(x)[:5]) if pd.notna(x) else None)
        
        # Calculate age
        if 'year_built' in df.columns:
            df['age'] = df['year_built'].apply(calculate_age)
        else:
            df['age'] = 30  # Default
        
        # Remove rows with missing required values
        df = df.dropna(subset=['price', 'sqft', 'beds', 'baths', 'zip_code'])
        print(f"   After NaN removal: {len(df)}")
        
        # Apply data quality filters
        df = df[
            (df['price'] >= MIN_PRICE) & 
            (df['price'] <= MAX_PRICE) &
            (df['sqft'] >= MIN_SQFT) &
            (df['sqft'] <= MAX_SQFT) &
            (df['beds'] <= MAX_BEDS) &
            (df['baths'] <= MAX_BATHS)
        ]
        print(f"   After quality filters: {len(df)}")
        
        if len(df) == 0:
            return None, None, "No valid records after filtering"
        
        # Convert types
        df['zip_code'] = df['zip_code'].astype(int)
        df['beds'] = df['beds'].astype(int)
        df['age'] = df['age'].astype(int)
        
        # Select final columns
        final_cols = ['price', 'sqft', 'beds', 'baths', 'age', 'zip_code']
        if 'property_type' in df.columns:
            final_cols.append('property_type')
        
        df = df[final_cols]
        
        # Get ZIP code counts
        zip_counts = df['zip_code'].value_counts().to_dict()
        
        return df, zip_counts, None
        
    except Exception as e:
        return None, None, f"Error processing file: {str(e)}"


def save_cleaned_data(df, zip_counts):
    """Save cleaned data and supported ZIP codes list."""
    
    # Create directories
    os.makedirs(CLEAN_DATA_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(SUPPORTED_ZIPS_PATH), exist_ok=True)
    
    # Save per-ZIP CSVs
    for zip_code in df['zip_code'].unique():
        zip_df = df[df['zip_code'] == zip_code]
        zip_path = os.path.join(CLEAN_DATA_DIR, f'homes_{zip_code}.csv')
        zip_df.to_csv(zip_path, index=False)
        print(f"   💾 Saved: homes_{zip_code}.csv ({len(zip_df)} records)")
    
    # Save combined housing_data.csv for the API
    df.to_csv(HOUSING_DATA_PATH, index=False)
    print(f"\n   💾 Saved combined dataset: {HOUSING_DATA_PATH} ({len(df)} records)")
    
    # Save supported ZIP codes JSON
    zip_list = sorted([int(z) for z in df['zip_code'].unique()])
    supported_data = {
        'region': 'Bay Area, California',
        'total_zips': len(zip_list),
        'zip_codes': zip_list,
        'generated_at': datetime.now().isoformat(),
        'total_records': len(df),
        'zip_counts': {str(k): v for k, v in zip_counts.items()}
    }
    
    with open(SUPPORTED_ZIPS_PATH, 'w') as f:
        json.dump(supported_data, f, indent=2)
    
    print(f"\n   📋 Saved supported ZIP codes: {SUPPORTED_ZIPS_PATH}")
    print(f"\n✅ Dataset ready. {len(zip_list)} Bay Area ZIP codes loaded.")
    
    return zip_list


# ============================================
# Main
# ============================================

def main():
    """Main entry point."""
    print("\n" + "=" * 50)
    print("🏠 Redfin CSV Import Tool")
    print("=" * 50)
    
    # Check for input file
    if len(sys.argv) < 2:
        # Look for any CSV in redfin_raw folder
        os.makedirs(RAW_DATA_DIR, exist_ok=True)
        csv_files = [f for f in os.listdir(RAW_DATA_DIR) if f.endswith('.csv')]
        
        if csv_files:
            print(f"\n📂 Found {len(csv_files)} CSV file(s) in {RAW_DATA_DIR}")
        else:
            print(f"\n❌ No CSV files found.")
            print(f"\nUsage: python redfin_import.py <path_to_redfin.csv>")
            print(f"\nOr place CSV files in: {RAW_DATA_DIR}")
            return 1
        
        csv_paths = [os.path.join(RAW_DATA_DIR, f) for f in csv_files]
    else:
        csv_paths = [sys.argv[1]]
    
    # Process all CSV files
    all_dfs = []
    all_zip_counts = {}
    
    for csv_path in csv_paths:
        df, zip_counts, error = import_redfin_csv(csv_path)
        
        if error:
            print(f"\n❌ Error: {error}")
            continue
        
        all_dfs.append(df)
        all_zip_counts.update(zip_counts)
    
    if not all_dfs:
        print("\n❌ No valid data to process")
        return 1
    
    # Combine all data
    combined_df = pd.concat(all_dfs, ignore_index=True)
    print(f"\n📊 Combined dataset: {len(combined_df)} records")
    
    # Print summary
    print("\n📈 Price Summary:")
    print(combined_df['price'].describe())
    
    print("\n🏘️ Top 10 ZIP codes by record count:")
    for zip_code, count in sorted(all_zip_counts.items(), key=lambda x: -x[1])[:10]:
        median = combined_df[combined_df['zip_code'] == zip_code]['price'].median()
        print(f"   {zip_code}: {count} homes (median: ${median:,.0f})")
    
    # Save cleaned data
    zip_list = save_cleaned_data(combined_df, all_zip_counts)
    
    print("\n" + "=" * 50)
    print("✅ Import complete!")
    print(f"   Total ZIP codes: {len(zip_list)}")
    print(f"   Total records: {len(combined_df)}")
    print("=" * 50 + "\n")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

