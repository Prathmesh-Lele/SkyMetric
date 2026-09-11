"""Index computation orchestrator: compute daily, weekly, monthly, sector, and national indices."""

from datetime import date, datetime, timedelta
from typing import List, Dict, Optional, Tuple
from collections import defaultdict

from skymetric.index_engine.formulas import (
    jevons_index, laspeyres_index, paasche_index,
    fisher_index, torqvist_index, chain_laspeyres_index,
    cpi_transmission_bps,
)
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


def compute_weekly_index(
    daily_indices: List[Dict],
) -> Dict:
    """Compute weekly SkyMetric from daily index values.

    Args:
        daily_indices: list of {"date": str, "headline": float, "sectors": dict}

    Returns:
        dict with weekly averaged headline and sector indices
    """
    if not daily_indices:
        return {"headline": 100.0, "sectors": {}}

    # Group by ISO week
    weekly_data = defaultdict(list)
    for rec in daily_indices:
        d = datetime.strptime(rec["date"], "%Y-%m-%d").date()
        week_key = d.isocalendar()[:2]  # (year, week_number)
        weekly_data[week_key].append(rec)

    # Compute latest week average
    latest_week = max(weekly_data.keys())
    week_records = weekly_data[latest_week]

    headline_avg = round(sum(r["headline"] for r in week_records) / len(week_records), 2)

    # Average sector indices across the week
    sector_avg = {}
    all_sectors = set()
    for r in week_records:
        all_sectors.update(r.get("sectors", {}).keys())
    for sector in all_sectors:
        vals = [r.get("sectors", {}).get(sector, 100.0) for r in week_records]
        sector_avg[sector] = round(sum(vals) / len(vals), 2)

    year, week = latest_week
    return {
        "headline": headline_avg,
        "sectors": sector_avg,
        "year": year,
        "week": week,
        "days_in_week": len(week_records),
    }


def compute_monthly_index(
    daily_indices: List[Dict],
) -> Dict:
    """Compute monthly SkyMetric from daily index values.

    Args:
        daily_indices: list of {"date": str, "headline": float, "sectors": dict}

    Returns:
        dict with monthly averaged headline and sector indices
    """
    if not daily_indices:
        return {"headline": 100.0, "sectors": {}}

    # Group by year-month
    monthly_data = defaultdict(list)
    for rec in daily_indices:
        d = datetime.strptime(rec["date"], "%Y-%m-%d").date()
        month_key = (d.year, d.month)
        monthly_data[month_key].append(rec)

    # Compute latest month average
    latest_month = max(monthly_data.keys())
    month_records = monthly_data[latest_month]

    headline_avg = round(sum(r["headline"] for r in month_records) / len(month_records), 2)

    # Average sector indices across the month
    sector_avg = {}
    all_sectors = set()
    for r in month_records:
        all_sectors.update(r.get("sectors", {}).keys())
    for sector in all_sectors:
        vals = [r.get("sectors", {}).get(sector, 100.0) for r in month_records]
        sector_avg[sector] = round(sum(vals) / len(vals), 2)

    year, month = latest_month
    return {
        "headline": headline_avg,
        "sectors": sector_avg,
        "year": year,
        "month": month,
        "days_in_month": len(month_records),
    }


def compute_chain_index(
    period_indices: List[float],
) -> List[float]:
    """Compute chain-linked index from a series of period indices.

    Args:
        period_indices: list of index values (each relative to previous period)

    Returns:
        list of chain-linked index values (base = first period)
    """
    return chain_laspeyres_index(period_indices)


