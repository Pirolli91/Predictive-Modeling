"""
Central configuration for the NC Coastal Townhome ETL pipeline.

Everything that a scraper module or the orchestrator needs to know about
target geography, filtering thresholds, and network behavior lives here so
it can be tuned without touching parsing logic.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Filtering thresholds
# ---------------------------------------------------------------------------

PRICE_CAP = 240000  # USD, inclusive
MAX_DISTANCE_TO_WATER_MILES = 20.0
MAX_DRIVE_MINUTES_TO_WATER = 30

# ---------------------------------------------------------------------------
# Geography: coastal NC counties in scope.
# ---------------------------------------------------------------------------

COASTAL_COUNTIES = [
    "Brunswick",
    "New Hanover",
    "Pender",
    "Onslow",
    "Carteret",
    "Craven",
    "Pamlico",
    "Beaufort",
    "Currituck",
    "Dare",
    "Hyde",
    "Bertie",
    "Chowan",
    "Perquimans",
    "Camden",
    "Pasquotank",
    "Tyrrell",
    "Washington",
]

# Reference points used as the baseline for the Haversine proximity-to-water
# calculation. Each entry is a tuple of (name, latitude, longitude), spread
# along the Atlantic coastline and the major sounds so that every coastal
# county above has a nearby reference point.
COASTAL_REFERENCE_POINTS = [
    ("Calabash", 33.89, -78.57),
    ("Holden Beach", 33.91, -78.30),
    ("Southport", 33.92, -78.02),
    ("Wrightsville Beach", 34.21, -77.79),
    ("Topsail Beach", 34.37, -77.62),
    ("Swansboro", 34.69, -77.12),
    ("Emerald Isle", 34.66, -77.04),
    ("Morehead City", 34.72, -76.73),
    ("Beaufort", 34.72, -76.66),
    ("Oriental", 35.02, -76.70),
    ("New Bern", 35.11, -77.04),
    ("Washington", 35.55, -77.05),
    ("Elizabeth City", 36.29, -76.25),
    ("Kitty Hawk", 36.07, -75.70),
    ("Nags Head", 35.95, -75.62),
    ("Manteo", 35.91, -75.68),
]

# ---------------------------------------------------------------------------
# Network behavior
# ---------------------------------------------------------------------------

# Rotated per-request to avoid presenting a single fixed fingerprint. This is
# a courtesy/robustness measure, not an attempt to bypass access controls.
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) "
    "Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]

REQUEST_TIMEOUT_SECONDS = 20
MAX_RETRIES = 4
BACKOFF_BASE_SECONDS = 1.5
MIN_REQUEST_DELAY_SECONDS = 1.0
MAX_REQUEST_DELAY_SECONDS = 3.0

# Free public OSRM demo routing server, used only as a best-effort refinement
# of drive-time-to-water. No API key required. If unreachable, the pipeline
# falls back to a Haversine-distance-based estimate.
OSRM_DEMO_SERVER = "https://router.project-osrm.org"

# ---------------------------------------------------------------------------
# Data sources
# ---------------------------------------------------------------------------
# Each source module in scraper/sources/ implements `fetch_listings()` and is
# registered here so the orchestrator can loop over them uniformly. Selectors
# inside each module are best-effort and may need periodic maintenance as
# target sites change their markup -- this is normal for any scraper and is
# why the pipeline is defensive (try/except per-listing, never let one
# malformed listing abort the whole run).
SOURCES = [
    {
        "name": "livabl",
        "module": "scraper.sources.livabl",
        "base_url": "https://www.livabl.com",
        "enabled": True,
    },
    {
        "name": "newhomesource",
        "module": "scraper.sources.newhomesource",
        "base_url": "https://www.newhomesource.com",
        "enabled": True,
    },
    {
        "name": "builder_direct",
        "module": "scraper.sources.builder_direct",
        "base_url": None,
        "enabled": True,
    },
]

# When true (or when live scraping yields zero results, e.g. in CI sandboxes
# without outbound access, or when a site's markup has drifted out from
# under the selectors), the pipeline seeds/falls back to the bundled sample
# dataset so the dashboard always has representative data to render. Live
# runs in GitHub Actions should set this to "false" once selectors have been
# validated against the live sites.
import os  # noqa: E402

USE_SAMPLE_DATA_FALLBACK = os.environ.get("USE_SAMPLE_DATA_FALLBACK", "true").lower() in (
    "1",
    "true",
    "yes",
)

# ---------------------------------------------------------------------------
# Investment metric assumptions
# ---------------------------------------------------------------------------
# These are configurable placeholders standing in for paid data feeds (e.g.
# a rent-comp API or a live mortgage-rate API). They are deliberately kept
# in one place so an operator can override them with better local data
# without touching calculation logic. The frontend mortgage calculator lets
# an end user override the investor rate and down payment interactively.

# Approximate monthly rent per square foot for small/attached coastal NC
# housing product, used as the default rent proxy when no better local
# comp is supplied. This is intentionally conservative for a starter
# townhome/villa product.
DEFAULT_RENT_PER_SQFT_MONTHLY = 1.05

# Per-county multiplier applied to the base rent/sqft figure above, to
# roughly reflect relative rent strength across coastal NC submarkets.
# 1.00 = matches the base rate. Counties not listed default to 1.00.
COUNTY_RENT_MULTIPLIERS = {
    "New Hanover": 1.15,
    "Dare": 1.35,
    "Carteret": 1.10,
    "Brunswick": 1.05,
    "Onslow": 0.95,
    "Pender": 1.05,
    "Craven": 0.90,
    "Currituck": 1.20,
}

# Standard (non-promotional) prevailing investor mortgage rate assumption,
# used for the "market rate" side of the buydown comparison. Override via
# env var, CLI flag, or interactively in the dashboard calculator.
STANDARD_INVESTOR_RATE_PCT = 7.5

DEFAULT_LOAN_TERM_YEARS = 30
DEFAULT_INVESTOR_DOWN_PAYMENT_PCT = 0.25  # 25%, within the 20-25% range

# Rough combined annual property-tax + hazard/flood-insurance estimate as a
# percentage of purchase price, reflecting coastal NC's elevated insurance
# costs relative to inland markets. Used only for the DSCR estimate.
ESTIMATED_ANNUAL_TAX_INSURANCE_PCT_OF_PRICE = 0.016
