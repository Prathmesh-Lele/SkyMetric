"""Schema normalization: separate base fares from taxes, normalize field names."""

from typing import List, Dict


def normalize_record(record: Dict) -> Dict:
    """Normalize a single fare record to the unified schema."""
    base_fare = record.get("base_fare", 0)
    taxes = record.get("taxes_and_fees", 0)
    total = record.get("total_fare", 0)

    # Recompute total if missing or inconsistent
    if total <= 0 and base_fare > 0:
        total = base_fare + taxes

    return {
        "timestamp": record.get("timestamp"),
        "origin": (record.get("origin") or "").upper()[:3],
        "destination": (record.get("destination") or "").upper()[:3],
        "carrier": record.get("carrier", "Unknown"),
        "flight_number": record.get("flight_number", ""),
        "departure_time": record.get("departure_time"),
        "advance_window_days": record.get("advance_window_days", 0),
        "fare_class": record.get("fare_class", "economy"),
        "base_fare": round(max(base_fare, 0), 2),
        "taxes_and_fees": round(max(taxes, 0), 2),
        "total_fare": round(max(total, 0), 2),
        "source_platform": record.get("source_platform", "unknown"),
    }


def normalize_records(records: List[Dict]) -> List[Dict]:
    """Normalize a batch of fare records."""
    return [normalize_record(r) for r in records]
