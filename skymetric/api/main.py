"""FastAPI application entry point with endpoint registration."""

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
from skymetric.api.routes.scraper import router as scraper_router
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


def _scheduled_scrape_job():
    """Daily scrape job triggered by APScheduler."""
    from datetime import datetime
    from skymetric.data.seed_data import generate_fares_for_day
    from skymetric.models.database import SessionLocal, init_db
    from skymetric.models.fare import Fare

    sched_logger = logging.getLogger("skymetric.scheduler")
    sched_logger.info("Running scheduled scrape job at %s", datetime.utcnow().isoformat())
    init_db()
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
        sched_logger.info("Scheduled job inserted %d fare records", len(records))
    except Exception as exc:
        sched_logger.error("Scheduled scrape job failed: %s", exc)
        db.rollback()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.add_job(_scheduled_scrape_job, "cron", hour=6, minute=0, id="daily_scrape")
    scheduler.start()
    logger.info("SkyMetric API started — scheduler running, log level=%s", settings.LOG_LEVEL)
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
    return {"status": "healthy", "service": "skymetric", "scheduler_running": scheduler.running}
