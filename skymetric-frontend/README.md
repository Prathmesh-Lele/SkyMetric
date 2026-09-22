# SkyMetric Frontend

Next.js 16 / React 19 dashboard for the SkyMetric airfare price index.

## Run

```bash
npm install
npm run dev
```

Open http://localhost:3000. Requires the backend on http://localhost:8000 (see repo root README).

## Pages

| Route | Description |
|-------|-------------|
| `/` | National index dashboard (KPIs, chart, windows, sectors) |
| `/heatmap` | Sector × date fare heatmap with filters + CSV export |
| `/elasticity` | Lead-time price curves by corridor (modeled) |
| `/carriers` | Market share and fare comparison |
| `/analytics` | Superlatives, anomalies, data-trust scorecard |
| `/backtest` | SkyMetric vs DGCA benchmark + CPI reference |
| `/scraper` | Scraper status and manual run controls |
| `/api-explorer` | Interactive API reference |

## Env

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Build

```bash
npm run build
```
