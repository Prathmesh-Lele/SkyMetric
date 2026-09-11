"""Analytics endpoints: superlative indices, anomaly detection, data trust scorecard."""

from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
import csv
import io

from skymetric.data.seed_data import generate_30_day_seed
from skymetric.pipeline.cleaner import clean_pipeline
from skymetric.pipeline.normalizer import normalize_records
from skymetric.index_engine.calculator import (
    compute_superlative_indices,
    detect_anomalies,
    compute_data_trust_score,
)

router = APIRouter()


def _get_current_and_base(target_date: date):
    """Load current and base records from DB or seed."""
    from skymetric.models.database import SessionLocal, init_db
    from skymetric.models.fare import Fare
    from sqlalchemy import func

    init_db()
    db = SessionLocal()
    try:
        base_date = target_date - timedelta(days=30)

        def _load(d):
            rows = db.query(Fare).filter(func.date(Fare.timestamp) == d).all()
            if rows:
                return [
                    {
                        "origin": r.origin, "destination": r.destination,
                        "carrier": r.carrier, "flight_number": r.flight_number,
                        "departure_time": r.departure_time.isoformat() if r.departure_time else "",
                        "advance_window_days": r.advance_window_days,
                        "fare_class": r.fare_class,
                        "base_fare": r.base_fare, "taxes_and_fees": r.taxes_and_fees,
                        "udf": getattr(r, "udf", 0), "convenience_charge": getattr(r, "convenience_charge", 0),
                        "total_fare": r.total_fare,
                        "source_platform": r.source_platform,
                        "timestamp": r.timestamp.isoformat() if r.timestamp else "",
                    }
                    for r in rows
                ]
            return []

        current = _load(target_date)
        base = _load(base_date)

        if not current or not base:
            all_seed = generate_30_day_seed(
                end_date=datetime.combine(target_date, datetime.min.time()),
                days=31,
            )
            current = [r for r in all_seed if r["timestamp"].date() == target_date] if not current else current
            base = [r for r in all_seed if r["timestamp"].date() == base_date] if not base else base

        return current, base
    finally:
        db.close()


@router.get("/superlative")
def get_superlative_indices(
    target_date: Optional[date] = Query(None),
):
    """Get Fisher, Paasche, Tornqvist, Laspeyres, and Jevons indices."""
    if target_date is None:
        target_date = date.today()

    current, base = _get_current_and_base(target_date)
    current_clean = clean_pipeline(normalize_records(current))
    base_clean = clean_pipeline(normalize_records(base))

    result = compute_superlative_indices(current_clean, base_clean)
    result["date"] = target_date.isoformat()
    result["base_date"] = (target_date - timedelta(days=30)).isoformat()
    return result


@router.get("/anomalies")
def get_anomalies(
    target_date: Optional[date] = Query(None),
    threshold: float = Query(3.0, description="Z-score threshold for anomaly detection"),
):
    """Detect fare anomalies using Modified Z-Score (MAD method)."""
    if target_date is None:
        target_date = date.today()

    current, _ = _get_current_and_base(target_date)
    current_clean = clean_pipeline(normalize_records(current))

    anomalies = detect_anomalies(current_clean, z_threshold=threshold)
    return {
        "date": target_date.isoformat(),
        "threshold": threshold,
        "count": len(anomalies),
        "anomalies": anomalies[:50],  # Top 50
    }


@router.get("/data-trust")
def get_data_trust_score(
    target_date: Optional[date] = Query(None),
):
    """Compute Data Trust Scorecard (0-100) across 7 dimensions."""
    if target_date is None:
        target_date = date.today()

    current, _ = _get_current_and_base(target_date)
    current_clean = clean_pipeline(normalize_records(current))
    anomalies = detect_anomalies(current_clean)

    result = compute_data_trust_score(current_clean, anomalies)
    result["date"] = target_date.isoformat()
    return result


@router.get("/export/csv")
def export_csv(
    target_date: Optional[date] = Query(None),
    days: int = Query(30),
):
    """Export fare data as downloadable CSV."""
    from skymetric.models.database import SessionLocal
    from skymetric.models.fare import Fare

    if target_date is None:
        target_date = date.today()

    start_date = target_date - timedelta(days=days)

    db = SessionLocal()
    try:
        rows = (
            db.query(Fare)
            .filter(Fare.timestamp >= datetime.combine(start_date, datetime.min.time()))
            .filter(Fare.timestamp <= datetime.combine(target_date, datetime.max.time()))
            .order_by(Fare.timestamp)
            .all()
        )

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "timestamp", "origin", "destination", "carrier", "flight_number",
            "departure_time", "advance_window_days", "fare_class",
            "base_fare", "taxes_and_fees", "udf", "convenience_charge",
            "total_fare", "source_platform",
        ])

        for r in rows:
            writer.writerow([
                r.timestamp.isoformat() if r.timestamp else "",
                r.origin, r.destination, r.carrier, r.flight_number,
                r.departure_time.isoformat() if r.departure_time else "",
                r.advance_window_days, r.fare_class,
                r.base_fare, r.taxes_and_fees,
                getattr(r, "udf", 0), getattr(r, "convenience_charge", 0),
                r.total_fare, r.source_platform,
            ])

        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=skymetric_{target_date}.csv"},
        )
    finally:
        db.close()
