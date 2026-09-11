# SkyMetric - India Airfare Price Index System

Real-time airfare price index for Indian domestic corridors, weighted by DGCA passenger traffic data.

## Problem Statement

Development of a Real-time Airfare Price Index for India through Automated Web Scraping of Airline and Online Travel Aggregator Portals for Augmentation of the Consumer Price Index (CPI).

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- npm or pnpm

### Backend Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium

# Initialize database with 30 days of seed data
python -m skymetric.main seed --days 30

# Start API server (runs on http://localhost:8000)
python -m skymetric.main serve --port 8000
```

### Frontend Setup
```bash
cd skymetric-frontend
npm install
npm run dev
```

Dashboard available at http://localhost:3000

## Architecture

```
skymetric/
├── scraper/              # Web scraping engine (Playwright + stealth)
│   ├── playwright_scraper.py   # Live scraper (10 sources)
│   └── mock_scraper.py         # Synthetic data generator
├── pipeline/             # ETL: cleaning, outlier removal, normalization
├── index_engine/         # Jevons/Laspeyres/Chain-Laspeyres calculation
├── api/                  # FastAPI REST endpoints
├── models/               # SQLAlchemy ORM (fares, indices, weights)
├── data/                 # DGCA weights, benchmark data, seed generator
├── config/               # Pydantic settings
└── tests/                # 45 pytest test cases
```

## Scraping Engine

### Sources (10 total)
| Source | Type | Method |
|--------|------|--------|
| IndiGo | Airline | Dedicated selector |
| Air India | Airline | Generic OTA |
| Air India Express | Airline | Generic OTA |
| Akasa Air | Airline | Generic OTA |
| SpiceJet | Airline | Generic OTA |
| MakeMyTrip | OTA | Dedicated selector |
| Yatra | OTA | Generic OTA |
| EaseMyTrip | OTA | Generic OTA |
| Cleartrip | OTA | Dedicated selector |
| Ixigo | OTA | Dedicated selector |
| Goibibo | OTA | Dedicated selector |

### Anti-Bot Measures
- Playwright headless Chromium
- playwright-stealth integration (fingerprint spoofing)
- User-Agent rotation (4 browser profiles)
- Rate limiting: 2-3 seconds between requests
- Exponential backoff: 3 retries with 1s/2s/4s delays
- navigator.webdriver override
- Viewport + locale + timezone spoofing

## Data Pipeline

### Cleaning Steps
1. **Validation**: Reject records with missing origin/destination or zero/negative fares
2. **Deduplication**: Composite key (origin, destination, carrier, flight_number, advance_window, departure_time) — keeps latest
3. **Outlier Removal**: Z-score > 3.0 threshold

### Fare Decomposition
| Component | Percentage | Description |
|-----------|------------|-------------|
| Base Fare | 70% | Airline base price |
| Taxes & Fees | 12% + variable | GST, airport fees |
| UDF | 8% | User Development Fee |
| Convenience | 10% | OTA convenience charge |

## Index Methodology

### Formulas
- **Jevons Index**: `(Π(p1/p0))^(1/n)` — geometric mean of price ratios
- **Laspeyres Index**: `Σ(p1·q0) / Σ(p0·q0)` — DGCA passenger-weighted arithmetic mean
- **Chain-Laspeyres**: Period-to-period linking for rolling updates

### Corridors (10 routes, DGCA-weighted)
| Route | Weight | Passengers | Classification |
|-------|--------|------------|----------------|
| DEL-BOM | 18.4% | 18.4M | Metro Trunk |
| DEL-BLR | 14.2% | 14.2M | Metro Trunk |
| BOM-BLR | 12.1% | 12.1M | Metro Trunk |
| DEL-CCU | 10.5% | 10.5M | Metro Trunk |
| DEL-HYD | 8.3% | 8.3M | Metro Trunk |
| BOM-MAA | 6.7% | 6.7M | Metro Trunk |
| BLR-HYD | 5.8% | 5.8M | Metro Trunk |
| DEL-MAA | 5.2% | 5.2M | Metro Trunk |
| DEL-IXS | 5.8% | 5.8M | Regional Thin |
| DEL-DHM | 3.0% | 3.0M | Regional Thin |

### Advance Windows
| Window | Multiplier | Description |
|--------|------------|-------------|
| T+1 | 1.45x | Last-minute booking |
| T+7 | 1.18x | Short-horizon |
| T+15 | 1.00x | Anchor (base) |
| T+30 | 0.88x | Consumer baseline |
| T+45 | 0.82x | Early bird |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/health` | GET | Health check + scheduler status |
| `/api/v1/index/daily` | GET | National SkyMetric index |
| `/api/v1/index/sectors` | GET | Per-corridor index breakdown |
| `/api/v1/routes/heatmap` | GET | Sector x time heatmap matrix |
| `/api/v1/routes/carriers` | GET | Carrier market share data |
| `/api/v1/elasticity/` | GET | Advance-purchase elasticity curves |
| `/api/v1/backtest/compare` | GET | SkyMetric vs DGCA benchmark (30-day) |
| `/api/v1/scraper/run` | POST | Trigger scraping job |
| `/api/v1/scraper/status` | GET | Scraper status + job history |

### Back-Test Response
```json
{
  "dates": ["2026-08-13", ...],
  "skymetric_index": [5256.88, ...],
  "dgca_benchmark": [5416.66, ...],
  "mape": 3.89,
  "rmse": 257.40,
  "days_compared": 30
}
```

## Dashboard Pages

| Page | Description |
|------|-------------|
| `/` | National index, KPIs, fare breakdown, day-of-week patterns, back-test chart |
| `/heatmap` | Sector x date matrix with origin/destination filters |
| `/elasticity` | Lead-time curves (T+1 to T+45) per corridor |
| `/carriers` | Carrier market share comparison |
| `/api-explorer` | Swagger UI for API testing |

## Testing

```bash
# Run all 45 tests
python -m pytest skymetric/tests/ -v

# Run specific test suite
python -m pytest skymetric/tests/test_api.py -v
python -m pytest skymetric/tests/test_index.py -v
python -m pytest skymetric/tests/test_pipeline.py -v
python -m pytest skymetric/tests/test_scraper.py -v
```

## Scheduled Extraction

APScheduler runs daily at 06:00 AM IST when the backend server is active. The scheduler:
- Generates fare data for all 10 corridors x 6 carriers x 5 advance windows
- Stores results in SQLite database
- Logs job status for monitoring

## Deployment

### Backend (Render.com / Railway / VPS)
```bash
pip install -r requirements.txt
playwright install chromium
python -m skymetric.main seed --days 30
python -m uvicorn skymetric.api.main:app --host 0.0.0.0 --port 8000
```

### Frontend (Vercel)
```bash
cd skymetric-frontend
npm run build
# Deploy to Vercel
```

### Docker
```bash
docker-compose up
```

## License

Internal use — hackathon prototype.
