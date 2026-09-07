"""
Diff engine: compares today's normalized, filtered listings against the
persisted data/history.json to flag new listings, price drops/increases,
and sold/off-market inventory (listings that were active yesterday but are
absent from today's scrape).

history.json shape:
{
    "last_updated": "2026-09-07T12:00:00+00:00",
    "price_history": {
        "<listing_id>": [
            {"date": "2026-09-01", "price": 229990, "status": "active"},
            {"date": "2026-09-07", "price": 224990, "status": "active"}
        ]
    },
    "events": [
        {
            "date": "2026-09-07",
            "listing_id": "...",
            "event": "new" | "price_drop" | "price_increase" | "sold",
            "builder_name": "...",
            "address": "...",
            "old_price": 229990,
            "new_price": 224990
        }
    ]
}
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

MAX_EVENTS_RETAINED = 500
MAX_PRICE_POINTS_PER_LISTING = 180  # ~6 months of daily snapshots


def _today_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def empty_history() -> dict:
    return {"last_updated": None, "price_history": {}, "events": []}


def apply_diff(today_listings: list[dict], history: Optional[dict] = None) -> tuple[list[dict], dict]:
    """
    Enrich today's listings with `price_change` and `listing_status`
    (new/price_drop/price_increase/unchanged), and return an updated
    history object that also logs sold/off-market listings as events.

    Does not mutate the input history dict; returns a new one.
    """
    history = history or empty_history()
    price_history = dict(history.get("price_history") or {})
    events = list(history.get("events") or [])

    today = _today_str()
    today_ids = set()
    enriched_listings = []

    for listing in today_listings:
        listing_id = listing["id"]
        today_ids.add(listing_id)
        price = listing.get("price")

        prior_points = price_history.get(listing_id, [])
        prior_price = prior_points[-1]["price"] if prior_points else None

        if prior_price is None:
            status = "new"
            price_change = None
            events.append(
                {
                    "date": today,
                    "listing_id": listing_id,
                    "event": "new",
                    "builder_name": listing.get("builder_name"),
                    "address": listing.get("address"),
                    "old_price": None,
                    "new_price": price,
                }
            )
        elif price is not None and price < prior_price:
            status = "price_drop"
            price_change = round(price - prior_price, 2)
            events.append(
                {
                    "date": today,
                    "listing_id": listing_id,
                    "event": "price_drop",
                    "builder_name": listing.get("builder_name"),
                    "address": listing.get("address"),
                    "old_price": prior_price,
                    "new_price": price,
                }
            )
        elif price is not None and price > prior_price:
            status = "price_increase"
            price_change = round(price - prior_price, 2)
            events.append(
                {
                    "date": today,
                    "listing_id": listing_id,
                    "event": "price_increase",
                    "builder_name": listing.get("builder_name"),
                    "address": listing.get("address"),
                    "old_price": prior_price,
                    "new_price": price,
                }
            )
        else:
            status = "unchanged"
            price_change = 0

        listing["price_change"] = price_change
        listing["listing_status"] = status
        listing["first_seen"] = (
            prior_points[0]["date"] if prior_points else today
        )
        listing["last_seen"] = today
        enriched_listings.append(listing)

        # Only append a new price point if the price actually changed, or
        # this is the first time we've seen the listing -- keeps the
        # history compact instead of recording an identical price daily.
        if not prior_points or prior_points[-1]["price"] != price:
            points = price_history.setdefault(listing_id, [])
            points.append({"date": today, "price": price, "status": "active"})
            price_history[listing_id] = points[-MAX_PRICE_POINTS_PER_LISTING:]

    # Anything with prior price history that isn't in today's active set is
    # presumed sold or otherwise off-market.
    previously_active_ids = {
        lid
        for lid, points in price_history.items()
        if points and points[-1]["status"] == "active"
    }
    newly_sold_ids = previously_active_ids - today_ids

    for listing_id in newly_sold_ids:
        points = price_history[listing_id]
        last_price = points[-1]["price"]
        points.append({"date": today, "price": last_price, "status": "sold"})
        price_history[listing_id] = points[-MAX_PRICE_POINTS_PER_LISTING:]
        events.append(
            {
                "date": today,
                "listing_id": listing_id,
                "event": "sold",
                "builder_name": None,
                "address": None,
                "old_price": last_price,
                "new_price": None,
            }
        )

    updated_history = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "price_history": price_history,
        "events": events[-MAX_EVENTS_RETAINED:],
    }

    return enriched_listings, updated_history
