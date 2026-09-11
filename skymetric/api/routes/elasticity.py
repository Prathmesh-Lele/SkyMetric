"""Elasticity endpoint: advance-purchase lead-time price curves."""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Query

from skymetric.data.dgca_weights import CORRIDORS, ADVANCE_WINDOWS

router = APIRouter()


@router.get("/")
def get_elasticity_data(
    target_date: Optional[date] = Query(None),
):
    """Get advance-purchase elasticity curves for all corridors.

    Returns price multipliers at each advance window relative to T+15 anchor.
    """
    if target_date is None:
        target_date = date.today()

    import random
    random.seed(42)

    # Elasticity multipliers (T+1 is most expensive, T+45 cheapest)
    window_multipliers = {
        1: 1.45,
        7: 1.18,
        15: 1.00,
        30: 0.88,
        45: 0.82,
    }

    curves = {}
    for corridor in CORRIDORS:
        route = f"{corridor['origin']}-{corridor['destination']}"
        base_price = random.uniform(3000, 6000)
        curve = {}
        for window in ADVANCE_WINDOWS:
            mult = window_multipliers.get(window, 1.0)
            noise = random.uniform(0.97, 1.03)
            curve[str(window)] = round(base_price * mult * noise, 2)
        curves[route] = curve

    return {
        "date": target_date.isoformat(),
        "advance_windows": ADVANCE_WINDOWS,
        "curves": curves,
        "anchor_window": 15,
    }
