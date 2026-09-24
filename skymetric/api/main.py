"""FastAPI application entry point with endpoint registration."""

import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from apscheduler.schedulers.background import BackgroundScheduler

from skymetric.config.settings import settings
from skymetric.api.routes.index import router as index_router
from skymetric.api.routes.heatmap import router as heatmap_router
from skymetric.api.routes.elasticity import router as elasticity_router
from skymetric.api.routes.scraper import router as scraper_router, scrape_trunk_live
from skymetric.api.routes.backtest import router as backtest_router
from skymetric.api.routes.cpi import router as cpi_router
from skymetric.api.routes.analytics import router as analytics_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def _run_async(coro):
    """Run an async coroutine from a sync APScheduler job."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Called from a thread with a loop — use a fresh loop
            new_loop = asyncio.new_event_loop()
            try:
                return new_loop.run_until_complete(coro)
            finally:
                new_loop.close()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


def _scheduled_scrape_job():
    """Daily live scrape (06:00): SerpApi trunk corridors + mock backfill."""
    from datetime import datetime
    from skymetric.data.seed_data import generate_fares_for_day
    from skymetric.models.database import SessionLocal, init_db
    from skymetric.models.fare import Fare

    sched_logger = logging.getLogger("skymetric.scheduler")
    sched_logger.info("Running scheduled scrape job at %s", datetime.utcnow().isoformat())
    init_db()

    # 1) Live SerpApi fetch for trunk corridors (3 calls)
    try:
        result = _run_async(scrape_trunk_live())
        sched_logger.info("Live trunk scrape: %s", result)
    except Exception as exc:
        sched_logger.error("Live trunk scrape failed: %s", exc)

    # 2) Synthetic backfill for full 10-corridor × 5-window coverage
    db = SessionLocal()
    try:
        records = generate_fares_for_day(datetime.utcnow(), include_outliers=False)
        for r in records:
            fare = Fare(
                timestamp=r["timestamp"],
                origin=r["origin"],
                destination=r["destination"],
                carrier=r["carrier"],
                flight_number=r["flight_number"],
                departure_time=r["departure_time"],
                advance_window_days=r["advance_window_days"],
                fare_class=r["fare_class"],
                base_fare=r["base_fare"],
                taxes_and_fees=r["taxes_and_fees"],
                udf=r.get("udf"),
                convenience_charge=r.get("convenience_charge"),
                total_fare=r["total_fare"],
                source_platform=r["source_platform"],
            )
            db.add(fare)
        db.commit()
        sched_logger.info("Backfill inserted %d synthetic fare records", len(records))
    except Exception as exc:
        sched_logger.error("Scheduled backfill failed: %s", exc)
        db.rollback()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.add_job(_scheduled_scrape_job, "cron", hour=6, minute=0, id="daily_scrape")
    scheduler.start()

    live = bool(settings.SERPAPI_KEY)
    logger.info(
        "SkyMetric API started — scheduler running, live=%s (SERPAPI_KEY %s), log level=%s",
        live,
        "set" if live else "missing",
        settings.LOG_LEVEL,
    )

    # Boot-time live refresh: only if no recent serpapi rows (quota guard).
    # force=False → skips when live data already exists within LIVE_MIN_INTERVAL_HOURS.
    if live:
        try:
            result = await scrape_trunk_live(force=False)
            logger.info(f"Boot live refresh: {result}")
        except Exception as exc:
            logger.warning(f"Boot live refresh failed: {exc}")

    yield
    scheduler.shutdown()


app = FastAPI(
    title="SkyMetric - India Airfare Price Index",
    description="Real-time airfare price index for Indian domestic corridors. "
    "Provides sector-level and national indices computed from live flight fare data "
    "using established econometric methodologies (Jevons, Laspeyres, Fisher, Tornqvist).",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — specific origins instead of wildcard + credentials
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://skymetric.vercel.app",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler — return proper HTTP status codes
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "path": request.url.path},
    )


app.include_router(index_router, prefix="/api/v1/index", tags=["Index"])
app.include_router(heatmap_router, prefix="/api/v1/routes", tags=["Heatmap"])
app.include_router(elasticity_router, prefix="/api/v1/elasticity", tags=["Elasticity"])
app.include_router(scraper_router, prefix="/api/v1/scraper", tags=["Scraper"])
app.include_router(backtest_router, prefix="/api/v1/backtest", tags=["Backtest"])
app.include_router(cpi_router, prefix="/api/v1/cpi", tags=["CPI"])
app.include_router(analytics_router, prefix="/api/v1/analytics", tags=["Analytics"])


@app.get("/api/v1/health", tags=["Health"])
def health_check():
    from skymetric.scraper.flight_api_client import flight_api_client

    next_scrape = None
    try:
        if scheduler.running:
            job = scheduler.get_job("daily_scrape")
            if job is not None and job.next_run_time is not None:
                next_scrape = job.next_run_time.isoformat()
    except Exception:
        next_scrape = None

    last_update = None
    try:
        from sqlalchemy import func
        from skymetric.models.database import SessionLocal, init_db
        from skymetric.models.fare import Fare

        init_db()
        db = SessionLocal()
        try:
            ts = db.query(func.max(Fare.timestamp)).scalar()
            last_update = ts.isoformat() if ts else None
        finally:
            db.close()
    except Exception:
        last_update = None

    return {
        "status": "healthy",
        "service": "skymetric",
        "scheduler_running": scheduler.running,
        "live_data": flight_api_client.live_enabled,
        "source": "serpapi" if flight_api_client.live_enabled else "mock",
        "last_data_update": last_update,
        "next_scheduled_scrape": next_scrape,
        "refresh_interval_seconds": 60,
    }
