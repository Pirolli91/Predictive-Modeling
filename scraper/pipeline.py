"""
Pipeline orchestrator: pulls raw listings from every enabled source,
normalizes and deduplicates them, applies the price-cap and
coastal-proximity filters, extracts builder incentive terms, computes
investment metrics, diffs against yesterday's history, and writes
data/listings.json + data/history.json.

Run directly:

    python -m scraper.pipeline

Or via the GitHub Actions daily_refresh workflow.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from scraper.config import COASTAL_COUNTIES, PRICE_CAP, SOURCES
from scraper.diff_engine import apply_diff, empty_history
from scraper.utils.financials import compute_investment_metrics
from scraper.utils.geo import evaluate_proximity
from scraper.utils.geocode import geocode_address
from scraper.utils.incentives import parse_incentive_text

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("scraper.pipeline")

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
LISTINGS_PATH = DATA_DIR / "listings.json"
HISTORY_PATH = DATA_DIR / "history.json"


def make_listing_id(builder_name: Optional[str], address: Optional[str], city: Optional[str], zip_code: Optional[str]) -> str:
    """Deterministic id derived from builder + address so the same physical
    listing gets the same id across daily runs (needed for diffing)."""
    key = "|".join(
        [
            (builder_name or "").strip().lower(),
            (address or "").strip().lower(),
            (city or "").strip().lower(),
            (zip_code or "").strip().lower(),
        ]
    )
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def collect_raw_listings() -> list[dict]:
    """Dynamically import and call `fetch_listings()` on every enabled
    source module registered in scraper.config.SOURCES."""
    raw_listings: list[dict] = []

    for source in SOURCES:
        if not source.get("enabled", True):
            continue
        module_path = source["module"]
        try:
            module = importlib.import_module(module_path)
            listings = module.fetch_listings()
            logger.info("Source '%s' returned %d raw listings", source["name"], len(listings))
            raw_listings.extend(listings)
        except Exception as exc:  # noqa: BLE001 - one bad source shouldn't kill the run
            logger.error("Source '%s' failed entirely: %s", source["name"], exc)

    return raw_listings


def deduplicate(raw_listings: list[dict]) -> list[dict]:
    """Drop exact duplicate listings (same builder+address+zip) that may
    have been returned by more than one source."""
    seen = set()
    deduped = []
    for listing in raw_listings:
        key = make_listing_id(
            listing.get("builder_name"),
            listing.get("address"),
            listing.get("city"),
            listing.get("zip"),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(listing)
    return deduped


def enrich_listing(raw: dict) -> Optional[dict]:
    """
    Turn a raw, source-specific listing dict into the full canonical
    schema: geocode if needed, filter by price/proximity, parse incentive
    text, and compute investment metrics. Returns None if the listing
    fails validation (missing price, out of budget, or not coastal).
    """
    price = raw.get("price")
    if price is None or price <= 0:
        logger.debug("Dropping listing with no usable price: %s", raw.get("address"))
        return None

    if price > PRICE_CAP:
        return None

    lat, lon = raw.get("latitude"), raw.get("longitude")
    if lat is None or lon is None:
        geocoded = geocode_address(
            raw.get("address"), raw.get("city"), raw.get("state") or "NC", raw.get("zip")
        )
        if geocoded:
            lat, lon = geocoded

    if lat is None or lon is None:
        logger.warning(
            "Dropping listing that could not be geocoded: %s, %s",
            raw.get("address"),
            raw.get("community_name"),
        )
        return None

    proximity = evaluate_proximity(lat, lon)
    if not proximity["meets_proximity_requirement"]:
        return None

    county = raw.get("county")
    if county and county not in COASTAL_COUNTIES:
        logger.debug("Dropping listing outside coastal county scope: %s", county)
        return None

    incentive_fields = parse_incentive_text(raw.get("raw_incentive_text") or "")

    sqft = raw.get("sqft")
    price_per_sqft = round(price / sqft, 2) if sqft else None

    investment_metrics = compute_investment_metrics(
        price=price,
        sqft=sqft,
        county=county,
        builder_rate_promo=incentive_fields["builder_rate_promo"],
        estimated_hoa_fee_monthly=raw.get("estimated_hoa_fee_monthly") or 0,
    )

    listing_id = make_listing_id(
        raw.get("builder_name"), raw.get("address"), raw.get("city"), raw.get("zip")
    )

    return {
        "id": listing_id,
        "builder_name": raw.get("builder_name"),
        "community_name": raw.get("community_name"),
        "plan_name": raw.get("plan_name"),
        "address": raw.get("address"),
        "city": raw.get("city"),
        "state": raw.get("state") or "NC",
        "zip": raw.get("zip"),
        "county": county,
        "latitude": lat,
        "longitude": lon,
        "price": price,
        "price_change": None,  # populated by diff engine
        "beds": raw.get("beds"),
        "baths": raw.get("baths"),
        "sqft": sqft,
        "price_per_sqft": price_per_sqft,
        "estimated_hoa_fee_monthly": raw.get("estimated_hoa_fee_monthly"),
        "estimated_completion_date": raw.get("estimated_completion_date"),
        "move_in_status": raw.get("move_in_status"),
        "distance_to_water_miles": proximity["distance_to_water_miles"],
        "nearest_water_point": proximity["nearest_water_point"],
        "estimated_drive_minutes_to_water": proximity["estimated_drive_minutes"],
        "builder_rate_promo": incentive_fields["builder_rate_promo"],
        "closing_cost_credit": incentive_fields["closing_cost_credit"],
        "investor_eligibility_flag": incentive_fields["investor_eligibility_flag"],
        "raw_incentive_text": incentive_fields["raw_incentive_text"],
        "estimated_monthly_rent": investment_metrics["estimated_monthly_rent"],
        "gross_rental_yield_pct": investment_metrics["gross_rental_yield_pct"],
        "investor_debt_service": investment_metrics["investor_debt_service"],
        "builder_promo_debt_service": investment_metrics["builder_promo_debt_service"],
        "investor_dscr": investment_metrics["investor_dscr"],
        "builder_promo_dscr": investment_metrics["builder_promo_dscr"],
        "source_name": raw.get("source_name"),
        "source_url": raw.get("source_url"),
        "listing_status": None,  # populated by diff engine
        "first_seen": None,  # populated by diff engine
        "last_seen": None,  # populated by diff engine
    }


def load_json(path: Path, default):
    if path.exists():
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            logger.warning("Failed to parse %s, starting fresh", path)
    return default


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str))


def run() -> dict:
    logger.info("Starting NC coastal townhome pipeline run")

    raw_listings = collect_raw_listings()
    logger.info("Collected %d raw listings across all sources", len(raw_listings))

    deduped = deduplicate(raw_listings)
    logger.info("%d listings after deduplication", len(deduped))

    enriched = []
    for raw in deduped:
        try:
            listing = enrich_listing(raw)
        except Exception as exc:  # noqa: BLE001 - never let one listing kill the run
            logger.warning("Failed to enrich listing %s: %s", raw.get("address"), exc)
            continue
        if listing:
            enriched.append(listing)

    logger.info(
        "%d listings passed price cap ($%s) and coastal proximity filters",
        len(enriched),
        f"{PRICE_CAP:,}",
    )

    history = load_json(HISTORY_PATH, empty_history())
    final_listings, updated_history = apply_diff(enriched, history)

    final_listings.sort(key=lambda l: l["price"])

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_active_listings": len(final_listings),
        "new_today": sum(1 for l in final_listings if l["listing_status"] == "new"),
        "price_drops_today": sum(1 for l in final_listings if l["listing_status"] == "price_drop"),
        "price_increases_today": sum(
            1 for l in final_listings if l["listing_status"] == "price_increase"
        ),
        "sold_or_delisted_today": sum(
            1 for e in updated_history["events"] if e["event"] == "sold" and e["date"] == datetime.now(timezone.utc).strftime("%Y-%m-%d")
        ),
    }

    output = {
        "generated_at": summary["generated_at"],
        "price_cap": PRICE_CAP,
        "summary": summary,
        "listings": final_listings,
    }

    write_json(LISTINGS_PATH, output)
    write_json(HISTORY_PATH, updated_history)

    logger.info("Wrote %s and %s", LISTINGS_PATH, HISTORY_PATH)
    logger.info("Run summary: %s", json.dumps(summary, indent=2))

    return summary


if __name__ == "__main__":
    try:
        run()
    except Exception:  # noqa: BLE001 - top-level guard for CI logs
        logger.exception("Pipeline run failed")
        sys.exit(1)
