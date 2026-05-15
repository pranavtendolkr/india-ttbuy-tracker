"""Indian Overseas Bank forex card rates parser.

The IOB page (``/en/forex-rates``) has a single rate table. The header is
two-row but the column nesting is mislabeled by the bank itself: the *first*
group is called "SELLING RATE" and contains "TT Buy" + "TT Sell". We just
match the literal "TT Buy" sub-header and ignore the misleading group label.
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


class IOBParser(BankParser):
    BANK_SLUG = "iob"
    PARSER_VERSION = "0.1.0"
    SOURCE_URL = "https://www.iob.bank.in/en/forex-rates"

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
            tt_col = _find_tt_buy_column(header)
            if tt_col is None:
                continue
            for row in grid[2:]:
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
                        source_title="IOB Forex Card Rates",
                        source_status=source_status,
                    )
                ]
        return []


def _find_tt_buy_column(header: list[str]) -> int | None:
    """Return the column whose merged header contains the inward TT-buy label.

    IOB's header grouping is misleading (the "SELLING RATE" group actually
    contains the TT Buy column), so we ignore the group label and match on
    the sub-label directly.
    """
    for idx, label in enumerate(header):
        # Take only the rightmost segment of the merged "A | B" label
        leaf = label.rsplit("|", 1)[-1].strip()
        if not leaf:
            continue
        if is_inward_tt_buy_label(leaf) and "SELL" not in leaf.upper():
            return idx
    return None


__all__ = ["IOBParser"]
