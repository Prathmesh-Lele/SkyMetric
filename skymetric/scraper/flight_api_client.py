"""Flight API client with 3-tier fallback: fli -> SerpApi -> MockScraper.

Tier 1: fli library (Google Flights data, no API key, unlimited)
Tier 2: SerpApi (Google Flights data, 100-250 searches/month, needs API key)
Tier 3: MockScraper (synthetic data, always available)
"""

import asyncio
import logging
import os
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

try:
    from skymetric.config.settings import settings
    SERPAPI_KEY = settings.SERPAPI_KEY
except Exception:
    SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")

CARRIER_CODES = {
    "IndiGo": "6E",
    "Air India": "AI",
    "Vistara": "UK",
    "SpiceJet": "SG",
    "Akasa Air": "QP",
    "Air India Express": "IX",
}

CARRIER_BY_CODE = {v: k for k, v in CARRIER_CODES.items()}


def _build_fare_record(
    origin: str,
    destination: str,
    carrier: str,
    flight_number: str,
    departure_time: str,
    total_fare: float,
    advance_window_days: int,
    source_platform: str,
) -> Dict:
    """Build a fare record in SkyMetric format."""
    base = round(total_fare * 0.70, 2)
    taxes = round(total_fare * 0.12, 2)
    udf = round(total_fare * 0.08, 2)
    conv = round(total_fare * 0.10, 2)
    return {
        "origin": origin,
        "destination": destination,
        "carrier": carrier,
        "flight_number": flight_number,
        "departure_time": departure_time,
        "total_fare": round(total_fare, 2),
        "base_fare": base,
        "taxes_and_fees": taxes,
        "udf": udf,
        "convenience_charge": conv,
        "fare_class": "economy",
        "advance_window_days": advance_window_days,
        "source_platform": source_platform,
        "timestamp": datetime.now().isoformat(),
    }


async def _search_fli(
    origin: str,
    destination: str,
    date_str: str,
    advance_window_days: int,
) -> List[Dict]:
    """Tier 1: Use fli library for Google Flights data."""
    try:
        from fli import search_flights
    except ImportError:
        logger.debug("fli not installed — skipping Tier 1")
        return []

    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(
        None,
        lambda: search_flights(
            origin=origin,
            destination=destination,
            date=date_str,
            country="IN",
            currency="INR",
            format="json",
        ),
    )

    if not results:
        return []

    fares = []
    for flight in results if isinstance(results, list) else results.get("flights", []):
        try:
            price = flight.get("price") or flight.get("total_price") or 0
            if price <= 0:
                continue
            carrier = flight.get("airline") or flight.get("carrier") or "Unknown"
            flight_no = flight.get("flight_number") or flight.get("flightNumber") or ""
            departure = flight.get("departure_time") or flight.get("departure") or ""

            fares.append(
                _build_fare_record(
                    origin=origin,
                    destination=destination,
                    carrier=carrier,
                    flight_number=flight_no,
                    departure_time=departure,
                    total_fare=float(price),
                    advance_window_days=advance_window_days,
                    source_platform="fli",
                )
            )
        except Exception as e:
            logger.debug(f"Failed to parse fli flight: {e}")
            continue

    if fares:
        logger.info(f"fli returned {len(fares)} fares for {origin}-{destination}")
    return fares


async def _search_serpapi(
    origin: str,
    destination: str,
    date_str: str,
    advance_window_days: int,
) -> List[Dict]:
    """Tier 2: Use SerpApi for Google Flights data."""
    if not SERPAPI_KEY:
        logger.debug("SERPAPI_KEY not set — skipping Tier 2")
        return []

    import httpx

    params = {
        "engine": "google_flights",
        "departure_id": origin,
        "arrival_id": destination,
        "outbound_date": date_str,
        "currency": "INR",
        "gl": "in",
        "hl": "en",
        "api_key": SERPAPI_KEY,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get("https://serpapi.com/search", params=params)
        resp.raise_for_status()
        data = resp.json()

    best_flights = data.get("best_flights", []) + data.get("other_flights", [])
    if not best_flights:
        return []

    fares = []
    for flight in best_flights:
        try:
            price = flight.get("price") or 0
            if price <= 0:
                continue

            airline_info = flight.get("flights", [{}])[0] if flight.get("flights") else {}
            carrier = airline_info.get("airline") or "Unknown"
            flight_no_raw = airline_info.get("flight_number") or ""
            departure = airline_info.get("departure_airport", {}).get("time") or ""

            flight_number = flight_no_raw
            if not flight_number.startswith(("6E", "AI", "UK", "SG", "QP", "IX")):
                flight_number = f"{flight_no_raw}"

            fares.append(
                _build_fare_record(
                    origin=origin,
                    destination=destination,
                    carrier=carrier,
                    flight_number=flight_number,
                    departure_time=departure,
                    total_fare=float(price),
                    advance_window_days=advance_window_days,
                    source_platform="serpapi",
                )
            )
        except Exception as e:
            logger.debug(f"Failed to parse SerpApi flight: {e}")
            continue

    if fares:
        logger.info(f"SerpApi returned {len(fares)} fares for {origin}-{destination}")
    return fares


async def _search_mock(
    origin: str,
    destination: str,
    departure_date: datetime,
    advance_window_days: int,
) -> List[Dict]:
    """Tier 3: Use MockScraper for synthetic data."""
    from skymetric.scraper.mock_scraper import MockScraper

    mock = MockScraper()
    loop = asyncio.get_event_loop()
    fares = await loop.run_in_executor(
        None, lambda: mock.scrape(origin, destination, departure_date, advance_window_days)
    )
    for f in fares:
        f["source_platform"] = "mock"
    logger.info(f"MockScraper returned {len(fares)} fares for {origin}-{destination}")
    return fares


class FlightApiClient:
    """3-tier fallback flight data client: fli -> SerpApi -> MockScraper."""

    def __init__(self):
        self._last_source: Optional[str] = None

    async def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: datetime,
        advance_window_days: int,
    ) -> Tuple[List[Dict], str]:
        """Search flights with 3-tier fallback.

        Returns:
            Tuple of (fares list, source tier name)
        """
        date_str = departure_date.strftime("%Y-%m-%d")

        # Tier 1: fli
        try:
            fares = await _search_fli(origin, destination, date_str, advance_window_days)
            if fares:
                self._last_source = "fli"
                return fares, "fli"
        except Exception as e:
            logger.warning(f"fli failed (Tier 1): {e}")

        # Tier 2: SerpApi
        try:
            fares = await _search_serpapi(origin, destination, date_str, advance_window_days)
            if fares:
                self._last_source = "serpapi"
                return fares, "serpapi"
        except Exception as e:
            logger.warning(f"SerpApi failed (Tier 2): {e}")

        # Tier 3: MockScraper
        try:
            fares = await _search_mock(origin, destination, departure_date, advance_window_days)
            self._last_source = "mock"
            return fares, "mock"
        except Exception as e:
            logger.error(f"MockScraper failed (Tier 3): {e}")
            return [], "none"

    def get_last_source(self) -> Optional[str]:
        return self._last_source


flight_api_client = FlightApiClient()
