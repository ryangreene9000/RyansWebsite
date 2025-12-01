#!/usr/bin/env python3
"""
Generate Sample Housing Data for Testing
Creates realistic SFR sold data for Bay Area ZIP codes.

Prices reflect actual Q4 2024 single-family home sold prices.
Data is synthetic but calibrated to real market conditions.
"""

import os
import random
import pandas as pd
import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(SCRIPT_DIR, 'housing_data_raw.csv')

# Real median SFR prices by ZIP (Q4 2024 approx)
ZIP_DATA = {
    # San Carlos - median ~$2.1M
    94070: {
        'median_price': 2100000,
        'price_std': 400000,
        'median_sqft': 1800,
        'sqft_std': 400,
        'count': 80
    },
    # Palo Alto - median ~$3.5M
    94301: {
        'median_price': 3500000,
        'price_std': 800000,
        'median_sqft': 2200,
        'sqft_std': 500,
        'count': 60
    },
    # Los Altos - median ~$4M
    94022: {
        'median_price': 4000000,
        'price_std': 900000,
        'median_sqft': 2500,
        'sqft_std': 600,
        'count': 55
    },
    # Los Altos Hills - median ~$4.5M
    94024: {
        'median_price': 4500000,
        'price_std': 1000000,
        'median_sqft': 3000,
        'sqft_std': 700,
        'count': 50
    },
    # Atherton - median ~$6M
    94027: {
        'median_price': 6000000,
        'price_std': 1500000,
        'median_sqft': 4000,
        'sqft_std': 1000,
        'count': 40
    },
    # Menlo Park - median ~$2.8M
    94025: {
        'median_price': 2800000,
        'price_std': 600000,
        'median_sqft': 2000,
        'sqft_std': 450,
        'count': 70
    },
    # Redwood City - median ~$1.8M
    94062: {
        'median_price': 1800000,
        'price_std': 350000,
        'median_sqft': 1700,
        'sqft_std': 350,
        'count': 90
    },
    # Redwood City (other) - median ~$1.6M
    94061: {
        'median_price': 1600000,
        'price_std': 300000,
        'median_sqft': 1600,
        'sqft_std': 300,
        'count': 85
    },
    # Burlingame - median ~$2.5M
    94010: {
        'median_price': 2500000,
        'price_std': 500000,
        'median_sqft': 1900,
        'sqft_std': 400,
        'count': 65
    },
    # San Mateo - median ~$1.9M
    94402: {
        'median_price': 1900000,
        'price_std': 400000,
        'median_sqft': 1750,
        'sqft_std': 350,
        'count': 75
    },
}


def generate_listing(zip_code, zip_info):
    """Generate a single realistic SFR listing."""
    # Base price with variation
    price = int(np.random.normal(zip_info['median_price'], zip_info['price_std']))
    price = max(500000, min(price, 15000000))  # Bounds
    
    # Square footage
    sqft = int(np.random.normal(zip_info['median_sqft'], zip_info['sqft_std']))
    sqft = max(800, min(sqft, 8000))
    
    # Price correlates with sqft
    price_per_sqft = price / sqft
    
    # Beds/baths based on sqft
    if sqft < 1200:
        beds = random.choice([2, 3])
        baths = random.choice([1, 1.5, 2])
    elif sqft < 1800:
        beds = random.choice([3, 3, 4])
        baths = random.choice([2, 2, 2.5])
    elif sqft < 2500:
        beds = random.choice([3, 4, 4, 5])
        baths = random.choice([2, 2.5, 3, 3])
    else:
        beds = random.choice([4, 5, 5, 6])
        baths = random.choice([3, 3.5, 4, 4.5])
    
    # Year built
    year_built = random.choice([
        *range(1920, 1950),    # 30 years
        *range(1950, 1970),    # 20 years
        *range(1970, 1990),    # 20 years  
        *range(1990, 2010),    # 20 years
        *range(2010, 2025),    # 15 years
    ])
    
    # Property type (all SFR)
    prop_type = random.choice([
        'Single Family',
        'Single Family Residence',
        'Residential',
        'House',
        'Single Family Residential'
    ])
    
    return {
        'zip_code': zip_code,
        'price': price,
        'sqft': sqft,
        'beds': beds,
        'baths': baths,
        'year_built': year_built,
        'age': 2025 - year_built,
        'property_type': prop_type,
        'price_per_sqft': round(price_per_sqft, 2)
    }


def generate_all_data():
    """Generate dataset for all ZIP codes."""
    all_listings = []
    
    print("Generating sample SFR sold data...")
    print("-" * 40)
    
    for zip_code, zip_info in ZIP_DATA.items():
        for _ in range(zip_info['count']):
            listing = generate_listing(zip_code, zip_info)
            all_listings.append(listing)
        
        print(f"ZIP {zip_code}: {zip_info['count']} listings (median ${zip_info['median_price']:,})")
    
    df = pd.DataFrame(all_listings)
    
    print("-" * 40)
    print(f"Total: {len(df)} SFR listings")
    
    # Save
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\n✅ Saved to {OUTPUT_FILE}")
    
    # Show summary
    print("\n" + "="*60)
    print("SUMMARY BY ZIP CODE")
    print("="*60)
    
    for zip_code in sorted(df['zip_code'].unique()):
        zip_df = df[df['zip_code'] == zip_code]
        print(f"\nZIP {zip_code}:")
        print(f"  Count: {len(zip_df)}")
        print(f"  Median price: ${zip_df['price'].median():,.0f}")
        print(f"  Price range: ${zip_df['price'].min():,.0f} - ${zip_df['price'].max():,.0f}")
        print(f"  Median sqft: {zip_df['sqft'].median():.0f}")
    
    return df


if __name__ == '__main__':
    generate_all_data()

