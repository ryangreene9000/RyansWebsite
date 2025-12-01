"""
Housing Data Cleaning Pipeline
Cleans and validates scraped housing data for ML training.

This script:
- Filters to single-family homes ONLY
- Removes outliers and bad data
- Validates all required fields
- Produces a clean dataset for model training
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime

# ============================================
# Configuration
# ============================================

# File paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DATA_FILE = os.path.join(SCRIPT_DIR, 'housing_data_raw.csv')
CLEAN_DATA_FILE = os.path.join(SCRIPT_DIR, 'housing_data.csv')

# Property types to INCLUDE
INCLUDE_PROPERTY_TYPES = [
    "single family",
    "single family residence",
    "single family residential", 
    "residential",
    "house",
    "sfr",
    "detached"
]

# Property types to EXCLUDE (reject if ANY of these appear)
EXCLUDE_PROPERTY_TYPES = [
    "condo",
    "condominium",
    "townhome", 
    "townhouse",
    "apartment",
    "apt",
    "multi",
    "multi-family",
    "multifamily",
    "duplex",
    "triplex",
    "fourplex",
    "quadplex",
    "mobile",
    "manufactured",
    "land",
    "lot",
    "commercial"
]

# Data quality thresholds
MIN_PRICE = 150000
MAX_PRICE = 10000000
MIN_SQFT = 300
MAX_SQFT = 10000
MAX_BEDS = 8
MAX_BATHS = 8


def load_raw_data():
    """Load raw scraped data."""
    if not os.path.exists(RAW_DATA_FILE):
        print(f"❌ Raw data file not found: {RAW_DATA_FILE}")
        print("Run scraper.py first to collect data.")
        return None
    
    df = pd.read_csv(RAW_DATA_FILE)
    print(f"📊 Loaded {len(df)} raw records")
    return df


def filter_property_type(df):
    """
    Filter to single-family homes only.
    Excludes condos, townhouses, apartments, etc.
    """
    initial_count = len(df)
    
    # Create lowercase property type for matching
    df['property_type_clean'] = df['property_type'].astype(str).str.lower().str.strip()
    
    # Step 1: Exclude unwanted types
    exclude_mask = df['property_type_clean'].apply(
        lambda x: any(exc in x for exc in EXCLUDE_PROPERTY_TYPES)
    )
    df = df[~exclude_mask]
    excluded_count = initial_count - len(df)
    print(f"  Excluded {excluded_count} non-SFR properties (condos, townhomes, etc.)")
    
    # Step 2: Include only valid SFR types
    include_mask = df['property_type_clean'].apply(
        lambda x: any(inc in x for inc in INCLUDE_PROPERTY_TYPES)
    )
    df = df[include_mask]
    
    final_count = len(df)
    print(f"  Kept {final_count} single-family residential listings")
    
    return df


def filter_price(df):
    """Remove listings with invalid prices."""
    initial = len(df)
    
    # Must have price
    df = df[df['price'].notna()]
    
    # Price bounds
    df = df[(df['price'] >= MIN_PRICE) & (df['price'] <= MAX_PRICE)]
    
    removed = initial - len(df)
    print(f"  Removed {removed} listings with invalid prices (${MIN_PRICE:,} - ${MAX_PRICE:,})")
    return df


def filter_sqft(df):
    """Remove listings with invalid square footage."""
    initial = len(df)
    
    df = df[df['sqft'].notna()]
    df = df[(df['sqft'] >= MIN_SQFT) & (df['sqft'] <= MAX_SQFT)]
    
    removed = initial - len(df)
    print(f"  Removed {removed} listings with invalid sqft ({MIN_SQFT} - {MAX_SQFT})")
    return df


def filter_beds_baths(df):
    """Remove listings with unreasonable bed/bath counts."""
    initial = len(df)
    
    df = df[(df['beds'] >= 0) & (df['beds'] <= MAX_BEDS)]
    df = df[(df['baths'] >= 0) & (df['baths'] <= MAX_BATHS)]
    
    removed = initial - len(df)
    print(f"  Removed {removed} listings with invalid beds/baths (max {MAX_BEDS}/{MAX_BATHS})")
    return df


def filter_zip_code(df):
    """Ensure valid ZIP codes."""
    initial = len(df)
    
    df = df[df['zip_code'].notna()]
    df['zip_code'] = df['zip_code'].astype(int)
    df = df[(df['zip_code'] >= 501) & (df['zip_code'] <= 99950)]
    
    removed = initial - len(df)
    print(f"  Removed {removed} listings with invalid ZIP codes")
    return df


def add_derived_features(df):
    """Add calculated features for ML training."""
    # Price per square foot
    df['price_per_sqft'] = df['price'] / df['sqft']
    
    # Age (if not present)
    if 'age' not in df.columns or df['age'].isna().all():
        current_year = datetime.now().year
        if 'year_built' in df.columns:
            df['age'] = current_year - df['year_built']
            df['age'] = df['age'].clip(0, 150)  # Cap at 150 years
        else:
            df['age'] = 30  # Default
    
    # Fill missing ages
    df['age'] = df['age'].fillna(30)
    
    print(f"  Added derived features (price_per_sqft, age)")
    return df


def remove_outliers(df, column, lower_percentile=1, upper_percentile=99):
    """Remove statistical outliers using percentile method."""
    initial = len(df)
    
    lower = df[column].quantile(lower_percentile / 100)
    upper = df[column].quantile(upper_percentile / 100)
    
    df = df[(df[column] >= lower) & (df[column] <= upper)]
    
    removed = initial - len(df)
    print(f"  Removed {removed} outliers in {column} (p{lower_percentile}-p{upper_percentile})")
    return df


def print_zip_summary(df, zip_code):
    """Print detailed summary for a ZIP code."""
    zip_df = df[df['zip_code'] == zip_code]
    
    print(f"\n{'='*60}")
    print(f"ZIP {zip_code} SUMMARY:")
    print(f"{'='*60}")
    
    if len(zip_df) == 0:
        print("  No data for this ZIP code")
        return
    
    print(f"\nPrice Statistics:")
    print(zip_df['price'].describe())
    
    print(f"\nProperty Type Distribution:")
    print(zip_df['property_type'].value_counts())
    
    print(f"\nTotal records used: {len(zip_df)}")
    
    median_price = zip_df['price'].median()
    print(f"\n📊 Median price: ${median_price:,.0f}")
    
    # Debug check for Bay Area zips
    if median_price < 1500000 and zip_code in [94070, 94301, 94022, 94024, 94027]:
        print("\n⚠️  WARNING: Median seems low for this high-value area!")
        print("\nSample listings for debugging:")
        sample = zip_df[['price', 'sqft', 'beds', 'baths', 'property_type', 'age']].head(10)
        print(sample.to_string())
        
        print(f"\nPrice range: ${zip_df['price'].min():,.0f} - ${zip_df['price'].max():,.0f}")
        print(f"Sqft range: {zip_df['sqft'].min():.0f} - {zip_df['sqft'].max():.0f}")


def clean_data():
    """Main data cleaning pipeline."""
    print("\n" + "="*60)
    print("HOUSING DATA CLEANING PIPELINE")
    print("="*60)
    
    # Load raw data
    df = load_raw_data()
    if df is None:
        return None
    
    print(f"\n📋 Starting with {len(df)} records\n")
    
    # Apply filters in sequence
    print("Step 1: Filter property types (SFR only)")
    df = filter_property_type(df)
    
    print("\nStep 2: Filter prices")
    df = filter_price(df)
    
    print("\nStep 3: Filter square footage")
    df = filter_sqft(df)
    
    print("\nStep 4: Filter beds/baths")
    df = filter_beds_baths(df)
    
    print("\nStep 5: Filter ZIP codes")
    df = filter_zip_code(df)
    
    print("\nStep 6: Add derived features")
    df = add_derived_features(df)
    
    print("\nStep 7: Remove statistical outliers")
    df = remove_outliers(df, 'price_per_sqft', 2, 98)
    
    # Sort by ZIP and price
    df = df.sort_values(['zip_code', 'price'])
    
    # Print summaries for each ZIP
    print("\n" + "="*60)
    print("ZIP CODE SUMMARIES")
    print("="*60)
    
    for zip_code in df['zip_code'].unique():
        print_zip_summary(df, zip_code)
    
    # Keep only needed columns
    output_columns = [
        'zip_code', 'price', 'sqft', 'beds', 'baths', 'age',
        'property_type', 'price_per_sqft'
    ]
    df_output = df[[col for col in output_columns if col in df.columns]]
    
    # Save cleaned data
    df_output.to_csv(CLEAN_DATA_FILE, index=False)
    
    print("\n" + "="*60)
    print(f"✅ CLEANING COMPLETE")
    print(f"   Input:  {len(pd.read_csv(RAW_DATA_FILE))} records")
    print(f"   Output: {len(df_output)} clean SFR records")
    print(f"   Saved to: {CLEAN_DATA_FILE}")
    print("="*60)
    
    return df_output


if __name__ == '__main__':
    clean_data()

