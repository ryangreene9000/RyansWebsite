"""
Housing Data Scraper
Fetches SOLD single-family home listings for the ML Estimator.

This scraper:
- Only includes Single Family Residential properties
- Excludes condos, townhouses, apartments, multi-family
- Uses SOLD prices only (not list prices)
- Validates data quality before saving
"""

import os
import json
import time
import requests
import pandas as pd
from datetime import datetime, timedelta

# ============================================
# Configuration
# ============================================

# Property types to INCLUDE (case-insensitive matching)
INCLUDE_PROPERTY_TYPES = [
    "single family",
    "single family residence", 
    "single family residential",
    "residential",
    "house",
    "sfr",
    "detached"
]

# Property types to EXCLUDE (if any of these appear in the type)
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
MIN_PRICE = 150000      # $150k minimum
MAX_PRICE = 10000000    # $10M maximum
MIN_SQFT = 300
MAX_SQFT = 10000
MAX_BEDS = 8
MAX_BATHS = 8

# Output file
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DATA_FILE = os.path.join(OUTPUT_DIR, 'housing_data_raw.csv')


def is_single_family(property_type):
    """
    Check if property type is single-family residential.
    Returns True only for SFR, excludes condos/townhouses/etc.
    """
    if not property_type:
        return False
    
    prop_type_lower = str(property_type).lower().strip()
    
    # First check exclusions - if any exclusion keyword is present, reject
    for exclude in EXCLUDE_PROPERTY_TYPES:
        if exclude in prop_type_lower:
            return False
    
    # Then check if it matches any inclusion keyword
    for include in INCLUDE_PROPERTY_TYPES:
        if include in prop_type_lower:
            return True
    
    return False


def validate_listing(listing):
    """
    Validate a listing meets all quality criteria.
    Returns (is_valid, reason) tuple.
    """
    # Must have sold price (not just list price)
    sold_price = listing.get('soldPrice') or listing.get('sold_price')
    if not sold_price:
        return False, "no_sold_price"
    
    # Price bounds
    if sold_price < MIN_PRICE:
        return False, f"price_too_low_{sold_price}"
    if sold_price > MAX_PRICE:
        return False, f"price_too_high_{sold_price}"
    
    # Square footage bounds
    sqft = listing.get('sqft') or listing.get('livingArea') or listing.get('squareFeet')
    if not sqft or sqft < MIN_SQFT:
        return False, f"sqft_too_low_{sqft}"
    if sqft > MAX_SQFT:
        return False, f"sqft_too_high_{sqft}"
    
    # Bedroom/bathroom limits
    beds = listing.get('beds') or listing.get('bedrooms') or 0
    baths = listing.get('baths') or listing.get('bathrooms') or 0
    
    if beds > MAX_BEDS:
        return False, f"too_many_beds_{beds}"
    if baths > MAX_BATHS:
        return False, f"too_many_baths_{baths}"
    
    # Property type must be single family
    prop_type = listing.get('property_type') or listing.get('propertyType') or listing.get('homeType')
    if not is_single_family(prop_type):
        return False, f"not_sfr_{prop_type}"
    
    return True, "valid"


def process_listing(raw_listing):
    """
    Process a raw listing into standardized format.
    Only uses SOLD price, never list price.
    """
    # Extract sold price - REQUIRED
    sold_price = (
        raw_listing.get('soldPrice') or 
        raw_listing.get('sold_price') or
        raw_listing.get('lastSoldPrice')
    )
    
    # If no sold price, check if there's a price field and status is SOLD
    if not sold_price:
        status = str(raw_listing.get('status', '')).lower()
        if 'sold' in status:
            sold_price = raw_listing.get('price')
    
    if not sold_price:
        return None  # Skip listings without sold price
    
    # Extract other fields
    listing = {
        'price': int(sold_price),
        'zip_code': extract_zip(raw_listing),
        'sqft': int(raw_listing.get('sqft') or raw_listing.get('livingArea') or raw_listing.get('squareFeet') or 0),
        'beds': int(raw_listing.get('beds') or raw_listing.get('bedrooms') or 0),
        'baths': float(raw_listing.get('baths') or raw_listing.get('bathrooms') or 0),
        'year_built': int(raw_listing.get('yearBuilt') or raw_listing.get('year_built') or 0),
        'property_type': raw_listing.get('property_type') or raw_listing.get('propertyType') or raw_listing.get('homeType') or '',
        'city': raw_listing.get('city', ''),
        'state': raw_listing.get('state', ''),
        'sold_date': raw_listing.get('soldDate') or raw_listing.get('sold_date') or '',
    }
    
    # Calculate age
    current_year = datetime.now().year
    if listing['year_built'] > 1800 and listing['year_built'] <= current_year:
        listing['age'] = current_year - listing['year_built']
    else:
        listing['age'] = 30  # Default age if unknown
    
    return listing


