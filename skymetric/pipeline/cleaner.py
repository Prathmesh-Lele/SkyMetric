"""Data cleaning pipeline: outlier rejection and deduplication."""

from typing import List, Dict
import statistics


def remove_outliers_zscore(records: List[Dict], threshold: float = 3.0) -> List[Dict]:
    """Remove fare records with total_fare Z-score > threshold."""
    if not records:
        return records

    fares = [r["total_fare"] for r in records if r.get("total_fare", 0) > 0]
    if len(fares) < 3:
        return records

    mean = statistics.mean(fares)
    stdev = statistics.stdev(fares)
    if stdev == 0:
        return records

    cleaned = []
    for r in records:
        fare = r.get("total_fare", 0)
        if fare <= 0:
            continue
        z = abs((fare - mean) / stdev)
        if z <= threshold:
            cleaned.append(r)
    return cleaned


def deduplicate(records: List[Dict]) -> List[Dict]:
    """Remove duplicate fare records across platforms, keeping latest."""
    seen = {}
    for r in records:
        key = (
            r.get("origin"),
            r.get("destination"),
            r.get("carrier"),
            r.get("flight_number"),
            r.get("advance_window_days"),
            r.get("departure_time"),
        )
        existing = seen.get(key)
        if existing is None or r.get("timestamp", "") > existing.get("timestamp", ""):
            seen[key] = r
    return list(seen.values())


def validate_record(record: Dict) -> bool:
    """Validate a single fare record has required fields."""
    required = ["origin", "destination", "carrier", "total_fare"]
    for field in required:
        if not record.get(field):
            return False
    if record.get("total_fare", 0) <= 0:
        return False
    return True


def clean_pipeline(records: List[Dict]) -> List[Dict]:
    """Full cleaning pipeline: validate, deduplicate, remove outliers."""
    valid = [r for r in records if validate_record(r)]
    deduped = deduplicate(valid)
    cleaned = remove_outliers_zscore(deduped)
    return cleaned
