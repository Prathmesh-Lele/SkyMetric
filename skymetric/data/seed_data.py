"""30-day historical seed data generator calibrated against DGCA benchmarks.

Generates realistic fare data with:
- Base fare ranges per corridor (₹2,500–₹8,500)
- Carrier-specific pricing multipliers
- Advance-purchase elasticity curves
- Day-of-week seasonality
- Random noise and outliers
"""

import random
from datetime import datetime, timedelta
from typing import List

from skymetric.data.dgca_weights import CORRIDORS, CARRIERS, CARRIER_MARKET_SHARE, ADVANCE_WINDOWS

BASE_FARE_RANGES = {
    "DEL-BOM": (3000, 5500),
    "DEL-BLR": (3500, 6500),
    "BOM-BLR": (2800, 5000),
    "DEL-CCU": (3200, 5800),
    "DEL-HYD": (3400, 6200),
    "BOM-MAA": (3000, 5200),
    "BLR-HYD": (2200, 4000),
    "DEL-MAA": (3600, 6800),
    "DEL-IXS": (5000, 8500),
    "DEL-DHM": (4500, 8000),
}

CARRIER_MULTIPLIER = {
    "IndiGo": 0.92,
    "Air India": 1.15,
    "Vistara": 1.12,
    "SpiceJet": 0.88,
    "Akasa Air": 0.85,
    "Air India Express": 0.90,
}

ADVANCE_DISCOUNT = {
    1: 1.45,
    7: 1.18,
    15: 1.00,
    30: 0.88,
    45: 0.82,
}

DAY_OF_WEEK_SEASONALITY = {
    0: 1.02,
    1: 0.98,
    2: 0.97,
    3: 0.99,
    4: 1.08,
    5: 1.12,
    6: 1.05,
}


def generate_flight_number(carrier: str) -> str:
    prefix_map = {
        "IndiGo": "6E",
        "Air India": "AI",
        "Vistara": "UK",
        "SpiceJet": "SG",
        "Akasa Air": "QP",
        "Air India Express": "IX",
    }
    return f"{prefix_map[carrier]}{random.randint(100, 9999)}"


def generate_fares_for_day(
    target_date: datetime,
    include_outliers: bool = True,
) -> List[dict]:
    """Generate fare quotes for all corridors, carriers, and advance windows on a single day."""
    records = []
    day_of_week = target_date.weekday()

    for corridor in CORRIDORS:
        route_key = f"{corridor['origin']}-{corridor['destination']}"
        base_low, base_high = BASE_FARE_RANGES.get(route_key, (3000, 6000))

        for carrier in CARRIERS:
            carrier_mult = CARRIER_MULTIPLIER.get(carrier, 1.0)

            for window in ADVANCE_WINDOWS:
                advance_mult = ADVANCE_DISCOUNT.get(window, 1.0)
                dow_mult = DAY_OF_WEEK_SEASONALITY.get(day_of_week, 1.0)

                base_fare = random.uniform(base_low, base_high)
                total = base_fare * carrier_mult * advance_mult * dow_mult

                # Add noise ±8%
                noise = random.uniform(0.92, 1.08)
                total *= noise

                # Occasionally inject outliers for testing pipeline robustness
                if include_outliers and random.random() < 0.02:
                    total *= random.choice([0.3, 3.5])

                base_fare_final = round(total * 0.75, 2)
                taxes = round(total * 0.15 + random.uniform(200, 600), 2)
                total_final = round(base_fare_final + taxes, 2)

                departure_hour = random.choice([5, 6, 7, 8, 9, 10, 11, 13, 14, 16, 18, 20, 22])
                departure = target_date.replace(hour=departure_hour, minute=random.randint(0, 59))

                records.append({
                    "timestamp": target_date,
                    "origin": corridor["origin"],
                    "destination": corridor["destination"],
                    "carrier": carrier,
                    "flight_number": generate_flight_number(carrier),
                    "departure_time": departure,
                    "advance_window_days": window,
                    "fare_class": "economy",
                    "base_fare": max(base_fare_final, 0),
                    "taxes_and_fees": max(taxes, 0),
                    "total_fare": max(total_final, 0),
                    "source_platform": "seed_generator",
                })

    return records


def generate_30_day_seed(
    end_date: datetime | None = None,
    include_outliers: bool = True,
) -> List[dict]:
    """Generate 30 days of historical fare data."""
    if end_date is None:
        end_date = datetime.utcnow()

    all_records = []
    for i in range(30):
        day = end_date - timedelta(days=i)
        day_records = generate_fares_for_day(day, include_outliers=include_outliers)
        all_records.extend(day_records)

    return all_records
