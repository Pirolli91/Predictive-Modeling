# NC Coastal Townhome Investment Dashboard

A fully automated, **$0/month** pipeline + dashboard that tracks newly built
townhomes and attached villas in coastal North Carolina priced at or below
**$240,000**, with builder financing incentives, investor eligibility, and
DSCR-based investment metrics.

- **ETL / scraper** — Python (`requests` + `BeautifulSoup4` for static
  pages, `playwright` for JS-rendered builder portals), with retries,
  exponential backoff, user-agent rotation, and defensive per-listing error
  trapping.
- **Automation** — a GitHub Actions workflow on a daily cron
  (`0 12 * * *`) that runs the pipeline and commits `data/listings.json` +
  `data/history.json` straight back into the repo.
- **Storage** — no database. The repo itself is the datastore
  ("GitHub-hosted flat data architecture").
- **Frontend** — Next.js (App Router) + Tailwind CSS + Lucide icons +
  React-Leaflet, deployable to Vercel or Cloudflare Pages's free tier.

Every piece of this stack runs on a free tier: GitHub Actions (public repo
minutes), GitHub-hosted JSON (no DB), OpenStreetMap tiles + the public OSRM
demo router + Nominatim geocoding (no API keys), and Vercel/Cloudflare Pages
hobby hosting.

---

## Repository layout

```
scraper/
  config.py              # counties, coastal reference points, thresholds, source registry
  pipeline.py             # orchestrator: scrape -> filter -> enrich -> diff -> write JSON
  diff_engine.py           # new / price-drop / price-increase / sold detection
  requirements.txt
  sources/
    livabl.py              # BeautifulSoup scraper for Livabl.com
    newhomesource.py        # BeautifulSoup scraper for NewHomeSource.com
    builder_direct.py        # Playwright-rendered scraper for builder portals (DHI, Lennar, True Homes, ...)
    sample_data.py           # bundled seed/fallback dataset
    base.py
  utils/
    geo.py                 # Haversine distance + drive-time-to-water proximity check
    geocode.py               # free Nominatim geocoding fallback, disk-cached
    incentives.py             # regex extraction of promo rate / closing credit / investor eligibility
    financials.py             # rent proxy, mortgage P&I, DSCR, investor vs. builder-rate comparison
    http.py                  # retrying/backoff/UA-rotating request session

data/
  listings.json            # current active listings (what the dashboard reads)
  history.json              # per-listing price history + new/price-drop/sold event log

.github/workflows/
  daily_refresh.yml         # cron + workflow_dispatch, runs the pipeline, commits & pushes data/*.json

dashboard/                 # Next.js App Router site
  app/                      # layout, page, globals.css
  components/                # KpiHeader, FilterBar, MapView, DealCard, DealTable, MortgageCalculatorModal, DashboardClient
  lib/                       # types.ts, data.ts, calculations.ts, kpis.ts, format.ts
  public/data/listings.json    # bundled offline/local-dev fallback snapshot
```

---

## How the pipeline works (`scraper/pipeline.py`)

1. **Collect** — dynamically imports every enabled entry in
   `scraper.config.SOURCES` and calls its `fetch_listings()`. Each source
   module is independently wrapped in a try/except so one dead source
   never takes down the run.
2. **Deduplicate** — collapses listings that appear from more than one
   source using a deterministic id (`sha256(builder|address|city|zip)`).
3. **Filter** — drops anything over the `$240,000` price cap
   (`scraper/config.py:PRICE_CAP`).
4. **Geocode (if needed)** — listings missing lat/lon are geocoded via the
   free OpenStreetMap Nominatim API (`scraper/utils/geocode.py`), rate
   limited to 1 req/sec per its usage policy, and cached to
   `data/.geocode_cache.json` so the same address is never looked up
   twice.
5. **Proximity filter** — `scraper/utils/geo.py` computes Haversine
   distance to the nearest of 16 coastal/sound reference points spanning
   Calabash to Manteo, plus a drive-time estimate (upgradeable to live
   OSRM routing). A listing passes if it's within 20 miles **or** an
   estimated 30-minute drive of water.
