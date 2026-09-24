"""Scraper control API endpoints."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException
from sqlalchemy import func

from skymetric.scraper.playwright_scraper import scraper
from skymetric.scraper.flight_api_client import flight_api_client
from skymetric.data.dgca_weights import CORRIDORS, ADVANCE_WINDOWS
from skymetric.data.seed_data import generate_30_day_seed

logger = logging.getLogger(__name__)
router = APIRouter()

SCRAPER_API_KEY = "skymetric-demo-key"

_daemon_task: Optional[asyncio.Task] = None
_daemon_running = False

# Trunk corridors for quota-friendly live daily scrapes (3 SerpApi calls/day)
LIVE_DAILY_CORRIDOR_KEYS = {"DEL-BOM", "DEL-BLR", "BOM-BLR"}

# Skip SerpApi when fresher live rows already exist (protect free-tier quota)
LIVE_MIN_INTERVAL_HOURS = 12
LIVE_REFRESH_COOLDOWN_MIN = 10
_last_live_refresh_at: Optional[datetime] = None


def _verify_api_key(x_api_key: Optional[str] = Header(None)):
    """API key auth for mutating scraper routes. Returns 401 when missing, 403 when wrong."""
    if x_api_key is None:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")
    if x_api_key != SCRAPER_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid X-API-Key")


def _recent_live_fare_count(hours: float = LIVE_MIN_INTERVAL_HOURS) -> int:
    """Count serpapi rows with timestamp within the last `hours` (quota guard)."""
    from skymetric.models.database import SessionLocal, init_db
    from skymetric.models.fare import Fare

    init_db()
    db = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return (
            db.query(Fare)
            .filter(
                Fare.source_platform == "serpapi",
                Fare.timestamp >= cutoff,
            )
            .count()
        )
    finally:
        db.close()


def _to_dt(value, default=None):
    """Coerce str/datetime into datetime for SQLite columns."""
    if isinstance(value, datetime):
        return value
    if value is None:
        return default or datetime.utcnow()
    if isinstance(value, str) and value:
        for fmt in (
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
        ):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError:
            pass
    return default or datetime.utcnow()


def _insert_fares(db, fares) -> int:
    from skymetric.models.fare import Fare

    for r in fares:
        fare = Fare(
            timestamp=_to_dt(r.get("timestamp")),
            origin=r["origin"],
            destination=r["destination"],
            carrier=r["carrier"],
            flight_number=r["flight_number"],
            departure_time=_to_dt(r.get("departure_time")),
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
    return len(fares)


def _source_breakdown() -> dict:
    """Count fare rows grouped by source_platform."""
    from skymetric.models.database import SessionLocal, init_db
    from skymetric.models.fare import Fare

    init_db()
    db = SessionLocal()
    try:
        rows = (
            db.query(Fare.source_platform, func.count(Fare.id))
            .group_by(Fare.source_platform)
            .all()
        )
        return {src: cnt for src, cnt in rows}
    finally:
        db.close()


def _next_scheduled_scrape() -> Optional[str]:
    """ISO timestamp of the next 06:00 daily scrape, or None if scheduler is down."""
    try:
        from skymetric.api.main import scheduler

        if not scheduler.running:
            return None
        job = scheduler.get_job("daily_scrape")
        if job is None or job.next_run_time is None:
            return None
        return job.next_run_time.isoformat()
    except Exception:
        return None


def _last_data_update() -> Optional[str]:
    """ISO timestamp of the newest fare row (when National SkyMetric last changed)."""
    from skymetric.models.database import SessionLocal, init_db
    from skymetric.models.fare import Fare

    init_db()
    db = SessionLocal()
    try:
        ts = db.query(func.max(Fare.timestamp)).scalar()
        return ts.isoformat() if ts else None
    finally:
        db.close()


@router.get("/status")
def get_scraper_status():
    """Get current scraper status, metrics, and live-data source breakdown."""
    status = scraper.get_status()
    breakdown = _source_breakdown()
    status["source_breakdown"] = breakdown
    status["live_enabled"] = flight_api_client.live_enabled
    status["live_source"] = "serpapi" if flight_api_client.live_enabled else None
    status["last_fetch_source"] = flight_api_client.get_last_source()
    status["total_fares"] = sum(breakdown.values())
    status["live_fares"] = breakdown.get("serpapi", 0)
    status["last_data_update"] = _last_data_update()
    status["next_scheduled_scrape"] = _next_scheduled_scrape()
    return status


@router.get("/sources")
def get_sources():
    """Fare row counts by source_platform (serpapi / mock / seed_generator)."""
    breakdown = _source_breakdown()
    return {
        "breakdown": breakdown,
        "total": sum(breakdown.values()),
        "live": breakdown.get("serpapi", 0),
        "live_enabled": flight_api_client.live_enabled,
    }


@router.post("/run")
async def run_scraper(
    origin: Optional[str] = None,
    destination: Optional[str] = None,
    date: Optional[str] = None,
    advance_window: int = 15,
    x_api_key: Optional[str] = Header(None),
):
    """Fetch live fares for one corridor (SerpApi first, mock fallback).

    Runs inline so the response includes the actual source and row count.
    Requires X-API-Key header.
    """
    _verify_api_key(x_api_key)

    if scraper.status.is_running:
        raise HTTPException(status_code=409, detail="Scraper is already running")

    origin_val = (origin or "DEL").upper()
    dest_val = (destination or "BOM").upper()
    date_str = date or datetime.now().strftime("%Y-%m-%d")

    scraper.status.is_running = True
    scraper.status.total_jobs += 1

    try:
        from skymetric.models.database import SessionLocal, init_db

        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        dep_datetime = datetime.combine(target_date, datetime.min.time())

        # Quota guard: only spend SerpApi on trunk corridors (same 3 as daily live)
        corridor_key = f"{origin_val}-{dest_val}"
        prefer_live = corridor_key in LIVE_DAILY_CORRIDOR_KEYS
        fares, source = await flight_api_client.search_flights(
            origin_val, dest_val, dep_datetime, advance_window, prefer_live=prefer_live
        )
        logger.info(
            f"Scraper run {origin_val}-{dest_val}: source={source}, {len(fares)} fares"
        )

        inserted = 0
        if fares:
            init_db()
            db = SessionLocal()
            try:
                inserted = _insert_fares(db, fares)
                db.commit()
            finally:
                db.close()

        scraper.status.quotes_collected += len(fares)
        scraper.status.sources_checked += 1
        scraper.status.completed_jobs += 1
        scraper.status.last_run = datetime.now()

        return {
            "message": f"Fetched {len(fares)} fares from {source}",
            "origin": origin_val,
            "destination": dest_val,
            "date": date_str,
            "advance_window": advance_window,
            "source": source,
            "live": source == "serpapi",
            "fares_inserted": inserted,
            "sample_fares": [
                {
                    "carrier": f.get("carrier"),
                    "flight_number": f.get("flight_number"),
                    "total_fare": f.get("total_fare"),
                }
                for f in fares[:5]
            ],
            "status": scraper.get_status(),
        }
    except Exception as exc:
        logger.error(f"Scraper run failed: {exc}", exc_info=True)
        scraper.status.failed_jobs += 1
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        scraper.status.is_running = False


@router.post("/run-all")
async def run_scraper_all(
    background_tasks: BackgroundTasks,
    live: bool = True,
    x_api_key: Optional[str] = Header(None),
):
    """Run scraper across all 10 corridors × 5 advance windows.

    live=true (default): SerpApi for trunk corridors at every window when key
    is set; mock fills remaining jobs. live=false: mock only.
    Requires X-API-Key header.
    """
    _verify_api_key(x_api_key)

    if scraper.status.is_running:
        return {"error": "Scraper is already running", "status": scraper.get_status()}

    async def _run_all():
        from datetime import date as date_type
        from skymetric.models.database import SessionLocal, init_db

        scraper.status.is_running = True
        total_fares = []
        source_counts = {"serpapi": 0, "mock": 0}

        try:
            init_db()
            db = SessionLocal()
            try:
                today = date_type.today()
                for corridor in CORRIDORS:
                    origin = corridor["origin"]
                    dest = corridor["destination"]
                    corridor_key = f"{origin}-{dest}"
                    for advance in ADVANCE_WINDOWS:
                        target_date = today + timedelta(days=advance)
                        dep_datetime = datetime.combine(target_date, datetime.min.time())

                        # Live only trunk corridors at T+15 (3 calls max) to
                        # protect SerpApi free-tier quota; other jobs use mock.
                        prefer_live = (
                            live
                            and corridor_key in LIVE_DAILY_CORRIDOR_KEYS
                            and advance == 15
                        )
                        fares, source = await flight_api_client.search_flights(
                            origin, dest, dep_datetime, advance, prefer_live=prefer_live
                        )
                        source_counts[source] = source_counts.get(source, 0) + len(fares)
                        _insert_fares(db, fares)
                        total_fares.extend(fares)
                db.commit()

                if total_fares:
                    from skymetric.models.index_value import IndexValue
                    from skymetric.index_engine.calculator import (
                        compute_sector_index,
                        compute_national_index,
                    )
                    from skymetric.pipeline.cleaner import clean_pipeline
                    from skymetric.pipeline.normalizer import normalize_records

                    today_date = date_type.today()
                    base_date = today_date - timedelta(days=30)

                    records_clean = clean_pipeline(normalize_records(total_fares))
                    base_records_all = generate_30_day_seed(
                        end_date=datetime.combine(today_date, datetime.min.time()),
                        days=31,
                    )
                    base_records = [
                        r
                        for r in base_records_all
                        if r["timestamp"].date() == base_date
                    ]
                    base_clean = (
                        clean_pipeline(normalize_records(base_records))
                        if base_records
                        else records_clean
                    )

                    sector_indices = {}
                    corridors_seen = set()
                    for r in records_clean:
                        corridors_seen.add((r["origin"], r["destination"]))

                    for origin, dest in corridors_seen:
                        curr = [
                            r
                            for r in records_clean
                            if r["origin"] == origin
                            and r["destination"] == dest
                            and r["advance_window_days"] == 15
                        ]
                        base = [
                            r
                            for r in base_clean
                            if r["origin"] == origin
                            and r["destination"] == dest
                            and r["advance_window_days"] == 15
                        ]
                        if curr and base:
                            sector_indices[f"{origin}-{dest}"] = compute_sector_index(
                                curr, base
                            )

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
            logger.info(
                f"run-all finished: {len(total_fares)} fares, sources={source_counts}"
            )

        except Exception:
            logger.exception("run-all failed")
            scraper.status.failed_jobs += 1
        finally:
            scraper.status.is_running = False
            scraper.status.last_run = datetime.now()

    background_tasks.add_task(_run_all)

    return {
        "message": "Full scraper run triggered"
        + (" (live SerpApi on trunk corridors)" if live and flight_api_client.live_enabled else " (mock)"),
        "corridors": len(CORRIDORS),
        "advance_windows": ADVANCE_WINDOWS,
        "total_jobs": len(CORRIDORS) * len(ADVANCE_WINDOWS),
        "live": live and flight_api_client.live_enabled,
        "live_enabled": flight_api_client.live_enabled,
        "status": scraper.get_status(),
    }


@router.get("/health")
def scraper_health():
    """Check scraper health."""
    return {
        "healthy": scraper.health_check(),
        "is_running": scraper.status.is_running,
        "last_run": scraper.status.last_run.isoformat() if scraper.status.last_run else None,
        "live_enabled": flight_api_client.live_enabled,
        "source": "serpapi" if flight_api_client.live_enabled else "mock",
    }


async def scrape_trunk_live(force: bool = False) -> dict:
    """Fetch live SerpApi fares for the 3 trunk corridors at T+15 (3 API calls).

    Quota guard: skips the network when recent serpapi rows already exist,
    unless `force=True`. Boot and the daily cron call this with force=False.
    """
    global _last_live_refresh_at
    from datetime import date as date_type
    from skymetric.models.database import SessionLocal, init_db

    if not flight_api_client.live_enabled:
        return {"skipped": True, "reason": "no SERPAPI_KEY"}

    if not force:
        recent = _recent_live_fare_count()
        if recent > 0:
            logger.info(
                f"Trunk live scrape skipped ({recent} serpapi rows in last "
                f"{LIVE_MIN_INTERVAL_HOURS}h) — saving SerpApi quota"
            )
            return {
                "skipped": True,
                "reason": "recent_live_data",
                "recent_live_fares": recent,
            }

    init_db()
    db = SessionLocal()
    counts = {"serpapi": 0, "mock": 0}
    try:
        today = date_type.today()
        target = today + timedelta(days=15)
        dep = datetime.combine(target, datetime.min.time())
        for corridor in CORRIDORS:
            key = f"{corridor['origin']}-{corridor['destination']}"
            if key not in LIVE_DAILY_CORRIDOR_KEYS:
                continue
            fares, source = await flight_api_client.search_flights(
                corridor["origin"], corridor["destination"], dep, 15, prefer_live=True
            )
            counts[source] = counts.get(source, 0) + len(fares)
            _insert_fares(db, fares)
        db.commit()
        _last_live_refresh_at = datetime.utcnow()
        logger.info(f"Trunk live scrape done: {counts}")
        return {"counts": counts}
    finally:
        db.close()


@router.post("/live-refresh")
async def live_refresh(
    force: bool = False,
    x_api_key: Optional[str] = Header(None),
):
    """One-shot live refresh: 3 trunk corridors via SerpApi (~3 quota units).

    force=false (default): skips if live rows exist within the last 12h.
    force=true: always fetch, subject to a 10-minute cooldown.
    """
    global _last_live_refresh_at
    _verify_api_key(x_api_key)
    if scraper.status.is_running:
        raise HTTPException(status_code=409, detail="Scraper is already running")
    if not flight_api_client.live_enabled:
        raise HTTPException(status_code=400, detail="SERPAPI_KEY not configured")

    if force and _last_live_refresh_at is not None:
        elapsed = datetime.utcnow() - _last_live_refresh_at
        if elapsed < timedelta(minutes=LIVE_REFRESH_COOLDOWN_MIN):
            raise HTTPException(
                status_code=429,
                detail=(
                    f"Live refresh cooldown: try again in "
                    f"{LIVE_REFRESH_COOLDOWN_MIN} minutes (quota protection)"
                ),
            )

    result = await scrape_trunk_live(force=force)
    scraper.status.last_run = datetime.now()
    scraper.status.completed_jobs += 1
    breakdown = _source_breakdown()
    if not result.get("skipped"):
        _last_live_refresh_at = datetime.utcnow()
    return {
        "message": (
            "Live refresh skipped (recent data)"
            if result.get("skipped")
            else "Live refresh complete"
        ),
        "fetched": result,
        "source_breakdown": breakdown,
        "live_fares": breakdown.get("serpapi", 0),
    }


@router.post("/daemon/start")
async def start_daemon(
    interval_minutes: int = 60,
    x_api_key: Optional[str] = Header(None),
):
    """Start continuous live scraping daemon (SerpApi trunk refresh loop)."""
    _verify_api_key(x_api_key)
    global _daemon_task, _daemon_running

    if _daemon_running:
        return {"error": "Daemon already running", "interval_minutes": interval_minutes}

    if not flight_api_client.live_enabled:
        raise HTTPException(status_code=400, detail="SERPAPI_KEY not configured")

    _daemon_running = True

    async def _daemon_loop():
        global _daemon_running
        while _daemon_running:
            try:
                await scrape_trunk_live()
                scraper.status.last_run = datetime.now()
                scraper.status.completed_jobs += 1
            except Exception:
                logger.exception("daemon scrape failed")
                scraper.status.failed_jobs += 1
            await asyncio.sleep(max(interval_minutes, 5) * 60)

    _daemon_task = asyncio.create_task(_daemon_loop())

    return {
        "message": "Live daemon started",
        "interval_minutes": interval_minutes,
        "corridors": sorted(LIVE_DAILY_CORRIDOR_KEYS),
        "source": "serpapi",
    }


@router.post("/daemon/stop")
async def stop_daemon(x_api_key: Optional[str] = Header(None)):
    """Stop the continuous scraping daemon. Requires X-API-Key header."""
    _verify_api_key(x_api_key)
    global _daemon_task, _daemon_running

    if not _daemon_running:
        return {"error": "Daemon not running"}

    _daemon_running = False
    if _daemon_task:
        _daemon_task.cancel()
        _daemon_task = None

    return {"message": "Daemon stopped"}
