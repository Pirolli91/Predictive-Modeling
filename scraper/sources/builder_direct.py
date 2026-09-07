"""
Builder-direct source module.

Builder portals (D.R. Horton, Lennar, True Homes, etc.) commonly render
their inventory/pricing via client-side JavaScript, so this module uses
Playwright (headless Chromium) instead of a plain HTTP GET. Each builder is
registered in BUILDER_SITES below with its own search URL and CSS
selectors; add new builders by appending an entry, no orchestrator changes
needed.

As with the other source modules, selectors are a best-effort starting
point that will need periodic validation against the live sites, and any
failure (browser launch, navigation, selector drift) is caught and logged
rather than raising, so one builder site being down/changed never blocks
the rest of the pipeline.
"""

from __future__ import annotations

import logging

from bs4 import BeautifulSoup

from scraper.config import USE_SAMPLE_DATA_FALLBACK
from scraper.sources.base import parse_price_text, safe_parse_all
from scraper.sources.sample_data import SAMPLE_LISTINGS

logger = logging.getLogger(__name__)

BUILDER_SITES = [
    {
        "builder_name": "D.R. Horton",
        "search_url": "https://www.drhorton.com/north-carolina",
        "card_selector": ".plan-card, [data-testid='home-card']",
    },
    {
        "builder_name": "Lennar",
        "search_url": "https://www.lennar.com/new-homes/north-carolina",
        "card_selector": ".home-card, [data-testid='home-card']",
    },
    {
        "builder_name": "True Homes",
        "search_url": "https://www.truehomesusa.com/new-homes/north-carolina",
        "card_selector": ".home-card, .community-card",
    },
]


def render_with_playwright(url: str, wait_selector: str | None = None) -> str | None:
    """
    Render a JS-heavy page with headless Chromium and return its final
    HTML. Returns None on any failure (browser launch, navigation timeout,
    Playwright not installed) so callers can fall back gracefully.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.warning("playwright is not installed; skipping dynamic render for %s", url)
        return None

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                page.goto(url, timeout=30_000, wait_until="networkidle")
                if wait_selector:
                    try:
                        page.wait_for_selector(wait_selector, timeout=10_000)
                    except Exception:  # noqa: BLE001 - selector may not exist
                        pass
                html = page.content()
                return html
            finally:
                browser.close()
    except Exception as exc:  # noqa: BLE001 - rendering is best-effort
        logger.warning("Playwright render failed for %s: %s", url, exc)
        return None


def _parse_card(card, builder_name: str) -> dict | None:
    price_el = card.select_one(".price, [data-testid='price']")
    address_el = card.select_one(".address, [data-testid='address']")
    plan_el = card.select_one(".plan-name, [data-testid='plan-name']")
    incentive_el = card.select_one(".incentive, [data-testid='incentive']")
    link_el = card.select_one("a[href]")

    if not price_el:
        return None

    price = parse_price_text(price_el.get_text())
    if price is None:
        return None

    return {
        "source_name": "builder_direct",
        "source_url": link_el["href"] if link_el and link_el.has_attr("href") else None,
        "builder_name": builder_name,
        "community_name": None,
        "plan_name": plan_el.get_text(strip=True) if plan_el else None,
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
    """Fetch and parse builder-direct inventory across all registered builders."""
    all_listings: list[dict] = []

    for site in BUILDER_SITES:
        html = render_with_playwright(site["search_url"], wait_selector=site["card_selector"])
        if html is None:
            logger.warning("builder_direct: no rendered HTML for %s", site["builder_name"])
            continue

        try:
            soup = BeautifulSoup(html, "lxml")
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "builder_direct: failed to parse HTML for %s: %s", site["builder_name"], exc
            )
            continue

        cards = soup.select(site["card_selector"])
        parsed = safe_parse_all(
            cards,
            lambda card, b=site["builder_name"]: _parse_card(card, b),
            f"builder_direct:{site['builder_name']}",
        )
        all_listings.extend(parsed)

    if not all_listings and USE_SAMPLE_DATA_FALLBACK:
        logger.info(
            "builder_direct: live scrape returned 0 results, using sample data fallback"
        )
        return [l for l in SAMPLE_LISTINGS if l["source_name"] == "builder_direct"]

    return all_listings
