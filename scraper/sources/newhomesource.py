"""
NewHomeSource.com source module.

Same best-effort static-HTML scraping approach as livabl.py: parse search
result cards with BeautifulSoup, fail soft on any error, and fall back to
bundled sample data when live scraping yields nothing. See livabl.py's
module docstring for the general caveats around selector maintenance.
"""

from __future__ import annotations

import logging

from bs4 import BeautifulSoup

from scraper.config import COASTAL_COUNTIES, USE_SAMPLE_DATA_FALLBACK
from scraper.sources.base import parse_price_text, safe_parse_all
from scraper.sources.sample_data import SAMPLE_LISTINGS
from scraper.utils.http import get_with_retry, polite_delay

logger = logging.getLogger(__name__)

SEARCH_URL = "https://www.newhomesource.com/communities/nc"


def _parse_card(card) -> dict | None:
    """Parse a single NewHomeSource search-result card."""
    builder_el = card.select_one(".builder-name, [data-testid='builder-name']")
    community_el = card.select_one(".community-name, [data-testid='community-name']")
    price_el = card.select_one(".price-range, .price, [data-testid='price']")
    address_el = card.select_one(".address, [data-testid='address']")
    link_el = card.select_one("a[href]")
    incentive_el = card.select_one(".incentive-text, [data-testid='incentive']")

    if not community_el or not price_el:
        return None

    price = parse_price_text(price_el.get_text())
    if price is None:
        return None

    return {
        "source_name": "newhomesource",
        "source_url": link_el["href"] if link_el and link_el.has_attr("href") else SEARCH_URL,
        "builder_name": builder_el.get_text(strip=True) if builder_el else None,
        "community_name": community_el.get_text(strip=True),
        "plan_name": None,
        "address": address_el.get_text(strip=True) if address_el else None,
        "city": None,
        "state": "NC",
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
        "raw_incentive_text": incentive_el.get_text(strip=True) if incentive_el else None,
    }


def fetch_listings() -> list[dict]:
    """Fetch and parse NewHomeSource's coastal-NC new-construction listings."""
    all_listings: list[dict] = []

    for county in COASTAL_COUNTIES:
        polite_delay()
        response = get_with_retry(
            SEARCH_URL, params={"county": county, "priceMax": 240000}
        )
        if response is None:
            logger.warning("newhomesource: no response for county=%s", county)
            continue

        try:
            soup = BeautifulSoup(response.text, "lxml")
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "newhomesource: failed to parse HTML for county=%s: %s", county, exc
            )
            continue

        cards = soup.select(".plp-card, [data-testid='plan-card'], [data-testid='community-card']")
        parsed = safe_parse_all(cards, _parse_card, "newhomesource")
        for listing in parsed:
            listing["county"] = listing.get("county") or county
        all_listings.extend(parsed)

    if not all_listings and USE_SAMPLE_DATA_FALLBACK:
        logger.info(
            "newhomesource: live scrape returned 0 results, using sample data fallback"
        )
        return [l for l in SAMPLE_LISTINGS if l["source_name"] == "newhomesource"]

    return all_listings
