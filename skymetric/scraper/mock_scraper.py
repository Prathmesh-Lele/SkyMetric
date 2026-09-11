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


class MockScraper(BaseScraper):
    """Generates realistic synthetic fare data without hitting any external APIs."""

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
            base_fare = random.uniform(base_low, base_high)
            total = base_fare * carrier_mult * advance_mult * dow_mult
            noise = random.uniform(0.95, 1.05)
            total *= noise

            base_fare_final = round(total * 0.75, 2)
            taxes = round(total * 0.15 + random.uniform(200, 500), 2)
            total_final = round(base_fare_final + taxes, 2)

            departure_hour = random.choice([6, 8, 10, 13, 16, 19, 22])
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
                "total_fare": total_final,
                "source_platform": "mock",
            })

        return records

    def health_check(self) -> bool:
        return True
