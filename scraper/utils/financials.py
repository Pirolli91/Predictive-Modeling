"""
Investment metric calculations: rent proxy, gross rental yield, amortized
mortgage payments, and DSCR (debt service coverage ratio) comparisons
between a builder's promotional rate and standard prevailing investor
financing.

All of these are pure functions so they can be unit tested independently
and mirrored on the frontend for the interactive calculator.
"""

from __future__ import annotations

from typing import Optional

from scraper.config import (
    COUNTY_RENT_MULTIPLIERS,
    DEFAULT_INVESTOR_DOWN_PAYMENT_PCT,
    DEFAULT_LOAN_TERM_YEARS,
    DEFAULT_RENT_PER_SQFT_MONTHLY,
    ESTIMATED_ANNUAL_TAX_INSURANCE_PCT_OF_PRICE,
    STANDARD_INVESTOR_RATE_PCT,
)


def estimate_monthly_rent(
    sqft: Optional[float],
    county: Optional[str],
    rent_per_sqft_override: Optional[float] = None,
) -> Optional[float]:
    """
    Proxy for expected gross monthly rent: base rent/sqft rate times a
    county multiplier times square footage. Returns None if sqft is
    unknown, since rent cannot be estimated without it.
    """
    if not sqft or sqft <= 0:
        return None

    rate = rent_per_sqft_override or DEFAULT_RENT_PER_SQFT_MONTHLY
    multiplier = COUNTY_RENT_MULTIPLIERS.get(county or "", 1.0)
    return round(sqft * rate * multiplier, 2)


def gross_rental_yield_pct(
    monthly_rent: Optional[float], price: Optional[float]
) -> Optional[float]:
    """Annualized gross rental yield as a percentage of purchase price."""
    if not monthly_rent or not price or price <= 0:
        return None
    annual_rent = monthly_rent * 12
    return round((annual_rent / price) * 100, 2)


def monthly_principal_and_interest(
    loan_amount: float, annual_rate_pct: float, term_years: int = DEFAULT_LOAN_TERM_YEARS
) -> float:
    """Standard fixed-rate amortized monthly P&I payment."""
    if loan_amount <= 0:
        return 0.0

    monthly_rate = (annual_rate_pct / 100) / 12
    num_payments = term_years * 12

    if monthly_rate == 0:
        return round(loan_amount / num_payments, 2)

    payment = (
        loan_amount
        * (monthly_rate * (1 + monthly_rate) ** num_payments)
        / ((1 + monthly_rate) ** num_payments - 1)
    )
    return round(payment, 2)


def investor_debt_service_estimate(
    price: float,
    down_payment_pct: float = DEFAULT_INVESTOR_DOWN_PAYMENT_PCT,
    annual_rate_pct: float = STANDARD_INVESTOR_RATE_PCT,
    term_years: int = DEFAULT_LOAN_TERM_YEARS,
) -> dict:
    """
    Monthly P&I at standard prevailing investor financing terms
    (20-25% down, market investor rate) for comparison against a builder's
    promotional buydown rate.
    """
    down_payment = price * down_payment_pct
    loan_amount = price - down_payment
    monthly_pi = monthly_principal_and_interest(loan_amount, annual_rate_pct, term_years)
    return {
        "down_payment_pct": down_payment_pct,
        "down_payment_amount": round(down_payment, 2),
        "loan_amount": round(loan_amount, 2),
        "annual_rate_pct": annual_rate_pct,
        "monthly_pi": monthly_pi,
    }


def builder_promo_debt_service_estimate(
    price: float,
    builder_rate_pct: Optional[float],
    down_payment_pct: float = DEFAULT_INVESTOR_DOWN_PAYMENT_PCT,
    term_years: int = DEFAULT_LOAN_TERM_YEARS,
) -> Optional[dict]:
    """Same shape as investor_debt_service_estimate but using the builder's
    promotional rate, when one was successfully parsed from listing text."""
    if builder_rate_pct is None:
        return None
    return investor_debt_service_estimate(
        price=price,
        down_payment_pct=down_payment_pct,
        annual_rate_pct=builder_rate_pct,
        term_years=term_years,
    )


def estimated_monthly_taxes_insurance(price: Optional[float]) -> Optional[float]:
    if not price:
        return None
    return round((price * ESTIMATED_ANNUAL_TAX_INSURANCE_PCT_OF_PRICE) / 12, 2)


def dscr(
    monthly_rent: Optional[float],
    monthly_debt_service: Optional[float],
    monthly_hoa: Optional[float] = 0,
    monthly_taxes_insurance: Optional[float] = 0,
) -> Optional[float]:
    """
    Debt Service Coverage Ratio = gross monthly rent / (P&I + HOA + taxes
    & insurance). A DSCR >= 1.0 means rent covers the full housing
    payment; investor lenders typically look for 1.0-1.25+.
    """
    if not monthly_rent or not monthly_debt_service:
        return None

    total_obligation = monthly_debt_service + (monthly_hoa or 0) + (monthly_taxes_insurance or 0)
    if total_obligation <= 0:
        return None

    return round(monthly_rent / total_obligation, 2)


def parse_rate_string_to_float(rate_str: Optional[str]) -> Optional[float]:
    """
    Extract the leading numeric rate from strings like "4.99% fixed" or
    "5.5% 30-year fixed" for use in payment math.
    """
    if not rate_str:
        return None
    digits = ""
    for ch in rate_str:
        if ch.isdigit() or ch == ".":
            digits += ch
        elif digits:
            break
    try:
        return float(digits) if digits else None
    except ValueError:
        return None


def compute_investment_metrics(
    price: float,
    sqft: Optional[float],
    county: Optional[str],
    builder_rate_promo: Optional[str],
    estimated_hoa_fee_monthly: Optional[float] = 0,
) -> dict:
    """
    Convenience wrapper that computes the full investment metrics block for
    a single listing, given already-parsed fields.
    """
    monthly_rent = estimate_monthly_rent(sqft, county)
    yield_pct = gross_rental_yield_pct(monthly_rent, price)

    investor_terms = investor_debt_service_estimate(price)
    builder_rate_pct = parse_rate_string_to_float(builder_rate_promo)
    builder_terms = builder_promo_debt_service_estimate(price, builder_rate_pct)

    monthly_tax_ins = estimated_monthly_taxes_insurance(price)

    investor_dscr = dscr(
        monthly_rent,
        investor_terms["monthly_pi"],
        estimated_hoa_fee_monthly,
        monthly_tax_ins,
    )
    builder_dscr = (
        dscr(
            monthly_rent,
            builder_terms["monthly_pi"],
            estimated_hoa_fee_monthly,
            monthly_tax_ins,
        )
        if builder_terms
        else None
    )

    return {
        "estimated_monthly_rent": monthly_rent,
        "gross_rental_yield_pct": yield_pct,
        "estimated_monthly_taxes_insurance": monthly_tax_ins,
        "investor_debt_service": investor_terms,
        "builder_promo_debt_service": builder_terms,
        "investor_dscr": investor_dscr,
        "builder_promo_dscr": builder_dscr,
    }
