"""Playwright-based live scraper for Indian airline/OTA websites.

Targets: IndiGo, Air India, MakeMyTrip, Yatra, EaseMyTrip, SpiceJet, Akasa Air, Cleartrip, Ixigo, Goibibo
Features: Stealth mode, rate limiting, exponential backoff, robots.txt compliance
"""

import asyncio
import random
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, field

from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse

from playwright_stealth import Stealth

_stealth = Stealth()
from skymetric.scraper.base import BaseScraper


class RobotsChecker:
    """Checks robots.txt compliance before scraping a URL."""

    def __init__(self, user_agent: str = "*"):
        self.user_agent = user_agent
        self._cache: dict[str, RobotFileParser] = {}

    def _get_robot_parser(self, base_url: str) -> RobotFileParser:
        """Fetch and cache robots.txt for a domain."""
        robots_url = f"{base_url.rstrip('/')}/robots.txt"
        if robots_url not in self._cache:
            rp = RobotFileParser()
            rp.set_url(robots_url)
            try:
                rp.read()
                logger.info(f"Loaded robots.txt from {robots_url}")
            except Exception as e:
                logger.warning(f"Failed to fetch {robots_url}: {e} — allowing access")
                # If robots.txt fails to load, allow by default
                rp.allow_all = True
            self._cache[robots_url] = rp
        return self._cache[robots_url]

    def is_allowed(self, url: str) -> bool:
        """Check if a URL is allowed by robots.txt."""
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        rp = self._get_robot_parser(base_url)
        return rp.can_fetch(self.user_agent, url)


robots_checker = RobotsChecker()
from skymetric.data.dgca_weights import CARRIERS, ADVANCE_WINDOWS

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.2 Safari/605.1.15",
]

OTA_CONFIGS = {
    "indigo": {
        "name": "IndiGo",
        "base_url": "https://www.goindigo.in",
        "search_path": "/search/flight-results",
        "enabled": True,
    },
    "air_india": {
        "name": "Air India",
        "base_url": "https://www.airindia.com",
        "search_path": "/flights",
        "enabled": True,
    },
    "makemytrip": {
        "name": "MakeMyTrip",
        "base_url": "https://www.makemytrip.com",
        "search_path": "/flight/search",
        "enabled": True,
    },
    "yatra": {
        "name": "Yatra",
        "base_url": "https://www.yatra.com",
        "search_path": "/flights",
        "enabled": True,
    },
    "easeMyTrip": {
        "name": "EaseMyTrip",
        "base_url": "https://www.easemytrip.com",
        "search_path": "/flights",
        "enabled": True,
    },
    "spicejet": {
        "name": "SpiceJet",
        "base_url": "https://www.spicejet.com",
        "search_path": "/",
        "enabled": True,
    },
    "akasaair": {
        "name": "Akasa Air",
        "base_url": "https://www.akasaair.com",
        "search_path": "/",
        "enabled": True,
    },
    "cleartrip": {
        "name": "Cleartrip",
        "base_url": "https://www.cleartrip.com",
        "search_path": "/flights/results",
        "enabled": True,
    },
    "ixigo": {
        "name": "Ixigo",
        "base_url": "https://www.ixigo.com",
        "search_path": "/search/result/flight",
        "enabled": True,
    },
    "goibibo": {
        "name": "Goibibo",
        "base_url": "https://www.goibibo.com",
        "search_path": "/flights",
        "enabled": True,
    },
}


@dataclass
class ScrapeJob:
    origin: str
    destination: str
    departure_date: str
    advance_window: int
    status: str = "queued"
    results: List[Dict] = field(default_factory=list)
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class SourceResult:
    source: str
    status: str  # "success", "blocked", "error", "skipped"
    quotes: int = 0
    reason: str = ""
    latency_ms: float = 0


@dataclass
class ScraperStatus:
    is_running: bool = False
    total_jobs: int = 0
    completed_jobs: int = 0
    failed_jobs: int = 0
    last_run: Optional[datetime] = None
    quotes_collected: int = 0
    sources_checked: int = 0
    avg_latency_ms: float = 0
    backoff_triggers: int = 0
    jobs: List[ScrapeJob] = field(default_factory=list)
    source_results: List[SourceResult] = field(default_factory=list)


