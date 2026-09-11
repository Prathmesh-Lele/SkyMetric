"""Index computation orchestrator: compute daily, sector, and national indices."""

from datetime import date, datetime, timedelta
from typing import List, Dict, Optional, Tuple
from collections import defaultdict

from skymetric.index_engine.formulas import jevons_index, laspeyres_index
from skymetric.index_engine.weights import get_all_weights, get_weight, normalize_weights


def compute_sector_index(
    fare_records: List[Dict],
    base_fares: List[Dict],
    method: str = "jevons",
) -> float:
    """Compute price index for a set of fares relative to base period fares.

    Args:
        fare_records: Current period fare records for one corridor+window
        base_fares: Base period fare records for the same corridor+window
        method: 'jevons' or 'laspeyres'
    """
    if not fare_records or not base_fares:
        return 100.0

    current_prices = [r["total_fare"] for r in fare_records if r.get("total_fare", 0) > 0]
    base_prices = [r["total_fare"] for r in base_fares if r.get("total_fare", 0) > 0]

    if not current_prices or not base_prices:
        return 100.0

    # Use median as representative price for each period
    current_prices.sort()
    base_prices.sort()
    current_med = current_prices[len(current_prices) // 2]
    base_med = base_prices[len(base_prices) // 2]

    if base_med <= 0:
        return 100.0

    if method == "jevons":
        return jevons_index([current_med], [base_med])
    else:
        return laspeyres_index([current_med], [base_med], [1.0])


def compute_national_index(
    sector_indices: Dict[str, float],
    base_date: Optional[date] = None,
) -> float:
    """Compute national SkyMetric from sector indices weighted by DGCA passenger shares.

    Args:
        sector_indices: dict of "ORIGIN-DEST" -> index value
        base_date: base date for weight reference (unused, weights are fixed)
    """
    if not sector_indices:
        return 100.0

    weights = get_all_weights()
    weight_map = {f"{w['origin']}-{w['destination']}": w["weight"] for w in weights}

    weighted_sum = 0.0
    weight_total = 0.0
    for route, index_val in sector_indices.items():
        w = weight_map.get(route, 1.0)
        weighted_sum += w * index_val
        weight_total += w

    if weight_total == 0:
        return 100.0

    return round(weighted_sum / weight_total, 2)


def compute_advance_window_indices(
    records: List[Dict],
    base_records: List[Dict],
    window: int,
) -> Dict[str, float]:
    """Compute sector indices for a specific advance window."""
    indices = {}
    corridors_seen = set()

    for r in records:
        key = f"{r['origin']}-{r['destination']}"
        corridors_seen.add(key)

    for corridor in corridors_seen:
        origin, dest = corridor.split("-")
        current = [r for r in records if r["origin"] == origin and r["destination"] == dest and r["advance_window_days"] == window]
        base = [r for r in base_records if r["origin"] == origin and r["destination"] == dest and r["advance_window_days"] == window]
        indices[corridor] = compute_sector_index(current, base)

    return indices


def compute_daily_index(
    all_records: List[Dict],
    base_records: List[Dict],
    target_window: int = 15,
) -> Dict:
    """Compute the daily national SkyMetric and sub-indices.

    Returns dict with:
        - headline: national index at target_window
        - sectors: per-corridor indices
        - windows: per-window national indices
    """
    # Filter to target advance window for headline
    headline_current = [r for r in all_records if r.get("advance_window_days") == target_window]
    headline_base = [r for r in base_records if r.get("advance_window_days") == target_window]

    sector_indices = {}
    corridors_seen = set()
    for r in headline_current:
        corridors_seen.add(f"{r['origin']}-{r['destination']}")

    for corridor in corridors_seen:
        origin, dest = corridor.split("-")
        curr = [r for r in headline_current if r["origin"] == origin and r["destination"] == dest]
        base = [r for r in headline_base if r["origin"] == origin and r["destination"] == dest]
        sector_indices[corridor] = compute_sector_index(curr, base)

    headline = compute_national_index(sector_indices)

    # Compute per-window national indices
    window_indices = {}
    for window in [1, 7, 15, 30, 45]:
        curr_w = [r for r in all_records if r.get("advance_window_days") == window]
        base_w = [r for r in base_records if r.get("advance_window_days") == window]
        sector_idx = {}
        cors = set()
        for r in curr_w:
            cors.add(f"{r['origin']}-{r['destination']}")
        for c in cors:
            o, d = c.split("-")
            cu = [r for r in curr_w if r["origin"] == o and r["destination"] == d]
            ba = [r for r in base_w if r["origin"] == o and r["destination"] == d]
            sector_idx[c] = compute_sector_index(cu, ba)
        window_indices[window] = compute_national_index(sector_idx)

    return {
        "headline": headline,
        "sectors": sector_indices,
        "windows": window_indices,
    }
