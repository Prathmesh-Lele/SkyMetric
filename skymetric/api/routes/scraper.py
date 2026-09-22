"""Scraper control API endpoints."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException

from skymetric.scraper.playwright_scraper import scraper
from skymetric.scraper.flight_api_client import flight_api_client
from skymetric.data.dgca_weights import CORRIDORS, ADVANCE_WINDOWS
from skymetric.data.seed_data import generate_30_day_seed

logger = logging.getLogger(__name__)
router = APIRouter()

SCRAPER_API_KEY = "skymetric-demo-key"

_daemon_task: Optional[asyncio.Task] = None
_daemon_running = False


def _verify_api_key(x_api_key: Optional[str] = Header(None)):
    """Simple API key auth for mutating scraper routes."""
    if x_api_key != SCRAPER_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid or missing X-API-Key header")


@router.get("/status")
def get_scraper_status():
    """Get current scraper status and metrics."""
    return scraper.get_status()


@router.post("/run")
async def run_scraper(
    background_tasks: BackgroundTasks,
    origin: Optional[str] = None,
    destination: Optional[str] = None,
    date: Optional[str] = None,
    x_api_key: Optional[str] = Header(None),
):
    """Trigger an ad-hoc scraper run.

    Uses 3-tier fallback: fli -> SerpApi -> MockScraper.
    Saves fetched fares to the database.
    Requires X-API-Key header.
    """
    _verify_api_key(x_api_key)

    if scraper.status.is_running:
        raise HTTPException(status_code=409, detail="Scraper is already running")

    origin_val = origin or "DEL"
    dest_val = destination or "BOM"
    date_str = date or datetime.now().strftime("%Y-%m-%d")

    async def _run():
        from skymetric.models.database import SessionLocal, init_db
        from skymetric.models.fare import Fare

        scraper.status.is_running = True
        scraper.status.total_jobs += 1

        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            dep_datetime = datetime.combine(target_date, datetime.min.time())

            # 3-tier fallback: fli -> SerpApi -> MockScraper
            fares, source = await flight_api_client.search_flights(
                origin_val, dest_val, dep_datetime, 15
            )
            logger.info(f"Scraper run for {origin_val}-{dest_val}: source={source}, {len(fares)} fares")

            if fares:
                init_db()
                db = SessionLocal()
                try:
                    for r in fares:
                        fare = Fare(
                            timestamp=r.get("timestamp", datetime.utcnow()),
                            origin=r["origin"],
                            destination=r["destination"],
                            carrier=r["carrier"],
                            flight_number=r["flight_number"],
                            departure_time=r["departure_time"],
                            advance_window_days=r["advance_window_days"],
                            fare_class=r.get("fare_class", "economy"),
                            base_fare=r["base_fare"],
                            taxes_and_fees=r["taxes_and_fees"],
                            udf=r.get("udf"),
                            convenience_charge=r.get("convenience_charge"),
                            total_fare=r["total_fare"],
                            source_platform=r.get("source_platform", "mock"),
                        )
                        db.add(fare)
                    db.commit()
                finally:
                    db.close()

            scraper.status.quotes_collected += len(fares)
            scraper.status.sources_checked += 1
            scraper.status.completed_jobs += 1

        except Exception as exc:
            logger.error(f"Scraper run failed: {exc}", exc_info=True)
            scraper.status.failed_jobs += 1
        finally:
            scraper.status.is_running = False
            scraper.status.last_run = datetime.now()

    background_tasks.add_task(_run)

    return {
        "message": "Scraper run triggered",
        "origin": origin_val,
        "destination": dest_val,
        "date": date_str,
        "status": scraper.get_status(),
    }


@router.post("/run-all")
async def run_scraper_all(background_tasks: BackgroundTasks):
    """Run scraper across all 10 corridors × 5 advance windows = 50 jobs.

    Uses mock scraper for speed. Each corridor gets quotes for T+1, T+7, T+15, T+30, T+45.
    """
    if scraper.status.is_running:
        return {"error": "Scraper is already running", "status": scraper.get_status()}

    async def _run_all():
        from datetime import date as date_type
        from skymetric.models.database import SessionLocal, init_db
        from skymetric.models.fare import Fare
        from skymetric.models.index_value import IndexValue
        from skymetric.scraper.mock_scraper import MockScraper
        from skymetric.index_engine.calculator import compute_sector_index, compute_national_index
        from skymetric.pipeline.cleaner import clean_pipeline
        from skymetric.pipeline.normalizer import normalize_records

        scraper.status.is_running = True
        total_fares = []

        # Check if Playwright is available
        use_playwright = False
        try:
            from playwright.async_api import async_playwright
            pw = await async_playwright().start()
            browser = await pw.chromium.launch(headless=True)
            await browser.close()
            await pw.stop()
            use_playwright = True
            logger.info("Playwright available — using live scraper for /run-all")
        except Exception:
            logger.info("Playwright not available — falling back to MockScraper for /run-all")

        mock = MockScraper() if not use_playwright else None

        try:
            init_db()
            db = SessionLocal()
            try:
                today = date_type.today()
                for corridor in CORRIDORS:
                    origin = corridor["origin"]
                    dest = corridor["destination"]
                    for advance in ADVANCE_WINDOWS:
                        target_date = today + timedelta(days=advance)
                        dep_datetime = datetime.combine(target_date, datetime.min.time())

                        if use_playwright:
                            fares = await scraper.scrape(origin, dest, dep_datetime, advance)
                        else:
                            fares = mock.scrape(origin, dest, dep_datetime, advance)

                        for r in fares:
                            fare = Fare(
                                timestamp=r.get("timestamp", datetime.utcnow()),
                                origin=r["origin"],
                                destination=r["destination"],
                                carrier=r["carrier"],
                                flight_number=r["flight_number"],
                                departure_time=r["departure_time"],
                                advance_window_days=r["advance_window_days"],
                                fare_class=r.get("fare_class", "economy"),
                                base_fare=r["base_fare"],
                                taxes_and_fees=r["taxes_and_fees"],
                                udf=r.get("udf"),
                                convenience_charge=r.get("convenience_charge"),
                                total_fare=r["total_fare"],
                                source_platform=r.get("source_platform", "mock"),
                            )
                            db.add(fare)
                        total_fares.extend(fares)
                db.commit()

                if total_fares:
                    today_date = date_type.today()
                    base_date = today_date - timedelta(days=30)

                    records_clean = clean_pipeline(normalize_records(total_fares))
                    base_records_all = generate_30_day_seed(
                        end_date=datetime.combine(today_date, datetime.min.time()), days=31
                    )
                    base_records = [r for r in base_records_all if r["timestamp"].date() == base_date]
                    base_clean = clean_pipeline(normalize_records(base_records)) if base_records else records_clean

                    sector_indices = {}
                    corridors_seen = set()
                    for r in records_clean:
                        corridors_seen.add((r["origin"], r["destination"]))

                    for origin, dest in corridors_seen:
                        curr = [r for r in records_clean if r["origin"] == origin and r["destination"] == dest and r["advance_window_days"] == 15]
                        base = [r for r in base_clean if r["origin"] == origin and r["destination"] == dest and r["advance_window_days"] == 15]
                        if curr and base:
                            sector_indices[f"{origin}-{dest}"] = compute_sector_index(curr, base)

                    if sector_indices:
                        national = compute_national_index(sector_indices)
                        idx = IndexValue(
                            date=today_date,
                            origin=None,
                            destination=None,
                            advance_window=15,
                            index_value=national,
                            base_value=100.0,
                            calculation_method="jevons",
                        )
                        db.add(idx)
                        db.commit()

            finally:
                db.close()

            scraper.status.quotes_collected += len(total_fares)
            scraper.status.completed_jobs += 1

        except Exception:
            scraper.status.failed_jobs += 1
        finally:
            scraper.status.is_running = False
            scraper.status.last_run = datetime.now()

    background_tasks.add_task(_run_all)

    return {
        "message": "Full scraper run triggered",
        "corridors": len(CORRIDORS),
        "advance_windows": ADVANCE_WINDOWS,
        "total_jobs": len(CORRIDORS) * len(ADVANCE_WINDOWS),
        "status": scraper.get_status(),
    }


@router.get("/health")
def scraper_health():
    """Check scraper health."""
    return {
        "healthy": scraper.health_check(),
        "is_running": scraper.status.is_running,
        "last_run": scraper.status.last_run.isoformat() if scraper.status.last_run else None,
    }


@router.post("/daemon/start")
async def start_daemon(background_tasks: BackgroundTasks, interval_minutes: int = 30):
    """Start continuous scraping daemon.

    Runs run-all every N minutes in the background.
    """
    global _daemon_task, _daemon_running

    if _daemon_running:
        return {"error": "Daemon already running", "interval_minutes": interval_minutes}

    _daemon_running = True

    async def _daemon_loop():
        global _daemon_running
        while _daemon_running:
            try:
                from datetime import date as date_type
                from skymetric.models.database import SessionLocal, init_db
                from skymetric.models.fare import Fare
                from skymetric.scraper.mock_scraper import MockScraper

                mock = MockScraper()
                init_db()
                db = SessionLocal()
                try:
                    today = date_type.today()
                    for corridor in CORRIDORS:
                        for advance in ADVANCE_WINDOWS:
                            target_date = today + timedelta(days=advance)
                            dep_datetime = datetime.combine(target_date, datetime.min.time())
                            fares = mock.scrape(corridor["origin"], corridor["destination"], dep_datetime, advance)
                            for r in fares:
                                fare = Fare(
                                    timestamp=r.get("timestamp", datetime.utcnow()),
                                    origin=r["origin"],
                                    destination=r["destination"],
                                    carrier=r["carrier"],
                                    flight_number=r["flight_number"],
                                    departure_time=r["departure_time"],
                                    advance_window_days=r["advance_window_days"],
                                    fare_class=r.get("fare_class", "economy"),
                                    base_fare=r["base_fare"],
                                    taxes_and_fees=r["taxes_and_fees"],
                                    udf=r.get("udf"),
                                    convenience_charge=r.get("convenience_charge"),
                                    total_fare=r["total_fare"],
                                    source_platform=r.get("source_platform", "mock"),
                                )
                                db.add(fare)
                    db.commit()
                finally:
                    db.close()

                scraper.status.last_run = datetime.now()
                scraper.status.completed_jobs += 1

            except Exception:
                scraper.status.failed_jobs += 1

            await asyncio.sleep(interval_minutes * 60)

    _daemon_task = asyncio.create_task(_daemon_loop())

    return {
        "message": "Daemon started",
        "interval_minutes": interval_minutes,
        "corridors": len(CORRIDORS),
        "advance_windows": ADVANCE_WINDOWS,
    }


@router.post("/daemon/stop")
async def stop_daemon():
    """Stop the continuous scraping daemon."""
    global _daemon_task, _daemon_running

    if not _daemon_running:
        return {"error": "Daemon not running"}

    _daemon_running = False
    if _daemon_task:
        _daemon_task.cancel()
        _daemon_task = None

    return {"message": "Daemon stopped"}
