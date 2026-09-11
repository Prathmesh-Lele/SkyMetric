"""Tests for the scraping engine."""

from datetime import datetime
from skymetric.scraper.mock_scraper import MockScraper
from skymetric.scraper.base import BaseScraper


class TestMockScraper:
    def test_returns_list(self):
        scraper = MockScraper()
        result = scraper.scrape("DEL", "BOM", datetime.utcnow(), 15)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_record_structure(self):
        scraper = MockScraper()
        records = scraper.scrape("DEL", "BOM", datetime.utcnow(), 15)
        for r in records:
            assert "origin" in r
            assert "destination" in r
            assert "carrier" in r
            assert "total_fare" in r
            assert "base_fare" in r
            assert "taxes_and_fees" in r
            assert r["origin"] == "DEL"
            assert r["destination"] == "BOM"

    def test_all_carriers_represented(self):
        scraper = MockScraper()
        records = scraper.scrape("DEL", "BOM", datetime.utcnow(), 15)
        carriers = {r["carrier"] for r in records}
        assert len(carriers) == 6

    def test_health_check(self):
        scraper = MockScraper()
        assert scraper.health_check() is True

    def test_advance_window_applied(self):
        scraper = MockScraper()
        t1 = scraper.scrape("DEL", "BOM", datetime.utcnow(), 1)
        t45 = scraper.scrape("DEL", "BOM", datetime.utcnow(), 45)
        avg_t1 = sum(r["total_fare"] for r in t1) / len(t1)
        avg_t45 = sum(r["total_fare"] for r in t45) / len(t45)
        assert avg_t1 > avg_t45

    def test_is_base_scraper(self):
        assert issubclass(MockScraper, BaseScraper)
