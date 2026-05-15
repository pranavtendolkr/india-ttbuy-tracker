"""State Bank of India - FOREX_CARD_RATES.pdf parser.

The SBI rate sheet is a multi-currency PDF table. The columns we want are the
"TT BUY" rate per currency, with an effective date in the document header.
SBI labels the inward remittance rate as "TT BUY"; this is the same rate that
applies when USD is wired into an SBI account and converted to INR.
"""

from __future__ import annotations

from datetime import date
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


class SBIParser(BankParser):
    BANK_SLUG = "sbi"
    PARSER_VERSION = "0.1.0"
    SOURCE_URL = "https://sbi.co.in/documents/16012/1400784/FOREX_CARD_RATES.pdf"

    def parse(self, payload: bytes) -> Sequence[ParsedRate]:
        text = all_text(payload)
        effective = parse_effective_date(text) or today_ist()
        source_status = "ok" if parse_effective_date(text) else "date_inferred"

        results: list[ParsedRate] = []
        for table in iter_pages_tables(payload):
            tt_buy_col = self._find_tt_buy_column(table)
            if tt_buy_col is None:
                continue
            for row in table:
                rate = self._extract_usd_rate(row, tt_buy_col)
                if rate is not None:
                    results.append(
                        ParsedRate(
                            currency="USD",
                            rate_type="inward_tt_buy",
                            rate_value=rate,
                            effective_date=effective,
                            source_title="SBI FOREX CARD RATES",
                            source_status=source_status,
                        )
                    )
                    break  # one USD row per page is enough
            if results:
                break
        return results

    @staticmethod
    def _find_tt_buy_column(table: list[list[str]]) -> int | None:
        # Header row may span 1-2 lines; check first 3 rows for a TT BUY column.
        for header in table[:3]:
            for idx, cell in enumerate(header):
                if is_inward_tt_buy_label(cell):
                    return idx
        return None

    @staticmethod
    def _extract_usd_rate(row: list[str], col: int) -> float | None:
        if col >= len(row):
            return None
        if not any(normalize_currency(c) == "USD" for c in row):
            return None
        return parse_decimal(row[col])


__all__ = ["SBIParser"]
