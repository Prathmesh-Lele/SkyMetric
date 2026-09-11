"""Mock scraper: generates realistic synthetic fare data for testing."""

import random
from datetime import datetime
from typing import List, Dict

from skymetric.scraper.base import BaseScraper
from skymetric.data.dgca_weights import CARRIERS, ADVANCE_WINDOWS
from skymetric.data.seed_data import (
    BASE_FARE_RANGES,
    CARRIER_MULTIPLIER,
    ADVANCE_DISCOUNT,
    DAY_OF_WEEK_SEASONALITY,
    generate_flight_number,
)

# Time slots: (hour_range, slot_label, price_multiplier)
TIME_SLOTS = [
    ((5, 7), "early_morning", 1.12),
    ((8, 10), "morning", 1.05),
    ((12, 14), "afternoon", 1.00),
    ((17, 19), "evening", 1.08),
    ((20, 22), "night", 0.95),
]


class MockScraper(BaseScraper):
    """Generates realistic synthetic fare data without hitting any external APIs.

    Each carrier gets 2-4 flights per route (different time slots), similar to
    VayuSutra's connector approach. This yields ~24 quotes per corridor instead of 6.
    """

    def scrape(
        self,
        origin: str,
        destination: str,
        departure_date: datetime,
        advance_window_days: int,
    ) -> List[Dict]:
        route_key = f"{origin}-{destination}"
        base_low, base_high = BASE_FARE_RANGES.get(route_key, (3000, 6000))
        day_of_week = departure_date.weekday()
        dow_mult = DAY_OF_WEEK_SEASONALITY.get(day_of_week, 1.0)
        advance_mult = ADVANCE_DISCOUNT.get(advance_window_days, 1.0)

        records = []
        for carrier in CARRIERS:
            carrier_mult = CARRIER_MULTIPLIER.get(carrier, 1.0)
            # Each carrier gets 2-4 time slots
            num_flights = random.choice([2, 3, 4])
            selected_slots = random.sample(TIME_SLOTS, num_flights)

            for (hour_min, hour_max), slot_label, slot_mult in selected_slots:
                base_fare = random.uniform(base_low, base_high)
                total = base_fare * carrier_mult * advance_mult * dow_mult * slot_mult
                noise = random.uniform(0.95, 1.05)
                total *= noise

                base_fare_final = round(total * 0.70, 2)
                taxes = round(total * 0.12 + random.uniform(200, 500), 2)
                udf = round(total * 0.08, 2)
                convenience = round(total * 0.10, 2)
                total_final = round(base_fare_final + taxes + udf + convenience, 2)

                departure_hour = random.randint(hour_min, hour_max)
                departure = departure_date.replace(hour=departure_hour, minute=random.randint(0, 59))

                records.append({
                    "timestamp": datetime.utcnow(),
                    "origin": origin,
                    "destination": destination,
                    "carrier": carrier,
                    "flight_number": generate_flight_number(carrier),
                    "departure_time": departure,
                    "advance_window_days": advance_window_days,
                    "fare_class": "economy",
                    "base_fare": base_fare_final,
                    "taxes_and_fees": taxes,
                    "udf": udf,
                    "convenience_charge": convenience,
                    "total_fare": total_final,
                    "source_platform": "mock",
                })

        return records

    def health_check(self) -> bool:
        return True
