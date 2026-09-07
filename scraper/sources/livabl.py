"""
Livabl.com source module.

Livabl aggregates new-construction community listings and exposes a
search/filter UI. This module attempts a best-effort static-HTML scrape of
its coastal-NC search results using BeautifulSoup. Because Livabl (like
most listing aggregators) periodically changes its markup and may render
results client-side via JavaScript, the CSS selectors below are a
best-effort starting point -- validate them against the live site before
relying on this in production, and consider swapping to the Playwright
based flow in scraper/sources/builder_direct.py's `render_with_playwright`
helper if results start coming back empty despite a 200 response.

On any failure (network, selector drift, parse error) this module logs and
returns an empty list; the orchestrator then falls back to bundled sample
data so the pipeline never hard-fails on one source.
"""

from __future__ import annotations

import logging

from bs4 import BeautifulSoup

from scraper.config import COASTAL_COUNTIES, USE_SAMPLE_DATA_FALLBACK
from scraper.sources.base import parse_int_text, parse_price_text, safe_parse_all
from scraper.sources.sample_data import SAMPLE_LISTINGS
from scraper.utils.http import get_with_retry, polite_delay

logger = logging.getLogger(__name__)

SEARCH_URL = "https://www.livabl.com/north-carolina"


def _parse_card(card) -> dict | None:
    """Parse a single Livabl search-result card into a raw listing dict."""
    name_el = card.select_one(".community-name, [data-testid='community-name']")
    price_el = card.select_one(".price, [data-testid='price']")
    location_el = card.select_one(".location, [data-testid='location']")
    link_el = card.select_one("a[href]")

    if not name_el or not price_el:
        return None

    price = parse_price_text(price_el.get_text())
    if price is None:
        return None

    location_text = location_el.get_text(strip=True) if location_el else ""
    city, _, state = location_text.partition(",")

    return {
        "source_name": "livabl",
        "source_url": link_el["href"] if link_el and link_el.has_attr("href") else SEARCH_URL,
        "builder_name": None,
        "community_name": name_el.get_text(strip=True),
        "plan_name": None,
        "address": None,
        "city": city.strip() or None,
        "state": state.strip() or "NC",
        "zip": None,
        "county": None,
        "latitude": None,
        "longitude": None,
        "price": price,
        "beds": None,
        "baths": None,
        "sqft": None,
        "estimated_hoa_fee_monthly": None,
        "estimated_completion_date": None,
        "move_in_status": None,
        "raw_incentive_text": None,
    }


def fetch_listings() -> list[dict]:
    """Fetch and parse Livabl's coastal-NC new-construction listings."""
    all_listings: list[dict] = []

    for county in COASTAL_COUNTIES:
        polite_delay()
        response = get_with_retry(SEARCH_URL, params={"county": county, "state": "NC"})
        if response is None:
            logger.warning("livabl: no response for county=%s", county)
            continue

        try:
            soup = BeautifulSoup(response.text, "lxml")
        except Exception as exc:  # noqa: BLE001
            logger.warning("livabl: failed to parse HTML for county=%s: %s", county, exc)
            continue

        cards = soup.select(".community-card, [data-testid='community-card']")
        parsed = safe_parse_all(cards, _parse_card, "livabl")
        for listing in parsed:
            listing["county"] = listing.get("county") or county
        all_listings.extend(parsed)

    if not all_listings and USE_SAMPLE_DATA_FALLBACK:
        logger.info("livabl: live scrape returned 0 results, using sample data fallback")
        return [l for l in SAMPLE_LISTINGS if l["source_name"] == "livabl"]

    return all_listings
