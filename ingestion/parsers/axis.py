"""Axis Bank inward wire remittance TT-buy rate parser.

Axis publishes a table where the column header is literally
"Inward Wire Remittance Rate (TT Buy)" and each row is
``[blank, currency_name, currency_code, rate]``. So we look for a header cell
matching the inward TT-buy pattern, then in body rows pick the cell whose
currency code normalizes to USD and read the rightmost numeric cell as the
rate.
"""

from __future__ import annotations

from typing import Sequence

from ..common.html import expand_table, iter_html_tables, parse_html
from ..common.normalize import (
    is_inward_tt_buy_label,
    normalize_currency,
    parse_decimal,
    parse_effective_date,
    today_ist,
)
from .base import BankParser, ParsedRate


class AxisParser(BankParser):
    BANK_SLUG = "axis"
    PARSER_VERSION = "0.2.0"
    SOURCE_URL = (
        "https://application.axis.bank.in/WebForms/currency-convert-forex/index.aspx"
    )

    def parse(self, payload: bytes) -> Sequence[ParsedRate]:
        soup = parse_html(payload)
        page_text = soup.get_text(" ", strip=True)
        effective = parse_effective_date(page_text) or today_ist()
        source_status = "ok" if parse_effective_date(page_text) else "date_inferred"

        for table in soup.find_all("table"):
            grid = expand_table(table)
            # Confirm this table is the inward-TT-buy table by searching the
            # first few header rows for the right label.
            if not _has_inward_tt_buy_header(grid):
                continue
            for row in grid:
                if not any(normalize_currency(c) == "USD" for c in row):
                    continue
                # Pick the last numeric cell on this row as the rate.
                rate = _last_decimal(row)
                if rate is None:
                    continue
                return [
                    ParsedRate(
                        currency="USD",
                        rate_type="inward_tt_buy",
                        rate_value=rate,
                        effective_date=effective,
                        source_title="Axis Bank Inward Wire Remittance Rate",
                        source_status=source_status,
                    )
                ]
        return []


def _has_inward_tt_buy_header(grid: list[list[str]]) -> bool:
    for row in grid[:4]:
        for cell in row:
            if is_inward_tt_buy_label(cell):
                return True
    return False


def _last_decimal(row: list[str]) -> float | None:
    for cell in reversed(row):
        v = parse_decimal(cell)
        if v is not None:
            return v
    return None


__all__ = ["AxisParser"]
