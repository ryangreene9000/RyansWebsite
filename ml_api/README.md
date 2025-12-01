# Housing Price Estimator API

Flask REST API for ML-powered single-family home price predictions.

## Features

- **SFR-Only**: Only uses single-family residential sold listings
- **ZIP-Specific**: Trains model on ZIP code-specific data
- **Quality Filters**: Removes outliers and bad data
- **Sold Prices Only**: Uses actual sold prices, not list prices
- **KNN Model**: K-Nearest Neighbors regression for accuracy

## Data Pipeline

The estimator uses a 3-step data pipeline:

```
1. scraper.py      → Fetches sold SFR listings
2. clean_data.py   → Filters and validates data
3. train_model.py  → Trains KNN model
```

### Property Type Filter

**INCLUDED** (single-family only):
- Single Family, Single Family Residence
- Residential, House, SFR, Detached

**EXCLUDED** (automatically filtered):
- Condo, Condominium, Townhome, Townhouse
- Apartment, Multi-Family, Duplex, etc.

### Data Quality Filters

- Price: $150,000 - $10,000,000
- Square feet: 300 - 10,000
- Beds: 0-8, Baths: 0-8
- Sold listings only (no pending/active)

## Installation

```bash
cd ml_api
pip install -r requirements.txt
```

## Quick Start

### 1. Generate Sample Data (for testing)

```bash
python sample_data.py
```

### 2. Run Full Pipeline

```bash
python run_pipeline.py
```

Or run steps individually:

```bash
python clean_data.py    # Clean raw data
python train_model.py   # Train model
```

### 3. Start API

```bash
# Development
python app.py

# Production
gunicorn app:app -b 0.0.0.0:5000
```

## API Endpoints

### Health Check

```bash
GET /
```

Response:
```json
{
  "status": "API running",
  "version": "3.0.0",
  "data_loaded": true,
  "records": 670
}
```

### Predict Price

```bash
POST /predict
Content-Type: application/json

{
  "zip": 94070,
  "sqft": 1800,
  "beds": 3,
  "baths": 2,
  "age": 30
}
```

Response:
```json
{
  "estimate": 2150000.00,
  "method": "zip_ml_sfr",
  "comparables": 80,
  "input": {
    "zip_code": 94070,
    "sqft": 1800,
    "beds": 3,
    "baths": 2,
    "age": 30
  }
}
```

### Debug ZIP Data

```bash
GET /debug/94070
```

Shows statistics for a specific ZIP code.

## Error Responses

| Error | Description |
|-------|-------------|
| `no_homes_in_zip` | No housing data for this ZIP |
| `no_sfr_in_zip` | Only condos/apartments in ZIP |
| `not_enough_comparables` | Need 50+ SFR listings |

## Testing

```bash
# Test specific ZIP code
python run_pipeline.py --test 94070

# Expected output for 94070 (San Carlos):
# Median: ~$2,100,000
# 1800 sqft 3BR/2BA: ~$2,000,000 - $2,200,000
```

## Deployment to Render

1. Push to GitHub
2. Create new Web Service on Render
3. Set:
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn app:app`
4. Deploy

## File Structure

```
ml_api/
├── app.py              # Flask API
├── scraper.py          # Data scraper
├── clean_data.py       # Data cleaning
├── train_model.py      # Model training
├── run_pipeline.py     # Pipeline runner
├── sample_data.py      # Sample data generator
├── requirements.txt    # Dependencies
├── runtime.txt         # Python version
├── housing_data.csv    # Cleaned SFR data
├── knn_model.pkl       # Trained model
└── scaler.pkl          # Feature scaler
```

## Accuracy

For Bay Area single-family homes:
- MAE: ~$150,000 (typical)
- MAPE: ~8-12%
- Best for: 1000-4000 sqft, 2-5 beds

## License

© 2025 Ryan Greene - All Rights Reserved
