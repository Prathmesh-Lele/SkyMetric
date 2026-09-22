# SkyMetric — India Airfare Price Index

Real-time airfare price index system for Indian domestic corridors. Computes sector-level and national indices from live flight fare data using established econometric methodologies.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (Next.js 16)                │
│  Dashboard · Heatmap · Elasticity · Carriers ·          │
│  Analytics · API Explorer                               │
└───────────────────────┬─────────────────────────────────┘
                        │ REST API (JSON)
┌───────────────────────▼─────────────────────────────────┐
│                  Backend (FastAPI)                       │
│  22 endpoints · 7 routers · OpenAPI/Swagger docs        │
├─────────────────────────────────────────────────────────┤
│  Index Engine          │  Pipeline                      │
│  • Jevons              │  • Validate                    │
│  • Laspeyres           │  • Deduplicate                 │
│  • Paasche             │  • Outlier removal (Z-score)   │
│  • Fisher              │  • Normalize                   │
│  • Tornqvist           │                                │
│  • Chain-Laspeyres     │                                │
├─────────────────────────────────────────────────────────┤
│  Scraper (3-tier fallback)                              │
│  Tier 1: fli (Google Flights, no API key)               │
│  Tier 2: SerpApi (Google Flights, free tier)            │
│  Tier 3: MockScraper (synthetic, always available)      │
├─────────────────────────────────────────────────────────┤
│  Storage: SQLite (SQLAlchemy ORM)                       │
│  Scheduler: APScheduler (daily cron at 06:00 IST)        │
└─────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- (Optional) SerpApi key from https://serpapi.com

### Backend

```bash
cd skymetric
pip install -r requirements.txt
cp .env.example .env   # edit SERPAPI_KEY if you have one
uvicorn skymetric.api.main:app --reload --port 8000
```

### Frontend

```bash
cd skymetric-frontend
npm install
npm run dev
```

Open http://localhost:3000

### Docker

```bash
docker-compose up -d
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/index/daily` | National index for a date |
| GET | `/api/v1/index/weekly` | Weekly average index |
| GET | `/api/v1/index/monthly` | Monthly average index |
| GET | `/api/v1/index/sectors` | Per-corridor index breakdown |
| GET | `/api/v1/routes/heatmap` | Sector × time fare matrix |
| GET | `/api/v1/routes/carriers` | Carrier market share |
| GET | `/api/v1/elasticity/` | Advance-purchase price curves |
| GET | `/api/v1/backtest/compare` | SkyMetric vs DGCA benchmark |
| GET | `/api/v1/cpi/` | CPI comparison (General/Transport/Air) |
| GET | `/api/v1/analytics/superlative` | Fisher/Paasche/Tornqvist indices |
| GET | `/api/v1/analytics/anomalies` | Outlier detection (Z-score) |
| GET | `/api/v1/analytics/data-trust` | Data quality scorecard |
| GET | `/api/v1/analytics/export/csv` | CSV export |
| GET | `/api/v1/scraper/status` | Scraper metrics |
| POST | `/api/v1/scraper/run` | Trigger single corridor scrape |
| POST | `/api/v1/scraper/run-all` | Full 10-corridor scrape |
| POST | `/api/v1/scraper/daemon/start` | Start continuous scraping |
| POST | `/api/v1/scraper/daemon/stop` | Stop daemon |

Full interactive docs: http://localhost:8000/docs

## Data Sources

| Tier | Source | API Key? | Quota |
|------|--------|----------|-------|
| 1 | fli (Google Flights) | No | Unlimited |
| 2 | SerpApi (Google Flights) | Yes (free) | 100-250/month |
| 3 | MockScraper | No | Unlimited |

## Corridors (10)

Weighted by DGCA 2023-24 passenger traffic:

| Route | Classification |
|-------|---------------|
| DEL-BOM | Metro trunk |
| DEL-BLR | Metro trunk |
| BOM-BLR | Metro trunk |
| DEL-CCU | Metro trunk |
| DEL-HYD | Metro trunk |
| BOM-MAA | Metro trunk |
| BLR-HYD | Metro trunk |
| DEL-MAA | Metro trunk |
| DEL-IXS | Regional thin |
| DEL-DHM | Regional thin |

## Advance-Purchase Windows

| Window | Label | Typical Multiplier |
|--------|-------|--------------------|
| T+1 | Emergency | 1.45× |
| T+7 | Short-notice | 1.18× |
| T+15 | Anchor | 1.00× |
| T+30 | Early booking | 0.88× |
| T+45 | Advance saver | 0.82× |

## Index Methodologies

- **Jevons** — log-mean of price relatives (primary)
- **Laspeyres** — base-period quantity weights
- **Paasche** — current-period quantity weights
- **Fisher** — geometric mean of Laspeyres × Paasche
- **Tornqvist** — share-weighted geometric mean
- **Chain-Laspeyres** — period-by-period chaining

## Testing

```bash
cd skymetric
$env:PYTHONPATH = ".."
python -m pytest tests/ -v
```

45 tests covering formulas, pipeline, scraper, and API endpoints.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS, Recharts |
| Backend | Python 3.11, FastAPI, SQLAlchemy, APScheduler |
| Data | SQLite (dev), PostgreSQL (production planned) |
| Scraping | fli, SerpApi, Playwright (optional) |
| Testing | pytest |

## Environment Variables

See `.env.example`:

```env
DATABASE_URL=sqlite:///skymetric.db
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
SERPAPI_KEY=your_key_here
SCRAPER_MODE=mock
```

## License

MIT
