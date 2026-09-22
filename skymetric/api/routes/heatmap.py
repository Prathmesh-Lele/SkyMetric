"""Heatmap endpoint: sector x time matrix for visualization."""

from collections import defaultdict
from datetime import date, datetime, time, timedelta
from typing import Optional

from fastapi import APIRouter, Query

from skymetric.data.dgca_weights import CORRIDORS, CARRIER_MARKET_SHARE
from skymetric.models.database import SessionLocal, init_db
from skymetric.models.fare import Fare

router = APIRouter()

# Realistic fare bounds for Indian domestic corridors (INR)
FARE_FLOOR = 1800
FARE_CEILING = 15000


@router.get("/heatmap")
def get_heatmap_data(
    days: int = Query(30, description="Number of past days"),
    target_date: Optional[date] = Query(None),
):
    """Generate heatmap data: corridors x days matrix with fare values."""
    if target_date is None:
        target_date = date.today()

    corridors = [f"{c['origin']}-{c['destination']}" for c in CORRIDORS]
    dates = [(target_date - timedelta(days=i)).isoformat() for i in range(days - 1, -1, -1)]

    # Load actual fare data from database
    init_db()
    db = SessionLocal()
    try:
        start_dt = datetime.combine(target_date - timedelta(days=days - 1), time.min)
        end_dt = datetime.combine(target_date, time.max)

        records = (
            db.query(Fare)
            .filter(Fare.timestamp >= start_dt, Fare.timestamp <= end_dt)
            .order_by(Fare.timestamp)
            .all()
        )

        # Group by corridor and date, compute median total_fare with outlier filtering
        grouped = defaultdict(list)
        for r in records:
            if r.total_fare < FARE_FLOOR or r.total_fare > FARE_CEILING:
                continue
            corridor_key = f"{r.origin}-{r.destination}"
            date_key = r.timestamp.date().isoformat()
            grouped[(corridor_key, date_key)].append(r.total_fare)

        # Build matrix: rows = corridors, columns = dates
        matrix = []
        for corridor in corridors:
            row = []
            for d in dates:
                fares = grouped.get((corridor, d), [])
                if fares:
                    median_fare = round(sorted(fares)[len(fares) // 2], 2)
                else:
                    median_fare = 0.0
                row.append(median_fare)
            matrix.append(row)

        # Source breakdown for transparency
        from collections import Counter
        src_counts = Counter(r.source_platform for r in records)

        has_data = any(v != 0.0 for row in matrix for v in row)
        if not has_data:
            result = _generate_heatmap_from_seed(corridors, dates, target_date, days)
            result["source"] = "seed"
            result["source_breakdown"] = {}
            result["live_fares"] = 0
            return result

        live = src_counts.get("serpapi", 0)
        source_label = "live" if live > 0 else "database"
        return {
            "corridors": corridors,
            "dates": dates,
            "matrix": matrix,
            "unit": "INR",
            "source": source_label,
            "source_breakdown": dict(src_counts),
            "live_fares": live,
        }
    finally:
        db.close()


def _generate_heatmap_from_seed(
    corridors: list[str],
    dates: list[str],
    target_date: date,
    days: int,
) -> dict:
    """Generate heatmap from seed data when database is empty."""
    from skymetric.data.seed_data import generate_30_day_seed

    earliest_needed = target_date - timedelta(days=days - 1)
    total_days = days + 30
    all_seed = generate_30_day_seed(
        end_date=datetime.combine(target_date, datetime.min.time()),
        days=total_days,
    )

    # Group by corridor and date, filter outliers, compute median
    grouped = defaultdict(list)
    for r in all_seed:
        if r["total_fare"] < FARE_FLOOR or r["total_fare"] > FARE_CEILING:
            continue
        corridor_key = f"{r['origin']}-{r['destination']}"
        date_key = r["timestamp"].date().isoformat()
        grouped[(corridor_key, date_key)].append(r["total_fare"])

    matrix = []
    for corridor in corridors:
        row = []
        for d in dates:
            fares = grouped.get((corridor, d), [])
            if fares:
                median_fare = round(sorted(fares)[len(fares) // 2], 2)
            else:
                median_fare = 0.0
            row.append(median_fare)
        matrix.append(row)

    return {
        "corridors": corridors,
        "dates": dates,
        "matrix": matrix,
        "unit": "INR",
    }


@router.get("/carriers")
def get_carrier_data():
    """Get carrier market share and pricing data."""
    return {
        "carriers": [
            {"name": k, "market_share": v}
            for k, v in CARRIER_MARKET_SHARE.items()
        ]
    }