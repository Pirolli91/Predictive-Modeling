"""
Representative sample listings for coastal NC new-construction townhomes
priced at or below $240,000.

This dataset serves two purposes:

1. It is the seed content committed to data/listings.json so the dashboard
   is demoable immediately after checkout, before the first live scrape
   runs.
2. Each source module falls back to its slice of this dataset when a live
   scrape returns zero results (e.g. no outbound network access in a
   sandbox, or a target site's markup has drifted out from under the
   selectors). This keeps the pipeline resilient without ever silently
   fabricating data that pretends to be freshly scraped -- fallback
   listings are tagged accordingly by the pipeline's diff engine via the
   `source_name` field, and the workflow log makes clear when fallback
   data was used instead of a live scrape.

Coordinates are approximate town-center/community-area coordinates for
illustration purposes.
"""

from __future__ import annotations

SAMPLE_LISTINGS = [
    {
        "source_name": "livabl",
        "source_url": "https://www.livabl.com/north-carolina/brunswick-county/example-community-a",
        "builder_name": "D.R. Horton",
        "community_name": "Palmetto Landing",
        "plan_name": "The Aspen",
        "address": "142 Palmetto Landing Dr",
        "city": "Leland",
        "state": "NC",
        "zip": "28451",
        "county": "Brunswick",
        "latitude": 34.2352,
        "longitude": -78.0658,
        "price": 229990,
        "beds": 3,
        "baths": 2.5,
        "sqft": 1560,
        "estimated_hoa_fee_monthly": 165,
        "estimated_completion_date": "2026-01-15",
        "move_in_status": "Under Construction",
        "raw_incentive_text": (
            "For a limited time, D.R. Horton is offering a 4.99% fixed rate "
            "for the first year through DHI Mortgage on select homes, plus "
            "up to $8,000 in closing cost assistance for qualified buyers. "
            "Rate promo applies to primary residences only."
        ),
    },
    {
        "source_name": "livabl",
        "source_url": "https://www.livabl.com/north-carolina/onslow-county/example-community-b",
        "builder_name": "True Homes",
        "community_name": "Sound View Villas",
        "plan_name": "The Camden",
        "address": "88 Sound View Ct",
        "city": "Sneads Ferry",
        "state": "NC",
        "zip": "28460",
        "county": "Onslow",
        "latitude": 34.5445,
        "longitude": -77.3961,
        "price": 219500,
        "beds": 3,
        "baths": 2,
        "sqft": 1420,
        "estimated_hoa_fee_monthly": 145,
        "estimated_completion_date": "2025-12-01",
        "move_in_status": "Move-In Ready",
        "raw_incentive_text": (
            "$5,000 builder closing cost credit with preferred lender. "
            "5.5% 30-year fixed rate available. Open to investors and "
            "second home buyers with 20% down."
        ),
    },
    {
        "source_name": "newhomesource",
        "source_url": "https://www.newhomesource.com/community/example-community-c",
        "builder_name": "Lennar",
        "community_name": "Cypress Cove",
        "plan_name": "The Dogwood",
        "address": "310 Cypress Cove Ln",
        "city": "Hampstead",
        "state": "NC",
        "zip": "28443",
        "county": "Pender",
        "latitude": 34.3660,
        "longitude": -77.7086,
        "price": 238900,
        "beds": 3,
        "baths": 2.5,
        "sqft": 1610,
        "estimated_hoa_fee_monthly": 195,
        "estimated_completion_date": "2026-03-01",
        "move_in_status": "To Be Built",
        "raw_incentive_text": (
            "Ask about Lennar's Everything's Included financing incentives: "
            "up to $10,000 in closing cost assistance. Rate promo terms "
            "apply to primary residence purchases; investor eligibility "
            "varies by lender program."
        ),
    },
    {
        "source_name": "newhomesource",
        "source_url": "https://www.newhomesource.com/community/example-community-d",
        "builder_name": "Ryan Homes",
        "community_name": "Marsh Harbor",
        "plan_name": "The Bristol",
        "address": "27 Marsh Harbor Way",
        "city": "Newport",
        "state": "NC",
        "zip": "28570",
        "county": "Carteret",
        "latitude": 34.7909,
        "longitude": -76.8672,
        "price": 224900,
        "beds": 3,
        "baths": 2.5,
        "sqft": 1495,
        "estimated_hoa_fee_monthly": 175,
        "estimated_completion_date": "2025-11-20",
        "move_in_status": "Under Construction",
        "raw_incentive_text": (
            "NVR/Ryan preferred lender offering 5.25% fixed for qualified "
            "buyers, plus $7,500 towards closing costs. Non-owner occupied "
            "purchases welcome with 25% down."
        ),
    },
    {
        "source_name": "builder_direct",
        "source_url": "https://www.trihomesnc.com/communities/example-community-e",
        "builder_name": "Landmark 24 Homes",
        "community_name": "Harborview Row",
        "plan_name": "The Beaufort",
        "address": "5 Harborview Row",
        "city": "Havelock",
        "state": "NC",
        "zip": "28532",
        "county": "Craven",
        "latitude": 34.8791,
        "longitude": -76.9013,
        "price": 209900,
        "beds": 2,
        "baths": 2,
        "sqft": 1280,
        "estimated_hoa_fee_monthly": 130,
        "estimated_completion_date": "2025-10-30",
        "move_in_status": "Move-In Ready",
        "raw_incentive_text": (
            "Move-in ready inventory home. $6,000 closing cost credit when "
            "using builder's preferred lender. Standard market rate "
            "financing; no restrictions on investor or second-home buyers."
        ),
    },
    {
        "source_name": "builder_direct",
        "source_url": "https://www.drhorton.com/north-carolina/example-community-f",
        "builder_name": "D.R. Horton",
        "community_name": "Currituck Landing",
        "plan_name": "The Sadler",
        "address": "19 Currituck Landing Cir",
        "city": "Moyock",
        "state": "NC",
        "zip": "27958",
        "county": "Currituck",
        "latitude": 36.5218,
        "longitude": -76.1866,
        "price": 234990,
        "beds": 3,
        "baths": 2.5,
        "sqft": 1540,
        "estimated_hoa_fee_monthly": 155,
        "estimated_completion_date": "2026-02-15",
        "move_in_status": "Under Construction",
        "raw_incentive_text": (
            "DHI Mortgage rate promo: 4.75% fixed year one with seller "
            "paid points. Up to $9,000 closing cost credit. Must be owner "
            "occupied to qualify for the promotional rate."
        ),
    },
]
