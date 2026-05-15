"""Helpers for normalizing currency codes, decimals, and column labels."""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Iterable

from dateutil import parser as date_parser

CURRENCY_ALIASES: dict[str, str] = {
    "USD": "USD",
    "US DOLLAR": "USD",
    "U.S. DOLLAR": "USD",
    "U S DOLLAR": "USD",
    "AMERICAN DOLLAR": "USD",
    "USD/INR": "USD",
}

# Phrases that indicate the column we want: inward remittance / TT buying.
# Different banks shorten "Telegraphic Transfer" wildly: T.T., TT, TT/DD, TT/CHQ.
# HDFC even compresses to "InwRem". Be liberal here, then the negative
# EXCLUDE_PATTERNS list filters out forex-card / cash / travel-card columns.
TT_BUY_INWARD_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"inward.*(remit|wire|rem\b)", re.IGNORECASE),
    re.compile(r"\binw[\s\.\-]*rem", re.IGNORECASE),  # HDFC: InwRem
    re.compile(r"t\.?\s*t\.?[\s\-/.]*buy(?:ing)?", re.IGNORECASE),
    re.compile(r"t\.?\s*t\.?[\s/]*(?:dd|chq|cheque)", re.IGNORECASE),  # Canara: TT/CHQ
    re.compile(r"telegraphic.*transfer.*buy", re.IGNORECASE),
)

# Phrases we explicitly do not want
EXCLUDE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"forex\s*card", re.IGNORECASE),
    re.compile(r"cash\s*(buy|sell)", re.IGNORECASE),
    re.compile(r"travel\s*card", re.IGNORECASE),
)


def normalize_currency(value: str) -> str | None:
    if not value:
        return None
    key = re.sub(r"\s+", " ", value.strip().upper())
    if key in CURRENCY_ALIASES:
        return CURRENCY_ALIASES[key]
    # Banks format the currency cell wildly: "USD/INR", "USD-INR",
    # "United States Dollar (USD)", "USA | USD". Split on every common
    # separator and a parenthesis.
    for token in re.split(r"[\s/|,\-()]+", key):
        if token in CURRENCY_ALIASES:
            return CURRENCY_ALIASES[token]
    return None


_DECIMAL_RE = re.compile(r"-?\d{1,3}(?:[,\s]\d{3})*(?:\.\d+)?|-?\d+(?:\.\d+)?")


def parse_decimal(value: str) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    match = _DECIMAL_RE.search(text)
    if not match:
        return None
    raw = match.group(0).replace(",", "").replace(" ", "")
    try:
        return float(raw)
    except ValueError:
        return None


def is_inward_tt_buy_label(label: str) -> bool:
    if not label:
        return False
    if any(p.search(label) for p in EXCLUDE_PATTERNS):
        return False
    return any(p.search(label) for p in TT_BUY_INWARD_PATTERNS)


def looks_like_usd_row(cells: Iterable[str]) -> bool:
    for cell in cells:
        if normalize_currency(cell) == "USD":
            return True
    return False


_DATE_HINT_RE = re.compile(
    r"(?:date|w\.?e\.?f\.?|with effect from|effective|"
    r"published\s+(?:on|at)|as\s+on|valid\s+from)"
    r"\s*[:\-]?\s*"
    r"([0-9]{1,2}[\-/. ][A-Za-z0-9]{2,9}[\-/. ][0-9]{2,4}|"
    r"[A-Za-z]+\s+\d{1,2},?\s*\d{4}|"
    r"\d{4}[\-/.]\d{2}[\-/.]\d{2})",
    re.IGNORECASE,
)

# Tighter fallback: require that the middle segment looks like a month name
# or a 1-2 digit number, not arbitrary words like "at".
_FALLBACK_DATE_RE = re.compile(
    r"\b(\d{1,2}[\-/. ]"
    r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec|\d{1,2})"
    r"[A-Za-z]*[\-/. ]\d{2,4})\b|"
    r"\b(\d{4}[\-/.]\d{2}[\-/.]\d{2})\b|"
    r"\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*"
    r"\s+\d{1,2},?\s*\d{4})\b",
    re.IGNORECASE,
)


def parse_effective_date(text: str) -> date | None:
    if not text:
        return None
    match = _DATE_HINT_RE.search(text)
    if match:
        candidate = match.group(1)
        try:
            return date_parser.parse(candidate, dayfirst=True).date()
        except (ValueError, TypeError):
            pass
    for raw in _FALLBACK_DATE_RE.findall(text):
        token = next((t for t in raw if t), "") if isinstance(raw, tuple) else raw
        if not token:
            continue
        try:
            return date_parser.parse(token, dayfirst=True).date()
        except (ValueError, TypeError):
            continue
    return None


def today_ist() -> date:
    import pytz

    tz = pytz.timezone("Asia/Kolkata")
    return datetime.now(tz).date()
