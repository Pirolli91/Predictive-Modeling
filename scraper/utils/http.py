"""
Shared HTTP session helper: rotating user-agents, retry with exponential
backoff, and a polite randomized delay between requests so the scraper is a
well-behaved citizen against public listing aggregators.
"""

from __future__ import annotations

import logging
import random
import time
from typing import Optional

import requests

from scraper.config import (
    BACKOFF_BASE_SECONDS,
    MAX_REQUEST_DELAY_SECONDS,
    MAX_RETRIES,
    MIN_REQUEST_DELAY_SECONDS,
    REQUEST_TIMEOUT_SECONDS,
    USER_AGENTS,
)

logger = logging.getLogger(__name__)


def _random_user_agent() -> str:
    return random.choice(USER_AGENTS)


def polite_delay() -> None:
    time.sleep(random.uniform(MIN_REQUEST_DELAY_SECONDS, MAX_REQUEST_DELAY_SECONDS))


def get_with_retry(
    url: str,
    params: Optional[dict] = None,
    headers: Optional[dict] = None,
    max_retries: int = MAX_RETRIES,
) -> Optional[requests.Response]:
    """
    GET a URL with rotating user-agent headers and exponential backoff on
    failure. Returns None (rather than raising) after exhausting retries,
    so a single unreachable source never crashes the whole pipeline run.
    """
    merged_headers = {
        "User-Agent": _random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    if headers:
        merged_headers.update(headers)

    last_exception = None
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(
                url,
                params=params,
                headers=merged_headers,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            if response.status_code == 200:
                return response
            if response.status_code in (429, 503):
                logger.warning(
                    "Rate limited/unavailable (%s) fetching %s, attempt %s/%s",
                    response.status_code,
                    url,
                    attempt,
                    max_retries,
                )
            elif response.status_code >= 400:
                logger.warning(
                    "HTTP %s fetching %s, attempt %s/%s",
                    response.status_code,
                    url,
                    attempt,
                    max_retries,
                )
                if response.status_code in (404, 410):
                    return None
        except requests.RequestException as exc:
            last_exception = exc
            logger.warning(
                "Request error fetching %s (attempt %s/%s): %s",
                url,
                attempt,
                max_retries,
                exc,
            )

        if attempt < max_retries:
            backoff = BACKOFF_BASE_SECONDS * (2 ** (attempt - 1))
            backoff += random.uniform(0, 0.5)
            time.sleep(backoff)

    if last_exception:
        logger.error("Exhausted retries fetching %s: %s", url, last_exception)
    else:
        logger.error("Exhausted retries fetching %s", url)
    return None
