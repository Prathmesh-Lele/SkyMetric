"""Index endpoints: daily, weekly, monthly national and sector indices."""

from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Query
from sqlalchemy import func

from skymetric.models.database import SessionLocal
from skymetric.models.fare import Fare
from skymetric.models.index_value import IndexValue
from skymetric.index_engine.calculator import compute_daily_index, compute_weekly_index, compute_monthly_index
from skymetric.pipeline.cleaner import clean_pipeline
from skymetric.pipeline.normalizer import normalize_records
from skymetric.data.seed_data import generate_30_day_seed

router = APIRouter()


def _load_records_for_date(target_date: date) -> list[dict]:
    """Load fare records from DB for a specific date, or generate seed data."""
    db = SessionLocal()
    try:
        rows = (
            db.query(Fare)
            .filter(func.date(Fare.timestamp) == target_date)
            .all()
        )
        if rows:
            return [
                {
                    "origin": r.origin,
                    "destination": r.destination,
                    "carrier": r.carrier,
                    "flight_number": r.flight_number,
                    "departure_time": r.departure_time.isoformat() if r.departure_time else "",
                    "advance_window_days": r.advance_window_days,
                    "fare_class": r.fare_class,
                    "base_fare": r.base_fare,
                    "taxes_and_fees": r.taxes_and_fees,
                    "total_fare": r.total_fare,
                    "source_platform": r.source_platform,
                    "timestamp": r.timestamp.isoformat() if r.timestamp else "",
                }
                for r in rows
            ]
        return []
    finally:
        db.close()


def _load_records_range(start_date: date, end_date: date) -> list[dict]:
    """Load fare records from DB for a date range."""
    db = SessionLocal()
    try:
        rows = (
            db.query(Fare)
            .filter(func.date(Fare.timestamp) >= start_date)
            .filter(func.date(Fare.timestamp) <= end_date)
            .all()
        )
        return [
            {
                "origin": r.origin,
                "destination": r.destination,
                "carrier": r.carrier,
                "flight_number": r.flight_number,
                "departure_time": r.departure_time.isoformat() if r.departure_time else "",
                "advance_window_days": r.advance_window_days,
                "fare_class": r.fare_class,
                "base_fare": r.base_fare,
                "taxes_and_fees": r.taxes_and_fees,
                "total_fare": r.total_fare,
                "source_platform": r.source_platform,
                "timestamp": r.timestamp.isoformat() if r.timestamp else "",
            }
            for r in rows
        ]
    finally:
        db.close()


def _compute_daily_indices_range(start_date: date, end_date: date) -> list[dict]:
    """Compute daily index for each day in a range."""
    # Need data from end_date down to (start_date - 30) for base dates
    earliest_needed = start_date - timedelta(days=30)
    total_days = (end_date - earliest_needed).days + 1
    all_seed = generate_30_day_seed(
        end_date=datetime.combine(end_date, datetime.min.time()),
        days=total_days,
    )

    daily_indices = []
    current = start_date
    while current <= end_date:
        day_records = [r for r in all_seed if r["timestamp"].date() == current]
        base_date = current - timedelta(days=30)
        base_records = [r for r in all_seed if r["timestamp"].date() == base_date]

        if day_records and base_records:
            day_clean = clean_pipeline(normalize_records(day_records))
            base_clean = clean_pipeline(normalize_records(base_records))
            result = compute_daily_index(day_clean, base_clean)
            daily_indices.append({
                "date": current.isoformat(),
                "headline": result["headline"],
                "sectors": result["sectors"],
            })
        current += timedelta(days=1)

    return daily_indices


@router.get("/daily")
def get_daily_index(
    target_date: Optional[date] = Query(None, description="Date for index (YYYY-MM-DD)"),
):
    """Get national SkyMetric for a specific date with sector breakdown."""
    if target_date is None:
        target_date = date.today()

    current = _load_records_for_date(target_date)
    base_date = target_date - timedelta(days=30)
    base = _load_records_for_date(base_date)

    # If no data in DB, generate seed data covering both current and base dates
    if not current or not base:
        # Generate 31 days from target_date to ensure base_date (30 days back) is included
        all_seed = generate_30_day_seed(
            end_date=datetime.combine(target_date, datetime.min.time()),
            days=31,
        )
        current = [r for r in all_seed if r["timestamp"].date() == target_date]
        base = [r for r in all_seed if r["timestamp"].date() == base_date]

    current_clean = clean_pipeline(normalize_records(current))
    base_clean = clean_pipeline(normalize_records(base))

    result = compute_daily_index(current_clean, base_clean)

    return {
        "date": target_date.isoformat(),
        "headline_index": result["headline"],
        "sector_indices": result["sectors"],
        "window_indices": {str(k): v for k, v in result["windows"].items()},
        "base_date": base_date.isoformat(),
    }


@router.get("/weekly")
def get_weekly_index(
    target_date: Optional[date] = Query(None, description="End date for week (YYYY-MM-DD)"),
):
    """Get weekly SkyMetric index (averaged from daily values)."""
    if target_date is None:
        target_date = date.today()

    start_date = target_date - timedelta(days=6)
    daily_indices = _compute_daily_indices_range(start_date, target_date)

    if not daily_indices:
        return {
            "headline": 100.0,
            "sectors": {},
            "year": target_date.isocalendar()[0],
            "week": target_date.isocalendar()[1],
            "days_in_week": 0,
            "note": "No data available for this week",
        }

    return compute_weekly_index(daily_indices)


@router.get("/monthly")
def get_monthly_index(
    target_date: Optional[date] = Query(None, description="End date for month (YYYY-MM-DD)"),
):
    """Get monthly SkyMetric index (averaged from daily values)."""
    if target_date is None:
        target_date = date.today()

    start_date = target_date.replace(day=1)
    daily_indices = _compute_daily_indices_range(start_date, target_date)

    if not daily_indices:
        return {
            "headline": 100.0,
            "sectors": {},
            "year": target_date.year,
            "month": target_date.month,
            "days_in_month": 0,
            "note": "No data available for this month",
        }

    return compute_monthly_index(daily_indices)


@router.get("/sectors")
def get_sector_indices(
    target_date: Optional[date] = Query(None),
):
    """Get per-corridor index breakdown."""
    if target_date is None:
        target_date = date.today()

    current = _load_records_for_date(target_date)
    base_date = target_date - timedelta(days=30)
    base = _load_records_for_date(base_date)

    if not current or not base:
        all_seed = generate_30_day_seed(
            end_date=datetime.combine(target_date, datetime.min.time()),
            days=31,
        )
        current = [r for r in all_seed if r["timestamp"].date() == target_date]
        base = [r for r in all_seed if r["timestamp"].date() == base_date]

    current_clean = clean_pipeline(normalize_records(current))
    base_clean = clean_pipeline(normalize_records(base))

    from skymetric.index_engine.calculator import compute_sector_index

    corridors_seen = set()
    for r in current_clean:
        corridors_seen.add((r["origin"], r["destination"]))

    sectors = {}
    for origin, dest in corridors_seen:
        curr = [r for r in current_clean if r["origin"] == origin and r["destination"] == dest and r["advance_window_days"] == 15]
        bas = [r for r in base_clean if r["origin"] == origin and r["destination"] == dest and r["advance_window_days"] == 15]
        sectors[f"{origin}-{dest}"] = compute_sector_index(curr, bas)

    return {"date": target_date.isoformat(), "sectors": sectors}
