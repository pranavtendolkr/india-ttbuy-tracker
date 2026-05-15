"""HDFC Bank forex card rates PDF parser.

The HDFC PDF has a multi-currency table with separate columns for telegraphic
transfer (TT) buying and selling, plus card rates. We pick the TT buying
column for USD.
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
    PARSER_VERSION = "0.1.0"
    SOURCE_URL = (
        "https://v.hdfcbank.com/content/dam/hdfc-aem-microsites/"
        "singapore-site/rates/forex-card-rates.pdf"
    )

    def parse(self, payload: bytes) -> Sequence[ParsedRate]:
        text = all_text(payload)
        effective = parse_effective_date(text) or today_ist()
        source_status = "ok" if parse_effective_date(text) else "date_inferred"

        for table in iter_pages_tables(payload):
            tt_col = _find_tt_buy_column(table)
            if tt_col is None:
                continue
            for row in table:
                if not any(normalize_currency(c) == "USD" for c in row):
                    continue
                if tt_col >= len(row):
                    continue
                rate = parse_decimal(row[tt_col])
                if rate is None:
                    continue
                return [
                    ParsedRate(
                        currency="USD",
                        rate_type="inward_tt_buy",
                        rate_value=rate,
                        effective_date=effective,
                        source_title="HDFC Bank Forex Card Rates",
                        source_status=source_status,
                    )
                ]
        return []


def _find_tt_buy_column(table: list[list[str]]) -> int | None:
    for header in table[:3]:
        for idx, cell in enumerate(header):
            if is_inward_tt_buy_label(cell):
                return idx
    return None


__all__ = ["HDFCParser"]
