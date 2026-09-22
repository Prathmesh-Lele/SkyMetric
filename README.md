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
│  Scraper (2-tier fallback)                             │
│  Tier 1: SerpApi (Google Flights, free tier)            │
│  Tier 2: MockScraper (synthetic, always available)      │
├─────────────────────────────────────────────────────────┤
│  Storage: SQLite (SQLAlchemy ORM)                       │
│  Scheduler: APScheduler (daily cron at 06:00 server time)│
└─────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- (Optional) SerpApi key from https://serpapi.com

### Backend

Run all commands from the **repo root** (`videos/`):

```bash
pip install -r requirements.txt
cp skymetric/.env.example skymetric/.env   # edit SERPAPI_KEY if you have one
uvicorn skymetric.api.main:app --reload --port 8000
```

Optional: seed the database with 30 days of fare data first:

```bash
python -m skymetric.main seed
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
| GET | `/api/v1/cpi/air-transport` | CPI Air Transport series |
| GET | `/api/v1/cpi/general` | CPI General series |
| GET | `/api/v1/analytics/superlative` | Fisher/Paasche/Tornqvist indices |
| GET | `/api/v1/analytics/anomalies` | Outlier detection (Z-score) |
| GET | `/api/v1/analytics/data-trust` | Data quality scorecard |
| GET | `/api/v1/analytics/export/csv` | CSV export |
| GET | `/api/v1/scraper/status` | Scraper metrics |
| GET | `/api/v1/scraper/health` | Scraper health check |
| POST | `/api/v1/scraper/run` | Trigger single corridor scrape |
| POST | `/api/v1/scraper/run-all` | Full 10-corridor scrape |
| POST | `/api/v1/scraper/daemon/start` | Start continuous scraping |
| POST | `/api/v1/scraper/daemon/stop` | Stop daemon |

Full interactive docs: http://localhost:8000/docs

## Data Sources

| Tier | Source | API Key? | Quota |
|------|--------|----------|-------|
| 1 | SerpApi (Google Flights) | Yes (free tier) | 100–250/month |
| 2 | MockScraper (synthetic) | No | Unlimited |

Set `SERPAPI_KEY` in `skymetric/.env` to enable live Google Flights data. Without a key, the system falls back to the deterministic MockScraper so the prototype always runs.

## Future Work

- **PostgreSQL** for multi-writer production workloads (SQLite today)
- **Alembic migrations** for schema versioning
- **More corridors** — expand beyond 10 to cover all DGCA city-pairs
- **Hosted deployment** (Vercel + Railway/Render) with CI/CD
- **Official DGCA / MoSPI live feeds** as primary data sources
- **Per-user API keys** and rate limiting on the public API
- **Alerting** — email/Slack notifications on anomaly spikes

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

Run from the repo root (PowerShell):

```powershell
$env:PYTHONPATH = "."
python -m pytest skymetric/tests/ -v
```

Or from `skymetric/`:

```bash
cd skymetric
PYTHONPATH=.. python -m pytest tests/ -v
```

45 tests covering formulas, pipeline, scraper, and API endpoints. Tests use an isolated in-memory SQLite database and do not touch your real data.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS, Recharts |
| Backend | Python 3.11+, FastAPI, SQLAlchemy, APScheduler |
| Data | SQLite (dev), PostgreSQL (production planned) |
| Scraping | SerpApi, Playwright (optional) |
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
