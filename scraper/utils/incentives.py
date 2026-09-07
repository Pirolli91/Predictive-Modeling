"""
Text-mining helpers for builder promotional/incentive blurbs.

Builder listing pages typically bury financing promos and closing-cost
credits inside free-form marketing copy (e.g. "Ask about our 4.99% rate
buydown for the first year, plus up to $10,000 in closing cost assistance
for qualified buyers using preferred lending. Rate promo applies to primary
residences only."). These helpers extract structured fields from that copy
so the pipeline can populate the Builder Financing & Incentives Module.
"""

from __future__ import annotations

import re
from typing import Optional

# Matches things like "4.99%", "5.5 %", "4.99% fixed"
_RATE_PATTERN = re.compile(
    r"(\d{1,2}(?:\.\d{1,3})?)\s*%\s*"
    r"(fixed|apr|rate|for (?:the )?(?:first )?year \d|"
    r"\d{1,2}[- ]year(?: fixed)?)?",
    re.IGNORECASE,
)

_CLOSING_CREDIT_PATTERN = re.compile(
    r"\$\s?([\d,]{3,7})\s*"
    r"(?:in\s+)?(?:builder\s+)?(?:closing\s+cost|closing-cost)"
    r"(?:s)?\s*(?:credit|assistance|incentive)?",
    re.IGNORECASE,
)

_GENERIC_DOLLAR_INCENTIVE_PATTERN = re.compile(
    r"(?:up to\s+)?\$\s?([\d,]{3,7})\s*(?:in\s+)?(?:incentives|credit|savings)",
    re.IGNORECASE,
)

_PRIMARY_RESIDENCE_ONLY_PATTERNS = (
    re.compile(r"primary residences?\s+only", re.IGNORECASE),
    re.compile(r"owner[- ]occupied\s+only", re.IGNORECASE),
    re.compile(r"must be owner[- ]occupied", re.IGNORECASE),
    re.compile(r"primary residence(?:s)?\s+required", re.IGNORECASE),
    re.compile(r"not available for investment", re.IGNORECASE),
    re.compile(r"not valid for investor", re.IGNORECASE),
    re.compile(r"excludes? investment propert", re.IGNORECASE),
    re.compile(r"excludes? non[- ]owner occupied", re.IGNORECASE),
)

_INVESTOR_ELIGIBLE_PATTERNS = (
    re.compile(r"investor", re.IGNORECASE),
    re.compile(r"investment purchase", re.IGNORECASE),
    re.compile(r"non[- ]owner occupied", re.IGNORECASE),
    re.compile(r"second home", re.IGNORECASE),
    re.compile(r"rental propert", re.IGNORECASE),
)


def extract_rate_promo(text: str) -> Optional[str]:
    """Pull the first plausible mortgage-rate promo mention out of text."""
    if not text:
        return None
    match = _RATE_PATTERN.search(text)
    if not match:
        return None
    rate, qualifier = match.group(1), match.group(2)
    qualifier = (qualifier or "").strip()
    if qualifier:
        return f"{rate}% {qualifier}"
    return f"{rate}%"


def extract_closing_cost_credit(text: str) -> Optional[str]:
    """Pull a builder closing-cost credit dollar amount out of text."""
    if not text:
        return None
    match = _CLOSING_CREDIT_PATTERN.search(text)
    if not match:
        match = _GENERIC_DOLLAR_INCENTIVE_PATTERN.search(text)
    if not match:
        return None
    amount = match.group(1)
    return f"${amount} builder credit"


def extract_investor_eligibility(text: str) -> str:
    """
    Classify whether a promo appears restricted to primary residences,
    explicitly open to investors, or unspecified in the source text.

    Returns one of: "primary_residence_only", "investor_eligible",
    "unspecified".
    """
    if not text:
        return "unspecified"

    for pattern in _PRIMARY_RESIDENCE_ONLY_PATTERNS:
        if pattern.search(text):
            return "primary_residence_only"

    for pattern in _INVESTOR_ELIGIBLE_PATTERNS:
        if pattern.search(text):
            return "investor_eligible"

    return "unspecified"


def parse_incentive_text(raw_text: str) -> dict:
    """Run all extractors over a single raw incentive text blob."""
    raw_text = (raw_text or "").strip()
    return {
        "builder_rate_promo": extract_rate_promo(raw_text),
        "closing_cost_credit": extract_closing_cost_credit(raw_text),
        "investor_eligibility_flag": extract_investor_eligibility(raw_text),
        "raw_incentive_text": raw_text or None,
    }
