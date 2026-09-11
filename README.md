# SkyMetric - India Airfare Price Index System

Real-time airfare price index for Indian domestic corridors, weighted by DGCA passenger traffic data.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest skymetric/tests/ -v

# Start API server
python -m skymetric.main serve --port 8000

# Launch dashboard
python -m skymetric.main dashboard
```

## Architecture

```
skymetric/
├── scraper/          # Web scraping adapters (mock + live modes)
├── pipeline/         # ETL: cleaning, outlier removal, normalization
├── index_engine/     # Jevons/Laspeyres index calculation
├── api/              # FastAPI REST endpoints
├── dashboard/        # Streamlit interactive dashboard
├── models/           # SQLAlchemy ORM models
├── config/           # Pydantic settings
├── data/             # DGCA weights, seed data generator
└── tests/            # Pytest test suite
```

## API Endpoints

| Endpoint | Description |
|---|---|
| `GET /api/v1/health` | Health check |
| `GET /api/v1/index/daily` | National SkyMetric for a date |
| `GET /api/v1/index/sectors` | Per-corridor index breakdown |
| `GET /api/v1/routes/heatmap` | Sector x time heatmap matrix |
| `GET /api/v1/routes/carriers` | Carrier market share data |
| `GET /api/v1/elasticity/` | Advance-purchase elasticity curves |

## Monitored Corridors

| Route | DGCA Weight | Classification |
|---|---|---|
| DEL-BOM | 18.4% | Metro Trunk |
| DEL-BLR | 14.2% | Metro Trunk |
| BOM-BLR | 12.1% | Metro Trunk |
| DEL-CCU | 10.5% | Metro Trunk |
| DEL-HYD | 8.3% | Metro Trunk |
| BOM-MAA | 6.7% | Metro Trunk |
| BLR-HYD | 5.8% | Metro Trunk |
| DEL-MAA | 5.2% | Metro Trunk |
| DEL-IXS | 5.8% | Regional Thin |
| DEL-DHM | 3.0% | Regional Thin |

## Advance Windows

- **T+1**: Emergency / last-minute (145% of base)
- **T+7**: Short-horizon (118% of base)
- **T+15**: Headline anchor (100% base)
- **T+30**: Consumer baseline (88% of base)
- **T+45**: Early bird (82% of base)

## Index Formulas

- **Jevons**: Geometric mean of price ratios (elementary level)
- **Laspeyres**: DGCA passenger-weighted arithmetic mean (upper level)
- **Chain-Laspeyres**: Period-to-period linking for rolling updates

## Database

SQLite (zero-config) with SQLAlchemy ORM. Tables:
- `fares`: Raw fare quotes with base fare / tax separation
- `indices`: Computed daily index values
- `sector_weights`: DGCA corridor weights
