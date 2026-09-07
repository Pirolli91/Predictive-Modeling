"""
Free geocoding fallback for listings that come back from a source module
without latitude/longitude, using OpenStreetMap's public Nominatim search
API. No API key is required, but Nominatim's usage policy caps anonymous
usage at 1 request/second and requires a descriptive User-Agent -- both are
respected here. Results are cached to disk so the same address is never
looked up twice across runs.
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Optional

import requests

logger = logging.getLogger(__name__)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
CACHE_PATH = Path(__file__).resolve().parent.parent.parent / "data" / ".geocode_cache.json"
MIN_SECONDS_BETWEEN_REQUESTS = 1.0

_last_request_time = 0.0


def _load_cache() -> dict:
    if CACHE_PATH.exists():
        try:
            return json.loads(CACHE_PATH.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_cache(cache: dict) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, indent=2))


_cache = _load_cache()


def geocode_address(
    address: Optional[str], city: Optional[str], state: str, zip_code: Optional[str] = None
) -> Optional[tuple]:
    """
    Look up (latitude, longitude) for a free-form US address via Nominatim.
    Returns None if the address can't be resolved or looks too sparse to
    geocode meaningfully.
    """
    global _last_request_time

    if not address and not city:
        return None

    query_parts = [p for p in [address, city, state, zip_code, "USA"] if p]
    query = ", ".join(query_parts)

    if query in _cache:
        cached = _cache[query]
        return (cached["lat"], cached["lon"]) if cached else None

    contact = os.environ.get("GEOCODE_CONTACT", "nc-coastal-townhome-etl-pipeline")
    headers = {"User-Agent": f"nc-coastal-townhome-etl/1.0 ({contact})"}

    elapsed = time.time() - _last_request_time
    if elapsed < MIN_SECONDS_BETWEEN_REQUESTS:
        time.sleep(MIN_SECONDS_BETWEEN_REQUESTS - elapsed)

    try:
        response = requests.get(
            NOMINATIM_URL,
            params={"q": query, "format": "json", "limit": 1, "countrycodes": "us"},
            headers=headers,
            timeout=15,
        )
        _last_request_time = time.time()
        response.raise_for_status()
        results = response.json()
        if not results:
            _cache[query] = None
            _save_cache(_cache)
            return None

        lat = float(results[0]["lat"])
        lon = float(results[0]["lon"])
        _cache[query] = {"lat": lat, "lon": lon}
        _save_cache(_cache)
        return (lat, lon)
    except Exception as exc:  # noqa: BLE001 - geocoding is best-effort
        logger.warning("Geocoding failed for '%s': %s", query, exc)
        return None
