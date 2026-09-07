"""
Shared scaffolding for source modules: a common exception-isolation wrapper
so that one malformed listing on a page never aborts the whole scrape, plus
a small helper for turning arbitrary price/number text into clean numerics.
"""

from __future__ import annotations

import logging
import re
from typing import Callable, Iterable, List, Optional

logger = logging.getLogger(__name__)


def safe_parse_all(items: Iterable, parse_fn: Callable[[object], dict], source_name: str) -> List[dict]:
    """
    Apply parse_fn to every item, logging and skipping any item that raises
    instead of letting one bad listing kill the whole source's results.
    """
    results = []
    for item in items:
        try:
            parsed = parse_fn(item)
            if parsed:
                results.append(parsed)
        except Exception as exc:  # noqa: BLE001 - defensive by design
            logger.warning("[%s] Failed to parse a listing: %s", source_name, exc)
            continue
    return results


_NUMERIC_PATTERN = re.compile(r"[\d,]+(?:\.\d+)?")


def parse_price_text(text: str) -> Optional[float]:
    """Turn '$219,990' or 'From $219,990' into 219990.0."""
    if not text:
        return None
    match = _NUMERIC_PATTERN.search(text.replace(",", ""))
    if not match:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None


def parse_int_text(text: str) -> Optional[int]:
    if not text:
        return None
    match = _NUMERIC_PATTERN.search(text.replace(",", ""))
    if not match:
        return None
    try:
        return int(float(match.group(0)))
    except ValueError:
        return None
