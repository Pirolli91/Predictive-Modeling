"""
Geographic helpers: Haversine distance to the coast and an optional
drive-time refinement via a free public OSRM routing server.
"""

from __future__ import annotations

import logging
import math
from typing import Optional

import requests

from scraper.config import (
    COASTAL_REFERENCE_POINTS,
    MAX_DISTANCE_TO_WATER_MILES,
    MAX_DRIVE_MINUTES_TO_WATER,
    OSRM_DEMO_SERVER,
    REQUEST_TIMEOUT_SECONDS,
)

logger = logging.getLogger(__name__)

EARTH_RADIUS_MILES = 3958.8


def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two lat/lon points, in miles."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return EARTH_RADIUS_MILES * c


def nearest_reference_point(lat: float, lon: float) -> tuple[str, float]:
    """Return (name, distance_miles) of the closest coastal reference point."""
    best_name = None
    best_distance = math.inf
    for name, ref_lat, ref_lon in COASTAL_REFERENCE_POINTS:
        distance = haversine_miles(lat, lon, ref_lat, ref_lon)
        if distance < best_distance:
            best_distance = distance
            best_name = name
    return best_name, best_distance


def estimated_drive_minutes(distance_miles: float) -> float:
    """
    Fallback drive-time estimate when live routing is unavailable: assumes
    an average of 32 mph across a mix of coastal secondary roads and
    highways, which is a reasonable proxy for short coastal NC trips.
    """
    average_speed_mph = 32.0
    return (distance_miles / average_speed_mph) * 60.0


def osrm_drive_minutes(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> Optional[float]:
    """
    Query the free public OSRM demo server for a driving duration between
    two points. Returns None on any failure (network, rate limit, bad
    response) so callers can fall back to the Haversine-based estimate.
    No API key is required, but this demo server is best-effort/rate
    limited and should not be hammered.
    """
    url = (
        f"{OSRM_DEMO_SERVER}/route/v1/driving/"
        f"{lon1},{lat1};{lon2},{lat2}"
    )
    try:
        response = requests.get(
            url,
            params={"overview": "false"},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
        routes = payload.get("routes") or []
        if not routes:
            return None
        duration_seconds = routes[0].get("duration")
        if duration_seconds is None:
            return None
        return duration_seconds / 60.0
    except Exception as exc:  # noqa: BLE001 - routing is best-effort
        logger.debug("OSRM lookup failed for (%s,%s): %s", lat1, lon1, exc)
        return None


def evaluate_proximity(
    lat: float, lon: float, use_live_routing: bool = False
) -> dict:
    """
    Determine whether a listing at (lat, lon) satisfies the coastal
    proximity constraint: within MAX_DISTANCE_TO_WATER_MILES of a coastal
    reference point OR within MAX_DRIVE_MINUTES_TO_WATER by road.

    Returns a dict with the nearest reference point, straight-line
    distance, an estimated (or live) drive time, and a boolean pass/fail.
    """
    name, distance_miles = nearest_reference_point(lat, lon)

    drive_minutes = None
    if use_live_routing:
        ref_lat, ref_lon = next(
            (r[1], r[2]) for r in COASTAL_REFERENCE_POINTS if r[0] == name
        )
        drive_minutes = osrm_drive_minutes(lat, lon, ref_lat, ref_lon)

    if drive_minutes is None:
        drive_minutes = estimated_drive_minutes(distance_miles)

    within_distance = distance_miles <= MAX_DISTANCE_TO_WATER_MILES
    within_drive_time = drive_minutes <= MAX_DRIVE_MINUTES_TO_WATER

    return {
        "nearest_water_point": name,
        "distance_to_water_miles": round(distance_miles, 2),
        "estimated_drive_minutes": round(drive_minutes, 1),
        "meets_proximity_requirement": bool(within_distance or within_drive_time),
    }