def compute_superlative_indices(
    all_records: List[Dict],
    base_records: List[Dict],
) -> Dict:
    """Compute Fisher, Paasche, and Torqvist superlative indices.

    Returns dict with:
        - fisher: Fisher Ideal index
        - paasche: Paasche index
        - torqvist: Tornqvist index
        - laspeyres: Laspeyres index
        - jevons: Jevons index
        - cpi_bps: CPI transmission basis points
    """
    from skymetric.data.dgca_weights import CORRIDORS, CARRIER_MARKET_SHARE

    # Collect all corridors and compute sector-level indices
    corridors_seen = set()
    for r in all_records:
        corridors_seen.add(f"{r['origin']}-{r['destination']}")

    # Build price lists for superlative computation
    prices_t = []
    prices_t0 = []
    weights = []
    shares_t = []
    shares_t0 = []

    for corridor in corridors_seen:
        origin, dest = corridor.split("-")
        curr = [r for r in all_records if r["origin"] == origin and r["destination"] == dest]
        base = [r for r in base_records if r["origin"] == origin and r["destination"] == dest]

        if not curr or not base:
            continue

        curr_prices = [r["total_fare"] for r in curr if r.get("total_fare", 0) > 0]
        base_prices = [r["total_fare"] for r in base if r.get("total_fare", 0) > 0]

        if not curr_prices or not base_prices:
            continue

        # Use median for robustness
        curr_prices.sort()
        base_prices.sort()
        curr_med = curr_prices[len(curr_prices) // 2]
        base_med = base_prices[len(base_prices) // 2]

        # Get DGCA weight
        w = 1.0
        for c in CORRIDORS:
            if c["origin"] == origin and c["destination"] == dest:
                w = c.get("weight", 1.0)
                break

        prices_t.append(curr_med)
        prices_t0.append(base_med)
        weights.append(w)

        # Expenditure shares for Tornqvist
        total_t = sum(curr_prices)
        total_t0 = sum(base_prices)
        shares_t.append(curr_med / total_t if total_t > 0 else 0)
        shares_t0.append(base_med / total_t0 if total_t0 > 0 else 0)

    if not prices_t:
        return {
            "fisher": 100.0, "paasche": 100.0, "torqvist": 100.0,
            "laspeyres": 100.0, "jevons": 100.0, "cpi_bps": {},
        }

    # Compute all indices
    las = laspeyres_index(prices_t, prices_t0, weights)
    paas = paasche_index(prices_t, prices_t0, weights)
    fish = fisher_index(prices_t, prices_t0, weights)
    torq = torqvist_index(prices_t, prices_t0, shares_t, shares_t0)
    jev = jevons_index(prices_t, prices_t0)

    # CPI transmission
    fare_change_pct = ((fish / 100) - 1) * 100 if fish > 0 else 0
    cpi_bps = cpi_transmission_bps(fare_change_pct)

    return {
        "fisher": round(fish, 2),
        "paasche": round(paas, 2),
        "torqvist": round(torq, 2),
        "laspeyres": round(las, 2),
        "jevons": round(jev, 2),
        "cpi_bps": cpi_bps,
    }


def detect_anomalies(
    records: List[Dict],
    z_threshold: float = 3.0,
) -> List[Dict]:
    """Detect fare anomalies using Modified Z-Score (MAD method).

    An anomaly is a fare with |MAD Z-score| > threshold.
    """
    if not records:
        return []

    # Group by corridor+window
    groups = defaultdict(list)
    for r in records:
        key = (r["origin"], r["destination"], r.get("advance_window_days", 15))
        groups[key].append(r)

    anomalies = []
    for (origin, dest, window), group_records in groups.items():
        fares = [r["total_fare"] for r in group_records if r.get("total_fare", 0) > 0]
        if len(fares) < 3:
            continue

        fares.sort()
        median = fares[len(fares) // 2]
        deviations = [abs(f - median) for f in fares]
        deviations.sort()
        mad = deviations[len(deviations) // 2]

        if mad == 0:
            continue

        for r in group_records:
            fare = r.get("total_fare", 0)
            if fare <= 0:
                continue
            z_score = 0.6745 * (fare - median) / mad
            if abs(z_score) > z_threshold:
                anomalies.append({
                    "origin": r["origin"],
                    "destination": r["destination"],
                    "carrier": r.get("carrier", "Unknown"),
                    "flight_number": r.get("flight_number", ""),
                    "fare": fare,
                    "median_fare": round(median, 2),
                    "z_score": round(z_score, 2),
                    "direction": "spike" if z_score > 0 else "drop",
                    "advance_window_days": window,
                    "timestamp": r.get("timestamp", ""),
                })

    anomalies.sort(key=lambda x: abs(x["z_score"]), reverse=True)
    return anomalies


def compute_data_trust_score(
    records: List[Dict],
    anomalies: List[Dict],
) -> Dict:
    """Compute Data Trust Scorecard (0-100) across 7 dimensions.

    Dimensions:
        1. Source diversity (0-15): number of unique sources
        2. Corridor coverage (0-15): % of expected corridors present
        3. Carrier coverage (0-15): % of expected carriers present
        4. Data freshness (0-15): how recent the data is
        5. Outlier ratio (0-15): lower anomalies = higher score
        6. Completeness (0-15): % of records with all fields populated
        7. Volume adequacy (0-10): sufficient observations per cell
    """
    from skymetric.data.dgca_weights import CORRIDORS, CARRIER_MARKET_SHARE

    total_records = len(records)
    if total_records == 0:
        return {"score": 0, "dimensions": {}, "grade": "F"}

    # 1. Source diversity
    sources = set(r.get("source_platform", "") for r in records)
    expected_sources = {"seed_generator", "mock", "indigo", "spicejet", "akasa", "cleartrip"}
    source_score = min(15, int(len(sources) / len(expected_sources) * 15))

    # 2. Corridor coverage
    corridors = set((r["origin"], r["destination"]) for r in records)
    corridor_score = min(15, int(len(corridors) / len(CORRIDORS) * 15))

    # 3. Carrier coverage
    carriers = set(r.get("carrier", "") for r in records)
    carrier_score = min(15, int(len(carriers) / len(CARRIER_MARKET_SHARE) * 15))

    # 4. Data freshness
    timestamps = []
    for r in records:
        ts = r.get("timestamp", "")
        if isinstance(ts, datetime):
            timestamps.append(ts)
        elif isinstance(ts, str) and ts:
            try:
                timestamps.append(datetime.fromisoformat(ts.replace("Z", "+00:00")))
            except (ValueError, TypeError):
                pass
    if timestamps:
        latest = max(timestamps)
        hours_old = (datetime.now(latest.tzinfo) - latest).total_seconds() / 3600
        freshness_score = max(0, min(15, int(15 - hours_old / 24)))
    else:
        freshness_score = 0

    # 5. Outlier ratio
    anomaly_ratio = len(anomalies) / total_records if total_records > 0 else 0
    outlier_score = max(0, min(15, int(15 * (1 - anomaly_ratio * 10))))

    # 6. Completeness
    required_fields = ["origin", "destination", "carrier", "total_fare", "advance_window_days"]
    complete = sum(1 for r in records if all(r.get(f) for f in required_fields))
    completeness_score = min(15, int(complete / total_records * 15))

    # 7. Volume adequacy
    cells = defaultdict(int)
    for r in records:
        key = (r["origin"], r["destination"], r.get("advance_window_days", 15))
        cells[key] += 1
    adequate_cells = sum(1 for v in cells.values() if v >= 3)
    volume_score = min(10, int(adequate_cells / max(1, len(cells)) * 10))

    total_score = (
        source_score + corridor_score + carrier_score +
        freshness_score + outlier_score + completeness_score + volume_score
    )

    # Grade
    if total_score >= 90:
        grade = "A+"
    elif total_score >= 80:
        grade = "A"
    elif total_score >= 70:
        grade = "B+"
    elif total_score >= 60:
        grade = "B"
    elif total_score >= 50:
        grade = "C"
    elif total_score >= 30:
        grade = "D"
    else:
        grade = "F"

    return {
        "score": total_score,
        "grade": grade,
        "dimensions": {
            "source_diversity": source_score,
            "corridor_coverage": corridor_score,
            "carrier_coverage": carrier_score,
            "data_freshness": freshness_score,
            "outlier_ratio": outlier_score,
            "completeness": completeness_score,
            "volume_adequacy": volume_score,
        },
        "details": {
            "total_records": total_records,
            "unique_sources": len(sources),
            "unique_corridors": len(corridors),
            "unique_carriers": len(carriers),
            "anomaly_count": len(anomalies),
            "anomaly_ratio": round(anomaly_ratio * 100, 2),
        },
    }