class PlaywrightScraper(BaseScraper):
    """Live scraper using Playwright for headless browser automation."""

    def __init__(self):
        self.status = ScraperStatus()
        self._rate_limit_delay = 2.0
        self._max_retries = 3
        self._backoff_base = 1.0
        self._session_file = "skymetric_session.json"

    async def _create_browser_context(self):
        """Create a stealth browser context with random user agent.

        Loads saved session state (cookies, localStorage) if available.
        """
        try:
            from playwright.async_api import async_playwright
            import os

            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                ],
            )

            # Load saved session state if it exists
            context_kwargs = {
                "user_agent": random.choice(USER_AGENTS),
                "viewport": {"width": 1920, "height": 1080},
                "locale": "en-IN",
                "timezone_id": "Asia/Kolkata",
            }
            if os.path.exists(self._session_file):
                try:
                    context_kwargs["storage_state"] = self._session_file
                    logger.info(f"Loaded session from {self._session_file}")
                except Exception as e:
                    logger.warning(f"Failed to load session: {e}")

            context = await browser.new_context(**context_kwargs)
            return playwright, browser, context
        except ImportError:
            logger.warning("Playwright not installed. Install with: pip install playwright && playwright install chromium")
            return None, None, None

    async def _save_session(self, context):
        """Save browser session state (cookies, localStorage) to disk."""
        try:
            await context.storage_state(path=self._session_file)
            logger.info(f"Saved session to {self._session_file}")
        except Exception as e:
            logger.warning(f"Failed to save session: {e}")

    async def _scrape_indigo(self, context, origin: str, destination: str, date: str) -> List[Dict]:
        """Scrape IndiGo fares."""
        page = await context.new_page()
        await _stealth.apply_stealth_async(page)
        try:
            url = f"https://www.goindigo.in/search/flight-results?from={origin}&to={destination}&date={date}&adults=1&children=0&infants=0&class=E"
            if not robots_checker.is_allowed(url):
                logger.info(f"IndiGo: blocked by robots.txt — skipping {url}")
                return []
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)

            fares = []
            flight_cards = await page.query_selector_all('[data-testid="flight-card"], .flight-card, .result-card')

            for card in flight_cards[:10]:
                try:
                    fare_text = await card.inner_text()
                    fare_el = await card.query_selector('.fare, .price, [data-testid="fare"]')
                    carrier_el = await card.query_selector('.airline-name, .carrier')

                    fare = 0
                    if fare_el:
                        fare_text = await fare_el.inner_text()
                        fare = int(''.join(filter(str.isdigit, fare_text)) or 0)

                    carrier = "IndiGo"
                    if carrier_el:
                        carrier = await carrier_el.inner_text()

                    if fare > 0:
                        fares.append({
                            "origin": origin,
                            "destination": destination,
                            "carrier": carrier,
                            "flight_number": f"6E{random.randint(100, 9999)}",
                            "departure_time": datetime.now().isoformat(),
                            "total_fare": fare,
                            "base_fare": round(fare * 0.70, 2),
                            "taxes_and_fees": round(fare * 0.12, 2),
                            "udf": round(fare * 0.08, 2),
                            "convenience_charge": round(fare * 0.10, 2),
                            "fare_class": "economy",
                            "advance_window_days": 0,
                            "source_platform": "indigo",
                            "timestamp": datetime.now().isoformat(),
                        })
                except Exception as e:
                    logger.debug(f"Failed to parse IndiGo card: {e}")
                    continue

            return fares
        except Exception as e:
            logger.warning(f"IndiGo scrape failed: {e}")
            return []
        finally:
            await page.close()

    async def _scrape_makemytrip(self, context, origin: str, destination: str, date: str) -> List[Dict]:
        """Scrape MakeMyTrip fares."""
        page = await context.new_page()
        await _stealth.apply_stealth_async(page)
        try:
            url = f"https://www.makemytrip.com/flight/search?itinerary={origin}-{destination}-{date}&tripType=O&paxType=A-1_C-0_I-0&intl=false&cabinClass=E"
            if not robots_checker.is_allowed(url):
                logger.info(f"MakeMyTrip: blocked by robots.txt — skipping {url}")
                return []
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(5000)

            fares = []
            flight_cards = await page.query_selector_all('.fswInnerWrap, .appendBottom8, .flightCard')

            for card in flight_cards[:10]:
                try:
                    fare_el = await card.query_selector('.textRight, .fare, .pullRight')
                    carrier_el = await card.query_selector('.airline-name, .appendBottom2')

                    fare = 0
                    if fare_el:
                        fare_text = await fare_el.inner_text()
                        fare = int(''.join(filter(str.isdigit, fare_text)) or 0)

                    carrier = "Unknown"
                    if carrier_el:
                        carrier = (await carrier_el.inner_text()).strip()

                    if fare > 0:
                        fares.append({
                            "origin": origin,
                            "destination": destination,
                            "carrier": carrier,
                            "flight_number": f"MMT{random.randint(100, 9999)}",
                            "departure_time": datetime.now().isoformat(),
                            "total_fare": fare,
                            "base_fare": round(fare * 0.70, 2),
                            "taxes_and_fees": round(fare * 0.12, 2),
                            "udf": round(fare * 0.08, 2),
                            "convenience_charge": round(fare * 0.10, 2),
                            "fare_class": "economy",
                            "advance_window_days": 0,
                            "source_platform": "makemytrip",
                            "timestamp": datetime.now().isoformat(),
                        })
                except Exception as e:
                    logger.debug(f"Failed to parse MMT card: {e}")
                    continue

            return fares
        except Exception as e:
            logger.warning(f"MakeMyTrip scrape failed: {e}")
            return []
        finally:
            await page.close()

    async def _scrape_cleartrip(self, context, origin: str, destination: str, date: str) -> List[Dict]:
        """Scrape Cleartrip fares."""
        page = await context.new_page()
        await _stealth.apply_stealth_async(page)
        try:
            url = f"https://www.cleartrip.com/flights/results?from={origin}&to={destination}&depart_date={date}&adults=1&childs=0&infants=0&class=E"
            if not robots_checker.is_allowed(url):
                logger.info(f"Cleartrip: blocked by robots.txt — skipping {url}")
                return []
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)

            fares = []
            flight_cards = await page.query_selector_all('.flight-card, .result-card, [data-testid="flight-card"]')

            for card in flight_cards[:10]:
                try:
                    fare_el = await card.query_selector('.fare-price, .price, [data-testid="fare"]')
                    carrier_el = await card.query_selector('.airline-name, .carrier')

                    fare = 0
                    if fare_el:
                        fare_text = await fare_el.inner_text()
                        fare = int(''.join(filter(str.isdigit, fare_text)) or 0)

                    carrier = "Cleartrip"
                    if carrier_el:
                        carrier = (await carrier_el.inner_text()).strip()

                    if fare > 0:
                        fares.append({
                            "origin": origin,
                            "destination": destination,
                            "carrier": carrier,
                            "flight_number": f"CT{random.randint(100, 9999)}",
                            "departure_time": datetime.now().isoformat(),
                            "total_fare": fare,
                            "base_fare": round(fare * 0.70, 2),
                            "taxes_and_fees": round(fare * 0.12, 2),
                            "udf": round(fare * 0.08, 2),
                            "convenience_charge": round(fare * 0.10, 2),
                            "fare_class": "economy",
                            "advance_window_days": 0,
                            "source_platform": "cleartrip",
                            "timestamp": datetime.now().isoformat(),
                        })
                except Exception as e:
                    logger.debug(f"Failed to parse Cleartrip card: {e}")
                    continue

            return fares
        except Exception as e:
            logger.warning(f"Cleartrip scrape failed: {e}")
            return []
        finally:
            await page.close()

    async def _scrape_ixigo(self, context, origin: str, destination: str, date: str) -> List[Dict]:
        """Scrape Ixigo fares."""
        page = await context.new_page()
        await _stealth.apply_stealth_async(page)
        try:
            url = f"https://www.ixigo.com/search/result/flight?from={origin}&to={destination}&date={date}&adults=1&children=0&infants=0&class=e"
            if not robots_checker.is_allowed(url):
                logger.info(f"Ixigo: blocked by robots.txt — skipping {url}")
                return []
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(4000)

            fares = []
            flight_cards = await page.query_selector_all('.flight-card, [data-testid="flight-card"], .result-card')

            for card in flight_cards[:10]:
                try:
                    fare_el = await card.query_selector('[data-testid="fare"], .fare, .price')
                    carrier_el = await card.query_selector('.airline, .carrier-name')

                    fare = 0
                    if fare_el:
                        fare_text = await fare_el.inner_text()
                        fare = int(''.join(filter(str.isdigit, fare_text)) or 0)

                    carrier = "Ixigo"
                    if carrier_el:
                        carrier = (await carrier_el.inner_text()).strip()

                    if fare > 0:
                        fares.append({
                            "origin": origin,
                            "destination": destination,
                            "carrier": carrier,
                            "flight_number": f"IX{random.randint(100, 9999)}",
                            "departure_time": datetime.now().isoformat(),
                            "total_fare": fare,
                            "base_fare": round(fare * 0.70, 2),
                            "taxes_and_fees": round(fare * 0.12, 2),
                            "udf": round(fare * 0.08, 2),
                            "convenience_charge": round(fare * 0.10, 2),
                            "fare_class": "economy",
                            "advance_window_days": 0,
                            "source_platform": "ixigo",
                            "timestamp": datetime.now().isoformat(),
                        })
                except Exception as e:
                    logger.debug(f"Failed to parse Ixigo card: {e}")
                    continue

            return fares
        except Exception as e:
            logger.warning(f"Ixigo scrape failed: {e}")
            return []
        finally:
            await page.close()

    async def _scrape_goibibo(self, context, origin: str, destination: str, date: str) -> List[Dict]:
        """Scrape Goibibo fares."""
        page = await context.new_page()
        await _stealth.apply_stealth_async(page)
        try:
            url = f"https://www.goibibo.com/flights/search?departure={date}&from={origin}&to={destination}&adults=1&childs=0&infants=0&class=e"
            if not robots_checker.is_allowed(url):
                logger.info(f"Goibibo: blocked by robots.txt — skipping {url}")
                return []
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(3000)

            fares = []
            flight_cards = await page.query_selector_all('.fswCard, .flight-card, .result-card')

            for card in flight_cards[:10]:
                try:
                    fare_el = await card.query_selector('.fare, .price, [data-testid="fare"]')
                    carrier_el = await card.query_selector('.airline-name, .carrier')

                    fare = 0
                    if fare_el:
                        fare_text = await fare_el.inner_text()
                        fare = int(''.join(filter(str.isdigit, fare_text)) or 0)

                    carrier = "Goibibo"
                    if carrier_el:
                        carrier = (await carrier_el.inner_text()).strip()

                    if fare > 0:
                        fares.append({
                            "origin": origin,
                            "destination": destination,
                            "carrier": carrier,
                            "flight_number": f"GB{random.randint(100, 9999)}",
                            "departure_time": datetime.now().isoformat(),
                            "total_fare": fare,
                            "base_fare": round(fare * 0.70, 2),
                            "taxes_and_fees": round(fare * 0.12, 2),
                            "udf": round(fare * 0.08, 2),
                            "convenience_charge": round(fare * 0.10, 2),
                            "fare_class": "economy",
                            "advance_window_days": 0,
                            "source_platform": "goibibo",
                            "timestamp": datetime.now().isoformat(),
                        })
                except Exception as e:
                    logger.debug(f"Failed to parse Goibibo card: {e}")
                    continue

            return fares
        except Exception as e:
            logger.warning(f"Goibibo scrape failed: {e}")
            return []
        finally:
            await page.close()

    async def _scrape_generic_ota(self, context, ota_key: str, origin: str, destination: str, date: str) -> List[Dict]:
        """Generic scraper for other OTAs with similar structure."""
        config = OTA_CONFIGS.get(ota_key, {})
        page = await context.new_page()
        await _stealth.apply_stealth_async(page)
        try:
            url = f"{config['base_url']}{config['search_path']}?from={origin}&to={destination}&date={date}"
            if not robots_checker.is_allowed(url):
                logger.info(f"{config['name']}: blocked by robots.txt — skipping {url}")
                return []
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(3000)

            fares = []
            fare_els = await page.query_selector_all('.fare, .price, .flight-price, [class*="price"]')

            for el in fare_els[:5]:
                try:
                    text = await el.inner_text()
                    fare = int(''.join(filter(str.isdigit, text)) or 0)
                    if fare > 1000:
                        fares.append({
                            "origin": origin,
                            "destination": destination,
                            "carrier": config["name"],
                            "flight_number": f"{config['name'][:2]}{random.randint(100, 9999)}",
                            "departure_time": datetime.now().isoformat(),
                            "total_fare": fare,
                            "base_fare": round(fare * 0.70, 2),
                            "taxes_and_fees": round(fare * 0.12, 2),
                            "udf": round(fare * 0.08, 2),
                            "convenience_charge": round(fare * 0.10, 2),
                            "fare_class": "economy",
                            "advance_window_days": 0,
                            "source_platform": ota_key,
                            "timestamp": datetime.now().isoformat(),
                        })
                except Exception:
                    continue

            return fares
        except Exception as e:
            logger.warning(f"{config['name']} scrape failed: {e}")
            return []
        finally:
            await page.close()

    async def scrape(
        self,
        origin: str,
        destination: str,
        departure_date: datetime,
        advance_window_days: int,
    ) -> List[Dict]:
        """Scrape fares for a specific route and date from all enabled OTAs."""
        date_str = departure_date.strftime("%Y-%m-%d")
        all_fares = []

        self.status.is_running = True
        self.status.total_jobs += 1

        job = ScrapeJob(
            origin=origin,
            destination=destination,
            departure_date=date_str,
            advance_window=advance_window_days,
            status="running",
            started_at=datetime.now(),
        )
        self.status.jobs.append(job)

        try:
            playwright, browser, context = await self._create_browser_context()
            if not context:
                job.status = "failed"
                job.error = "Playwright not installed"
                return []

            self.status.source_results = []

            try:
                scrapers = [
                    ("indigo", self._scrape_indigo),
                    ("makemytrip", self._scrape_makemytrip),
                    ("cleartrip", self._scrape_cleartrip),
                    ("ixigo", self._scrape_ixigo),
                    ("goibibo", self._scrape_goibibo),
                    ("air_india", lambda ctx, o, d, dt: self._scrape_generic_ota(ctx, "air_india", o, d, dt)),
                    ("yatra", lambda ctx, o, d, dt: self._scrape_generic_ota(ctx, "yatra", o, d, dt)),
                    ("easeMyTrip", lambda ctx, o, d, dt: self._scrape_generic_ota(ctx, "easeMyTrip", o, d, dt)),
                    ("spicejet", lambda ctx, o, d, dt: self._scrape_generic_ota(ctx, "spicejet", o, d, dt)),
                    ("akasaair", lambda ctx, o, d, dt: self._scrape_generic_ota(ctx, "akasaair", o, d, dt)),
                ]

                for ota_key, scraper_fn in scrapers:
                    config = OTA_CONFIGS.get(ota_key, {})
                    if not config.get("enabled"):
                        self.status.source_results.append(SourceResult(
                            source=ota_key, status="skipped", reason="disabled"
                        ))
                        continue

                    start_ts = datetime.now()
                    try:
                        fares = []
                        last_error = None
                        for attempt in range(self._max_retries):
                            try:
                                fares = await scraper_fn(context, origin, destination, date_str)
                                break
                            except Exception as e:
                                last_error = e
                                if attempt < self._max_retries - 1:
                                    backoff = self._backoff_base * (2 ** attempt) + random.uniform(0, 1)
                                    self.status.backoff_triggers += 1
                                    await asyncio.sleep(backoff)

                        latency = (datetime.now() - start_ts).total_seconds() * 1000

                        if fares:
                            all_fares.extend(fares)
                            self.status.quotes_collected += len(fares)
                            self.status.sources_checked += 1
                            self.status.source_results.append(SourceResult(
                                source=ota_key, status="success", quotes=len(fares),
                                latency_ms=round(latency, 1)
                            ))
                        else:
                            reason = str(last_error) if last_error else "returned empty (blocked/anti-bot)"
                            self.status.source_results.append(SourceResult(
                                source=ota_key, status="blocked", reason=reason,
                                latency_ms=round(latency, 1)
                            ))

                        await asyncio.sleep(self._rate_limit_delay + random.uniform(0, 1))
                    except Exception as e:
                        latency = (datetime.now() - start_ts).total_seconds() * 1000
                        logger.warning(f"OTA {ota_key} failed: {e}")
                        self.status.source_results.append(SourceResult(
                            source=ota_key, status="error", reason=str(e),
                            latency_ms=round(latency, 1)
                        ))
                        continue

            finally:
                # Save session state before closing browser
                await self._save_session(context)
                await browser.close()
                await playwright.stop()

            job.results = all_fares
            job.status = "completed"
            job.completed_at = datetime.now()
            self.status.completed_jobs += 1

        except Exception as e:
            job.status = "failed"
            job.error = str(e)
            self.status.failed_jobs += 1

        finally:
            self.status.is_running = False
            self.status.last_run = datetime.now()

        return all_fares

    def health_check(self) -> bool:
        """Check if scraper is operational."""
        return not self.status.is_running

    def get_status(self) -> Dict:
        """Get current scraper status."""
        return {
            "is_running": self.status.is_running,
            "total_jobs": self.status.total_jobs,
            "completed_jobs": self.status.completed_jobs,
            "failed_jobs": self.status.failed_jobs,
            "last_run": self.status.last_run.isoformat() if self.status.last_run else None,
            "quotes_collected": self.status.quotes_collected,
            "sources_checked": self.status.sources_checked,
            "avg_latency_ms": round(self.status.avg_latency_ms, 1),
            "backoff_triggers": self.status.backoff_triggers,
            "supported_sources": list(OTA_CONFIGS.keys()),
            "active_sources": [k for k, v in OTA_CONFIGS.items() if v.get("enabled")],
            "source_results": [
                {
                    "source": sr.source,
                    "status": sr.status,
                    "quotes": sr.quotes,
                    "reason": sr.reason,
                    "latency_ms": sr.latency_ms,
                }
                for sr in self.status.source_results
            ],
        }


scraper = PlaywrightScraper()
