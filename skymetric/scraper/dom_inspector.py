"""DOM Inspector — Diagnostic tool to discover real CSS selectors for each OTA.

Run this tool to inspect the actual page structure of each source and find
the correct selectors for fare elements, flight cards, and carrier names.

Usage:
    python -m skymetric.scraper.dom_inspector
    python -m skymetric.scraper.dom_inspector --source makemytrip
    python -m skymetric.scraper.dom_inspector --source all --origin DEL --destination BOM
"""

import asyncio
import json
import os
import re
import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

OUTPUT_DIR = "dom_inspection_results"

SOURCES = {
    "indigo": {
        "name": "IndiGo",
        "url_template": "https://www.goindigo.in/search/flight-results?from={origin}&to={dest}&date={date}&adults=1&children=0&infants=0&class=E",
        "date_format": "%d-%m-%Y",
    },
    "makemytrip": {
        "name": "MakeMyTrip",
        "url_template": "https://www.makemytrip.com/flight/search?itinerary={origin}-{dest}-{date}&tripType=O&paxType=A-1_C-0_I-0&intl=false&cabinClass=E",
        "date_format": "%d/%m/%Y",
    },
    "cleartrip": {
        "name": "Cleartrip",
        "url_template": "https://www.cleartrip.com/flights/results?adults=1&childs=0&infants=0&depart_date={date}&from={origin}&to={dest}&intl=n&sd=0&page=1&sort=price_a&class=E",
        "date_format": "%d/%m/%Y",
    },
    "ixigo": {
        "name": "Ixigo",
        "url_template": "https://www.ixigo.com/search/result/flight?from={origin}&to={dest}&date={date}&adults=1&children=0&infants=0&class=e&source=Search+Form",
        "date_format": "%d%m%Y",
    },
    "goibibo": {
        "name": "Goibibo",
        "url_template": "https://www.goibibo.com/flight/search?itinerary={origin}-{dest}-{date}&tripType=O&paxType=A-1_C-0_I-0&cabinClass=E",
        "date_format": "%d/%m/%Y",
    },
    "yatra": {
        "name": "Yatra",
        "url_template": "https://www.yatra.com/flights/air/city?from={origin}&to={dest}&departDate={date}&adult=1&child=0&infant=0&class=economy",
        "date_format": "%d-%m-%Y",
    },
    "easemytrip": {
        "name": "EaseMyTrip",
        "url_template": "https://www.easemytrip.com/flights/search/result?origin={origin}&destination={dest}&departdate={date}&adults=1&childs=0&infants=0&class=economy&tripType=O",
        "date_format": "%d-%m-%Y",
    },
    "spicejet": {
        "name": "SpiceJet",
        "url_template": "https://www.spicejet.com/",
        "date_format": "%Y-%m-%d",
    },
    "akasaair": {
        "name": "Akasa Air",
        "url_template": "https://www.akasaair.com/",
        "date_format": "%Y-%m-%d",
    },
    "air_india": {
        "name": "Air India",
        "url_template": "https://www.airindia.com/in/en/book/search-flights.html",
        "date_format": "%Y-%m-%d",
    },
}


async def inspect_source(
    source_key: str,
    origin: str = "DEL",
    destination: str = "BOM",
    wait_ms: int = 8000,
):
    """Inspect a single OTA source — capture screenshot, HTML, and element analysis."""
    config = SOURCES.get(source_key)
    if not config:
        print(f"Unknown source: {source_key}")
        return

    print(f"\n{'='*60}")
    print(f"Inspecting: {config['name']} ({source_key})")
    print(f"{'='*60}")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("Playwright not installed. Run: pip install playwright && playwright install chromium")
        return

    departure_date = datetime.now() + timedelta(days=15)
    date_str = departure_date.strftime(config["date_format"])
    url = config["url_template"].format(origin=origin, dest=destination, date=date_str)

    print(f"URL: {url}")
    print(f"Date string: {date_str}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            locale="en-IN",
            timezone_id="Asia/Kolkata",
        )
        page = await context.new_page()

        try:
            print("Navigating...")
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(wait_ms)

            # Screenshot
            screenshot_path = os.path.join(OUTPUT_DIR, f"{source_key}_screenshot.png")
            await page.screenshot(path=screenshot_path, full_page=True)
            print(f"Screenshot saved: {screenshot_path}")

            # Save HTML
            html_path = os.path.join(OUTPUT_DIR, f"{source_key}_page.html")
            html = await page.content()
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"HTML saved: {html_path} ({len(html)} chars)")

            # Analyze elements
            analysis = await _analyze_page(page, source_key)
            analysis_path = os.path.join(OUTPUT_DIR, f"{source_key}_analysis.json")
            with open(analysis_path, "w", encoding="utf-8") as f:
                json.dump(analysis, f, indent=2, default=str)
            print(f"Analysis saved: {analysis_path}")

            # Print summary
            print(f"\n--- Analysis for {config['name']} ---")
            print(f"Page title: {analysis['page_title']}")
            print(f"Total elements: {analysis['total_elements']}")
            print(f"Price-like elements: {analysis['price_elements_count']}")
            print(f"Airline-like elements: {analysis['airline_elements_count']}")
            if analysis["price_elements"]:
                print(f"\nTop price elements:")
                for i, el in enumerate(analysis["price_elements"][:10]):
                    print(f"  {i+1}. tag={el['tag']} class={el['class']} text={el['text'][:50]}")
            if analysis["airline_elements"]:
                print(f"\nTop airline elements:")
                for i, el in enumerate(analysis["airline_elements"][:10]):
                    print(f"  {i+1}. tag={el['tag']} class={el['class']} text={el['text'][:50]}")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()


