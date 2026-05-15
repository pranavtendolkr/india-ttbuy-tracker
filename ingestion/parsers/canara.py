"""Canara Bank forex card rates HTML parser.

The Canara table has a two-level header:
    row 0: [ -, SELLING RATES (colspan=3), BUYING RATES (colspan=2) ]
    row 1: [ CURRENCY, TT/DDS, -, BILL, TT/CHQ, BILL ]
We expand colspan/rowspan, merge the two header rows, then pick the column
whose merged header contains both "BUYING" and a TT/cheque label. The body
USD/INR row's rate at that index is the inward TT-buy rate.
"""

from __future__ import annotations

from typing import Sequence

from ..common.html import expand_table, merge_header_rows, parse_html
from ..common.normalize import (
    is_inward_tt_buy_label,
    normalize_currency,
    parse_decimal,
    parse_effective_date,
    today_ist,
)
from .base import BankParser, ParsedRate


class CanaraParser(BankParser):
    BANK_SLUG = "canara"
    PARSER_VERSION = "0.2.0"
    SOURCE_URL = "https://canarabank.com/pages/forex-card-rates"

    def parse(self, payload: bytes) -> Sequence[ParsedRate]:
        soup = parse_html(payload)
        page_text = soup.get_text(" ", strip=True)
        effective = parse_effective_date(page_text) or today_ist()
        source_status = "ok" if parse_effective_date(page_text) else "date_inferred"

        for table in soup.find_all("table"):
            grid = expand_table(table)
            if len(grid) < 3:
                continue
            header = merge_header_rows(grid, n_header_rows=2)
            buy_col = _find_buying_tt_column(header)
            if buy_col is None:
                continue
            for row in grid[2:]:
                if not any(normalize_currency(c) == "USD" for c in row):
                    continue
                if buy_col >= len(row):
                    continue
                rate = parse_decimal(row[buy_col])
                if rate is None:
                    continue
                return [
                    ParsedRate(
                        currency="USD",
                        rate_type="inward_tt_buy",
                        rate_value=rate,
                        effective_date=effective,
                        source_title="Canara Bank Forex Card Rates",
                        source_status=source_status,
                    )
                ]
        return []


def _find_buying_tt_column(header: list[str]) -> int | None:
    """Pick the column whose merged header is a buying-side TT label.

    Falls back to the first TT-buy column if no explicit BUYING/SELLING
    grouping is present.
    """
    candidates: list[int] = []
    for idx, label in enumerate(header):
        if not is_inward_tt_buy_label(label):
            continue
        upper = label.upper()
        if "SELL" in upper:
            continue
        candidates.append(idx)
    # Prefer those that explicitly say BUY/BUYING.
    explicit_buy = [i for i in candidates if "BUY" in header[i].upper()]
    if explicit_buy:
        return explicit_buy[0]
    return candidates[0] if candidates else None


__all__ = ["CanaraParser"]