def extract_zip(listing):
    """Extract and validate ZIP code from listing."""
    zip_code = (
        listing.get('zipcode') or 
        listing.get('zip_code') or 
        listing.get('postalCode') or
        listing.get('zip')
    )
    
    if zip_code:
        # Clean and validate
        zip_str = str(zip_code).strip()[:5]
        if zip_str.isdigit() and len(zip_str) == 5:
            return int(zip_str)
    
    return None


def scrape_zip_code(zip_code, api_key=None):
    """
    Scrape sold listings for a specific ZIP code.
    
    This is a placeholder - implement with your preferred data source:
    - Zillow API
    - Redfin API  
    - Realtor.com API
    - MLS data feed
    - Web scraping
    """
    print(f"\n{'='*50}")
    print(f"Scraping ZIP: {zip_code}")
    print(f"{'='*50}")
    
    listings = []
    
    # TODO: Implement actual API calls here
    # Example structure for API response processing:
    """
    response = requests.get(
        f"https://api.example.com/sold-listings",
        params={
            'zip': zip_code,
            'status': 'sold',
            'property_type': 'single_family',
            'sold_within_days': 365
        },
        headers={'Authorization': f'Bearer {api_key}'}
    )
    
    for raw in response.json()['listings']:
        processed = process_listing(raw)
        if processed:
            is_valid, reason = validate_listing(processed)
            if is_valid:
                listings.append(processed)
            else:
                print(f"  Rejected: {reason}")
    """
    
    print(f"  Found {len(listings)} valid SFR sold listings")
    return listings


def print_zip_summary(df, zip_code):
    """Print debug summary for a ZIP code's data."""
    zip_df = df[df['zip_code'] == zip_code]
    
    print(f"\n{'='*50}")
    print(f"ZIP {zip_code} SUMMARY:")
    print(f"{'='*50}")
    
    if len(zip_df) == 0:
        print("  No data for this ZIP code")
        return
    
    print(f"\nPrice Statistics:")
    print(zip_df['price'].describe())
    
    print(f"\nProperty Type Distribution:")
    print(zip_df['property_type'].value_counts())
    
    print(f"\nTotal records used: {len(zip_df)}")
    
    # Additional debugging for high-value areas
    median_price = zip_df['price'].median()
    print(f"\nMedian price: ${median_price:,.0f}")
    
    if median_price < 1500000 and zip_code in [94070, 94301, 94022, 94024, 94027]:
        print("\n⚠️  WARNING: Median seems low for this area!")
        print("Sample listings:")
        print(zip_df[['price', 'sqft', 'beds', 'baths', 'property_type']].head(10))


def main(zip_codes=None):
    """
    Main scraper function.
    
    Args:
        zip_codes: List of ZIP codes to scrape, or None for default list
    """
    # Default ZIP codes (Bay Area for testing)
    if zip_codes is None:
        zip_codes = [
            94070,  # San Carlos
            94301,  # Palo Alto
            94022,  # Los Altos
            94024,  # Los Altos
            94027,  # Atherton
            94025,  # Menlo Park
            94028,  # Portola Valley
            94062,  # Redwood City
            94061,  # Redwood City
            94063,  # Redwood City
        ]
    
    all_listings = []
    
    for zip_code in zip_codes:
        listings = scrape_zip_code(zip_code)
        all_listings.extend(listings)
        time.sleep(1)  # Rate limiting
    
    if not all_listings:
        print("\nNo listings scraped. Check API configuration.")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(all_listings)
    
    # Print summaries
    for zip_code in zip_codes:
        print_zip_summary(df, zip_code)
    
    # Save raw data
    df.to_csv(RAW_DATA_FILE, index=False)
    print(f"\n✅ Saved {len(df)} listings to {RAW_DATA_FILE}")
    
    return df


if __name__ == '__main__':
    main()

