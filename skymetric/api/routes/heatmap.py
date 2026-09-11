"""Heatmap endpoint: sector x time matrix for visualization."""

from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Query

from skymetric.data.dgca_weights import CORRIDORS, CARRIER_MARKET_SHARE

router = APIRouter()


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

    # Generate synthetic heatmap values for demonstration
    import random
    random.seed(42)

    matrix = []
    for corridor in corridors:
        row = []
        base_val = random.uniform(3000, 7000)
        for d in dates:
            noise = random.uniform(0.85, 1.15)
            row.append(round(base_val * noise, 2))
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
