"""HDFC Bank forex card rates PDF parser.

The HDFC Singapore-branch PDF lays out three repeated column groups per row:
    [ CurrencyPair, T.T.Buying(InwRem), T.T.Selling(O/wRem) ] * 3
followed by a disclaimers column. The USD-INR row therefore looks like:
    ['USD-INR', '94.13', '97.58', 'SAR-...', ..., None]
We find the column index of the inward TT-buy column in each group, then in
each body row look for a cell that normalizes to USD and read the
corresponding rate cell in the same group.
"""

from __future__ import annotations

from typing import Sequence

from ..common.normalize import (
    is_inward_tt_buy_label,
    normalize_currency,
    parse_decimal,
    parse_effective_date,
    today_ist,
)
from ..common.pdf import all_text, iter_pages_tables
from .base import BankParser, ParsedRate


class HDFCParser(BankParser):
    BANK_SLUG = "hdfc"
    PARSER_VERSION = "0.2.0"
    SOURCE_URL = (
        "https://v.hdfcbank.com/content/dam/hdfc-aem-microsites/"
        "singapore-site/rates/forex-card-rates.pdf"
    )

    def parse(self, payload: bytes) -> Sequence[ParsedRate]:
        text = all_text(payload)
        effective = parse_effective_date(text) or today_ist()
        source_status = "ok" if parse_effective_date(text) else "date_inferred"

        for table in iter_pages_tables(payload):
            buy_columns = _find_buying_tt_columns(table)
            if not buy_columns:
                continue
            for row in table:
                hit = _usd_rate(row, buy_columns)
                if hit is not None:
                    return [
                        ParsedRate(
                            currency="USD",
                            rate_type="inward_tt_buy",
                            rate_value=hit,
                            effective_date=effective,
                            source_title="HDFC Bank Forex Card Rates",
                            source_status=source_status,
                        )
                    ]
        return []


def _find_buying_tt_columns(table: list[list[str]]) -> list[int]:
    """All column indices in the header that look like an inward TT-buy column."""
    cols: list[int] = []
    for header in table[:4]:
        for idx, cell in enumerate(header):
            if cell and is_inward_tt_buy_label(cell) and "SELL" not in cell.upper():
                if idx not in cols:
                    cols.append(idx)
        if cols:
            break
    return cols


def _usd_rate(row: list[str], buy_columns: list[int]) -> float | None:
    # The HDFC sheet quotes pairs like ``USD-INR``, ``EUR-USD`` etc. We want
    # only the USD->INR conversion, so the pair cell must contain BOTH USD
    # and INR. Once found, the inward TT-buy rate is the next plausible
    # numeric cell to the right within the same column group.
    for c_idx, cell in enumerate(row):
        if not cell:
            continue
        upper = cell.upper()
        if "USD" not in upper or "INR" not in upper:
            continue
        # Prefer reading the rate from a known TT-buy column > c_idx.
        for buy in buy_columns:
            if buy <= c_idx or buy >= len(row):
                continue
            rate = parse_decimal(row[buy])
            if rate is not None:
                return rate
        # Otherwise fall back to the cell immediately to the right.
        if c_idx + 1 < len(row):
            rate = parse_decimal(row[c_idx + 1])
            if rate is not None:
                return rate
    return None


__all__ = ["HDFCParser"]
