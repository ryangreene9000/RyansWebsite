#!/usr/bin/env python3
"""
Housing Data Pipeline Runner
Runs the complete data pipeline: scrape → clean → train

Usage:
    python run_pipeline.py              # Run full pipeline
    python run_pipeline.py --clean      # Clean data only
    python run_pipeline.py --train      # Train model only
    python run_pipeline.py --test 94070 # Test specific ZIP
"""

import sys
import os

# Add script directory to path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)


def run_scraper():
    """Run the housing data scraper."""
    print("\n" + "="*60)
    print("STEP 1: SCRAPING HOUSING DATA")
    print("="*60)
    
    try:
        from scraper import main as scrape_main
        scrape_main()
        return True
    except Exception as e:
        print(f"❌ Scraper failed: {e}")
        return False


def run_cleaner():
    """Run the data cleaning pipeline."""
    print("\n" + "="*60)
    print("STEP 2: CLEANING DATA")
    print("="*60)
    
    try:
        from clean_data import clean_data
        result = clean_data()
        return result is not None
    except Exception as e:
        print(f"❌ Cleaning failed: {e}")
        return False


def run_trainer():
    """Run the model training."""
    print("\n" + "="*60)
    print("STEP 3: TRAINING MODEL")
    print("="*60)
    
    try:
        from train_model import main as train_main
        train_main()
        return True
    except Exception as e:
        print(f"❌ Training failed: {e}")
        return False


def test_zip(zip_code):
    """Test predictions for a specific ZIP code."""
    print("\n" + "="*60)
    print(f"TESTING ZIP CODE: {zip_code}")
    print("="*60)
    
    try:
        import pandas as pd
        import numpy as np
        from app import get_zip_data, estimate_by_zip
        
        # Get ZIP data
        zip_df, error = get_zip_data(zip_code)
        
        if error:
            print(f"❌ Error getting data: {error}")
            return
        
        print(f"\n📊 Found {len(zip_df)} SFR records for ZIP {zip_code}")
        print(f"\nPrice Statistics:")
        print(zip_df['price'].describe())
        
        # Test predictions for typical homes
        test_cases = [
            {'sqft': 1500, 'beds': 3, 'baths': 2, 'age': 30},
            {'sqft': 1800, 'beds': 3, 'baths': 2, 'age': 30},
            {'sqft': 2000, 'beds': 4, 'baths': 2, 'age': 40},
            {'sqft': 2500, 'beds': 4, 'baths': 3, 'age': 20},
        ]
        
        print(f"\n🏠 Test Predictions:")
        for case in test_cases:
            estimate, method, error, comps = estimate_by_zip(
                zip_code, case['sqft'], case['beds'], case['baths'], case['age']
            )
            
            if estimate:
                print(f"  {case['sqft']}sqft {case['beds']}BR/{case['baths']}BA: ${estimate:,.0f} ({method})")
            else:
                print(f"  {case['sqft']}sqft: Error - {error}")
        
        # Validation check
        median_price = zip_df['price'].median()
        print(f"\n📈 Median price in ZIP: ${median_price:,.0f}")
        
        if zip_code == 94070 and median_price < 1500000:
            print("\n⚠️  WARNING: 94070 median seems low!")
            print("Expected ~$2M for San Carlos SFR")
            print("\nSample listings:")
            print(zip_df[['price', 'sqft', 'beds', 'baths', 'property_type']].head(10))
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Run the full pipeline."""
    args = sys.argv[1:]
    
    if '--clean' in args:
        run_cleaner()
    elif '--train' in args:
        run_trainer()
    elif '--test' in args:
        idx = args.index('--test')
        if idx + 1 < len(args):
            zip_code = int(args[idx + 1])
            test_zip(zip_code)
        else:
            print("Usage: python run_pipeline.py --test <ZIP_CODE>")
    else:
        # Full pipeline
        print("\n" + "="*60)
        print("HOUSING DATA PIPELINE")
        print("SFR-Only Sold Listings")
        print("="*60)
        
        # Note: Scraper needs API configuration
        print("\n⚠️  Note: Scraper requires API configuration.")
        print("Skipping scrape step - using existing data if available.")
        
        # Clean
        if run_cleaner():
            # Train
            run_trainer()
            
            # Test high-value ZIP
            print("\n" + "="*60)
            print("VALIDATION TEST")
            print("="*60)
            test_zip(94070)
        
        print("\n" + "="*60)
        print("✅ PIPELINE COMPLETE")
        print("="*60)


if __name__ == '__main__':
    main()

