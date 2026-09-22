"""Flight API client with 2-tier fallback: SerpApi -> MockScraper.

Tier 1: SerpApi (Google Flights live data, needs SERPAPI_KEY)
Tier 2: MockScraper (synthetic, always available)
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

CARRIER_CODES = {
    "IndiGo": "6E",
    "Air India": "AI",
    "Vistara": "UK",
    "SpiceJet": "SG",
    "Akasa Air": "QP",
    "Air India Express": "IX",
}

CARRIER_BY_CODE = {v: k for k, v in CARRIER_CODES.items()}


def _get_serpapi_key() -> str:
    """Read SerpApi key from settings/env at call time (never cache empty)."""
    try:
        from skymetric.config.settings import settings

        key = (settings.SERPAPI_KEY or "").strip()
        if key:
            return key
    except Exception as exc:
        logger.debug(f"settings load failed for SERPAPI_KEY: {exc}")
    return (os.getenv("SERPAPI_KEY") or "").strip()


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
        "timestamp": datetime.now(),
    }


async def _search_serpapi(
    origin: str,
    destination: str,
    date_str: str,
    advance_window_days: int,
) -> List[Dict]:
    """Tier 1: Live Google Flights data via SerpApi (one-way)."""
    api_key = _get_serpapi_key()
    if not api_key:
        logger.debug("SERPAPI_KEY not set — skipping Tier 1 (SerpApi)")
        return []

    import httpx

    params = {
        "engine": "google_flights",
        "departure_id": origin,
        "arrival_id": destination,
        "outbound_date": date_str,
        "type": "2",  # one-way
        "currency": "INR",
        "gl": "in",
        "hl": "en",
        "api_key": api_key,
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get("https://serpapi.com/search", params=params)
        if resp.status_code != 200:
            logger.warning(f"SerpApi HTTP {resp.status_code}: {resp.text[:200]}")
            return []
        data = resp.json()

    if data.get("error"):
        logger.warning(f"SerpApi error: {data['error']}")
        return []

    best_flights = data.get("best_flights", []) + data.get("other_flights", [])
    if not best_flights:
        logger.info(f"SerpApi returned 0 flights for {origin}-{destination} {date_str}")
        return []

    fares = []
    for flight in best_flights:
        try:
            price = flight.get("price") or 0
            if price <= 0:
                continue

            airline_info = flight.get("flights", [{}])[0] if flight.get("flights") else {}
            carrier = airline_info.get("airline") or "Unknown"
            flight_number = airline_info.get("flight_number") or ""
            departure = airline_info.get("departure_airport", {}).get("time") or ""

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
        logger.info(f"SerpApi LIVE returned {len(fares)} fares for {origin}-{destination}")
    return fares


async def _search_mock(
    origin: str,
    destination: str,
    departure_date: datetime,
    advance_window_days: int,
) -> List[Dict]:
    """Tier 2: MockScraper for synthetic fallback data."""
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
    """2-tier fallback flight data client: SerpApi -> MockScraper."""

    def __init__(self):
        self._last_source: Optional[str] = None
        self._last_count: int = 0

    @property
    def live_enabled(self) -> bool:
        return bool(_get_serpapi_key())

    async def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: datetime,
        advance_window_days: int,
        prefer_live: bool = True,
    ) -> Tuple[List[Dict], str]:
        """Search flights. Returns (fares, source) where source is serpapi|mock|none."""
        date_str = departure_date.strftime("%Y-%m-%d")

        if prefer_live and self.live_enabled:
            try:
                fares = await _search_serpapi(
                    origin, destination, date_str, advance_window_days
                )
                if fares:
                    self._last_source = "serpapi"
                    self._last_count = len(fares)
                    return fares, "serpapi"
            except Exception as e:
                logger.warning(f"SerpApi failed (Tier 1): {e}")

        try:
            fares = await _search_mock(
                origin, destination, departure_date, advance_window_days
            )
            self._last_source = "mock"
            self._last_count = len(fares)
            return fares, "mock"
        except Exception as e:
            logger.error(f"MockScraper failed (Tier 2): {e}")
            return [], "none"

    def get_last_source(self) -> Optional[str]:
        return self._last_source


flight_api_client = FlightApiClient()