async def _analyze_page(page, source_key: str) -> dict:
    """Analyze page DOM to find price and airline elements."""
    result = {
        "source": source_key,
        "page_title": await page.title(),
        "url": page.url,
        "total_elements": 0,
        "price_elements_count": 0,
        "airline_elements_count": 0,
        "price_elements": [],
        "airline_elements": [],
        "all_classes_with_price": [],
        "all_classes_with_airline": [],
    }

    # Count all elements
    all_elements = await page.query_selector_all("*")
    result["total_elements"] = len(all_elements)

    # Find price-like elements (contain ₹ or numbers > 1000)
    price_els = await page.query_selector_all('[class*="price"], [class*="fare"], [class*="cost"], [class*="amount"]')
    result["price_elements_count"] = len(price_els)
    for el in price_els[:20]:
        try:
            text = (await el.inner_text()).strip()
            tag = await el.evaluate("el => el.tagName.toLowerCase()")
            cls = await el.evaluate("el => el.className")
            if text and len(text) < 100:
                result["price_elements"].append({
                    "tag": tag,
                    "class": cls[:100],
                    "text": text[:80],
                })
        except Exception:
            continue

    # Find airline-like elements
    airline_els = await page.query_selector_all('[class*="airline"], [class*="carrier"], [class*="operator"], [class*="flight-name"]')
    result["airline_elements_count"] = len(airline_els)
    for el in airline_els[:20]:
        try:
            text = (await el.inner_text()).strip()
            tag = await el.evaluate("el => el.tagName.toLowerCase()")
            cls = await el.evaluate("el => el.className")
            if text and len(text) < 100:
                result["airline_elements"].append({
                    "tag": tag,
                    "class": cls[:100],
                    "text": text[:80],
                })
        except Exception:
            continue

    # Find all unique classes containing "price" or "fare"
    price_classes = await page.evaluate("""
        () => {
            const classes = new Set();
            document.querySelectorAll('*').forEach(el => {
                if (el.className && typeof el.className === 'string') {
                    const cls = el.className.toLowerCase();
                    if (cls.includes('price') || cls.includes('fare') || cls.includes('cost')) {
                        classes.add(el.className.substring(0, 80));
                    }
                }
            });
            return Array.from(classes).slice(0, 30);
        }
    """)
    result["all_classes_with_price"] = price_classes

    airline_classes = await page.evaluate("""
        () => {
            const classes = new Set();
            document.querySelectorAll('*').forEach(el => {
                if (el.className && typeof el.className === 'string') {
                    const cls = el.className.toLowerCase();
                    if (cls.includes('airline') || cls.includes('carrier') || cls.includes('operator')) {
                        classes.add(el.className.substring(0, 80));
                    }
                }
            });
            return Array.from(classes).slice(0, 30);
        }
    """)
    result["all_classes_with_airline"] = airline_classes

    return result


async def inspect_all(origin: str = "DEL", destination: str = "BOM"):
    """Inspect all sources sequentially."""
    for source_key in SOURCES:
        try:
            await inspect_source(source_key, origin, destination)
            await asyncio.sleep(3)
        except Exception as e:
            print(f"Failed to inspect {source_key}: {e}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="DOM Inspector for SkyMetric Scraper")
    parser.add_argument("--source", default="all", help="Source to inspect (or 'all')")
    parser.add_argument("--origin", default="DEL", help="Origin airport code")
    parser.add_argument("--destination", default="BOM", help="Destination airport code")
    parser.add_argument("--wait", type=int, default=8000, help="Wait time in ms after page load")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    if args.source == "all":
        asyncio.run(inspect_all(args.origin, args.destination))
    else:
        asyncio.run(inspect_source(args.source, args.origin, args.destination, args.wait))


if __name__ == "__main__":
    main()
