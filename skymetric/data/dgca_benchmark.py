"""Static DGCA monthly average fare benchmarks for back-testing.

Values derived from publicly available DGCA monthly air fare data
(https://www.dgca.gov.in/digigov-portal/jsp/dgca/homePage/airFareData.html).
Representative averages for major Indian domestic corridors.
"""

from datetime import datetime, timedelta

# DGCA monthly average fares (INR) per corridor — Aug/Sep 2024 reference
DGCA_CORRIDOR_AVERAGES = {
    "DEL-BOM": 5280,
    "DEL-BLR": 5950,
    "BOM-BLR": 4750,
    "DEL-CCU": 5420,
    "DEL-HYD": 5680,
    "BOM-MAA": 4900,
    "BLR-HYD": 3650,
    "DEL-MAA": 6100,
    "DEL-IXS": 7850,
    "DEL-DHM": 7200,
}

# Corridor weights based on DGCA passenger traffic data
CORRIDOR_WEIGHTS = {
    "DEL-BOM": 0.184,
    "DEL-BLR": 0.142,
    "BOM-BLR": 0.098,
    "DEL-CCU": 0.076,
    "DEL-HYD": 0.068,
    "BOM-MAA": 0.062,
    "BLR-HYD": 0.054,
    "DEL-MAA": 0.048,
    "DEL-IXS": 0.032,
    "DEL-DHM": 0.028,
}


def generate_dgca_benchmark_30d(end_date: datetime | None = None) -> list[dict]:
    """Generate 30 days of DGCA-like benchmark fares with realistic daily variation.

    Returns list of {date, corridor, avg_fare, weight} dicts.
    DGCA publishes monthly averages, so we add realistic daily noise
    to simulate what daily tracking would look like.
    """
    import random
    if end_date is None:
        end_date = datetime.utcnow()

    random.seed(42)  # Deterministic for reproducibility
    records = []
    for i in range(30):
        day = end_date - timedelta(days=i)
        for corridor, base_avg in DGCA_CORRIDOR_AVERAGES.items():
            # DGCA monthly avg ± daily noise (±5%)
            noise = random.uniform(0.95, 1.05)
            # Slight weekend premium (Fri-Sun)
            dow = day.weekday()
            weekend_mult = 1.06 if dow >= 4 else 1.0
            avg_fare = round(base_avg * noise * weekend_mult, 2)
            records.append({
                "date": day.strftime("%Y-%m-%d"),
                "corridor": corridor,
                "avg_fare": avg_fare,
                "weight": CORRIDOR_WEIGHTS.get(corridor, 0.05),
            })
    return records


def compute_national_dgca_index(benchmark_records: list[dict]) -> list[dict]:
    """Compute weighted national average fare from corridor-level DGCA data."""
    from collections import defaultdict
    by_date = defaultdict(lambda: {"weighted_sum": 0.0, "weight_total": 0.0})
    for rec in benchmark_records:
        d = rec["date"]
        by_date[d]["weighted_sum"] += rec["avg_fare"] * rec["weight"]
        by_date[d]["weight_total"] += rec["weight"]

    result = []
    for d in sorted(by_date.keys()):
        v = by_date[d]
        national_avg = round(v["weighted_sum"] / v["weight_total"], 2) if v["weight_total"] > 0 else 0
        result.append({"date": d, "national_avg_fare": national_avg})
    return result
