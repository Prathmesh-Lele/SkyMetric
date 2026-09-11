"""Base scraper adapter interface."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict


class BaseScraper(ABC):
    """Abstract base class for all fare scrapers."""

    @abstractmethod
    def scrape(
        self,
        origin: str,
        destination: str,
        departure_date: datetime,
        advance_window_days: int,
    ) -> List[Dict]:
        """Scrape fares for a specific route and date."""
        ...

    @abstractmethod
    def health_check(self) -> bool:
        """Return True if scraper is operational."""
        ...