6. **Incentive parsing** — `scraper/utils/incentives.py` regex-extracts a
   promotional rate, a closing-cost credit, and an investor-eligibility
   classification (`investor_eligible` / `primary_residence_only` /
   `unspecified`) out of each listing's raw incentive blurb.
7. **Investment metrics** — `scraper/utils/financials.py` computes an
   estimated rent (configurable $/sqft-by-county proxy), gross rental
   yield, amortized P&I at both the standard investor rate and the
   builder's promo rate (20–25% down), estimated taxes/insurance, and
   DSCR for both financing scenarios.
8. **Diff against history** — `scraper/diff_engine.py` compares today's
   listings to `data/history.json` and tags each as `new`, `price_drop`,
   `price_increase`, or `unchanged`; anything previously active that
   disappears from today's scrape is logged as `sold`.
9. **Write** — `data/listings.json` (today's active, enriched listings)
   and `data/history.json` (append-only price/event log) are written back
   to the repo.

### Selector maintenance note

Like any scraper, the CSS selectors in `scraper/sources/*.py` are a
best-effort starting point against each site's current markup. Sites
change their HTML periodically — validate selectors against the live site
before depending on this in production. Every source module fails soft
(catches, logs, returns `[]`) rather than crashing the pipeline, and falls
back to the bundled sample dataset in `scraper/sources/sample_data.py` so
the dashboard always has representative data even if a source's markup has
drifted.

---

## Data schema

Each listing in `data/listings.json` follows this shape (see
`dashboard/lib/types.ts` for the mirrored TypeScript type):

| Field | Description |
|---|---|
| `id` | Deterministic hash of builder + address |
| `builder_name`, `community_name`, `plan_name` | |
| `address`, `city`, `state`, `zip`, `county` | |
| `latitude`, `longitude` | |
| `price`, `price_change` | Current price and diff vs. yesterday |
| `beds`, `baths`, `sqft`, `price_per_sqft` | |
| `estimated_hoa_fee_monthly` | |
| `estimated_completion_date`, `move_in_status` | |
| `distance_to_water_miles`, `nearest_water_point`, `estimated_drive_minutes_to_water` | |
| `builder_rate_promo`, `closing_cost_credit`, `investor_eligibility_flag`, `raw_incentive_text` | Builder Financing & Incentives Module |
| `estimated_monthly_rent`, `gross_rental_yield_pct` | |
| `investor_debt_service`, `builder_promo_debt_service` | P&I at 20-25% down, standard vs. promo rate |
| `investor_dscr`, `builder_promo_dscr` | |
| `listing_status`, `first_seen`, `last_seen` | Populated by the diff engine |

---

## Running the scraper locally

```bash
cd scraper
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install --with-deps chromium

# from the repo root:
python -m scraper.pipeline
```

Useful environment variables:

| Variable | Default | Purpose |
|---|---|---|
| `USE_SAMPLE_DATA_FALLBACK` | `true` | Fall back to bundled sample data when a live source returns 0 results |
| `GEOCODE_CONTACT` | `nc-coastal-townhome-etl-pipeline` | Identifies the app in Nominatim's required User-Agent, per its usage policy |

This writes `data/listings.json` and `data/history.json` in place.

---

## GitHub Actions automation

`.github/workflows/daily_refresh.yml` runs daily at 12:00 UTC (and on
manual `workflow_dispatch`):

1. Checks out the repo, sets up Python 3.11, installs
   `scraper/requirements.txt`, and installs headless Chromium for
   Playwright.
2. Runs `python -m scraper.pipeline` (with a single automatic retry of the
   whole pipeline if the first attempt fails outright — the pipeline's own
   HTTP layer already retries individual requests with backoff).
3. If `data/listings.json` or `data/history.json` changed, commits and
   pushes them back to the branch (with retry-with-rebase on push
   contention), using a commit message summarizing the day's active count,
   new listings, and price drops.

No secrets or paid services are required — it uses the workflow's default
`GITHUB_TOKEN` for the push (needs `permissions: contents: write`, already
set in the workflow).

---

## Running the dashboard locally

```bash
cd dashboard
npm install
npm run dev
```

Visit `http://localhost:3000`. By default it reads the bundled snapshot at
`dashboard/public/data/listings.json`. Run `npm run sync-data` any time you
want that snapshot refreshed from the repo's `data/listings.json`.

### Decoupling data updates from redeploys

In production, set `NEXT_PUBLIC_DATA_URL` (see `dashboard/.env.example`) to
the raw GitHub URL for your fork's `data/listings.json`, e.g.:

```
NEXT_PUBLIC_DATA_URL=https://raw.githubusercontent.com/<owner>/<repo>/<branch>/data/listings.json
```

The dashboard fetches that URL with a 3-hour ISR revalidation window
(`dashboard/lib/data.ts`), so the daily Action's commits show up on the
live site automatically — no rebuild/redeploy needed. If unset, it falls
back to the bundled `public/data/listings.json` snapshot.

---

## Deploying for free

**Vercel (recommended)**
1. Push this repo to GitHub.
2. In Vercel, "Import Project" → select the repo → set the **Root
   Directory** to `dashboard`.
3. Add the `NEXT_PUBLIC_DATA_URL` environment variable pointing at your
   repo's raw `data/listings.json`.
4. Deploy — Vercel's Hobby tier is free and this app has no server-side
   secrets or paid dependencies.

**Cloudflare Pages**
1. Connect the repo, set the build directory to `dashboard`, build command
   `npm run build`, and use the Next.js on Pages adapter
   (`@cloudflare/next-on-pages`) or Cloudflare's built-in Next.js
   framework preset.
2. Set `NEXT_PUBLIC_DATA_URL` the same way as above under Pages'
   environment variables.

---

## Dashboard features

- **KPI header** — total active deals under $240k, median $/sqft, best
  builder promo rate, largest price cut, all recomputed live as filters
  change.
- **Interactive map** — React-Leaflet map over OpenStreetMap tiles;
  markers render green for deep deals (investor-eligible promo rate or a
  recent price drop) and blue otherwise. Filters: county, max price, min
  sqft, investor-promo-eligible-only.
- **Deal cards / table** — toggle between a card grid and a dense table,
  both showing builder terms, HOA, promo rate, investor eligibility, and
  gross yield.
- **Mortgage & DSCR calculator modal** — per-listing interactive
  calculator comparing monthly P&I + HOA + estimated tax/insurance (and
  resulting DSCR and cashflow) at the builder's promotional rate vs. a
  configurable standard investor rate, with adjustable down payment, term,
  and rent assumptions.

---

## Assumptions & limitations (read before using this for real investment decisions)

- **This is not financial advice.** Rent estimates, standard investor
  rates, and tax/insurance estimates in `scraper/config.py` are
  configurable placeholders standing in for paid rent-comp/rate-API feeds.
  Override them with real local data before relying on the yield/DSCR
  numbers.
- **Scraper selectors need periodic maintenance.** Target sites change
  markup; the pipeline is defensive (never crashes, always falls back to
  sample data) but selector accuracy on live sites should be spot-checked
  regularly.
- **Drive-time-to-water** defaults to a distance-based estimate (32 mph
  average); `scraper/utils/geo.py:osrm_drive_minutes()` can be enabled for
  live routing via the free public OSRM demo server, which is rate-limited
  and best-effort.
- **Known, low-risk dependency advisory:** `npm audit` reports a
  moderate/high advisory in a `postcss` version bundled *internally* by
  Next.js's own build tooling (not something this app's code invokes on
  untrusted input). It will clear on Next's own next bump; tracked
  upstream rather than worked around with a bleeding-edge major-version
  jump.
