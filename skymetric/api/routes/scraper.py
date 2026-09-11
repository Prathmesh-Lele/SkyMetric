"""Scraper control API endpoints."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks

from skymetric.scraper.playwright_scraper import scraper

router = APIRouter()


@router.get("/status")
def get_scraper_status():
    """Get current scraper status and metrics."""
    return scraper.get_status()


@router.post("/run")
async def run_scraper(
    background_tasks: BackgroundTasks,
    origin: Optional[str] = None,
    destination: Optional[str] = None,
    date: Optional[str] = None,
):
    """Trigger an ad-hoc scraper run."""
    if scraper.status.is_running:
        return {"error": "Scraper is already running", "status": scraper.get_status()}

    async def _run():
        from datetime import date as date_type
        target_date = datetime.strptime(date, "%Y-%m-%d").date() if date else date_type.today()
        origin_val = origin or "DEL"
        dest_val = destination or "BOM"
        await scraper.scrape(origin_val, dest_val, datetime.combine(target_date, datetime.min.time()), 1)

    background_tasks.add_task(_run)

    return {
        "message": "Scraper run triggered",
        "origin": origin or "DEL",
        "destination": destination or "BOM",
        "date": date or datetime.now().strftime("%Y-%m-%d"),
        "status": scraper.get_status(),
    }


@router.get("/health")
def scraper_health():
    """Check scraper health."""
    return {
        "healthy": scraper.health_check(),
        "is_running": scraper.status.is_running,
        "last_run": scraper.status.last_run.isoformat() if scraper.status.last_run else None,
    }
