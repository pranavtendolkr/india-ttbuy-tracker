"""IDFC FIRST Bank inward TT-buy parser (JS-rendered).

The IDFC forex page calls ``/content/idfcfirstbank/api/forexRate`` which
returns an encrypted blob; the JS bundle decrypts it client-side. Rather
than reverse-engineer the encryption (which IDFC can rotate at will), we
let Chromium do its job and read the rendered DOM table.

Table shape after rendering:
    row 0: [logo,            "Updated At (YYYY-MM-DD HH:MM)"]
    row 1: [Currency Pair (rowspan=2), Telegraphic Transfer (TT) (colspan=2)]
    row 2: [Bank Buys, Bank Sells]
    row 3+: [USDINR, "94.24", "97.85"], [EURINR, ...], ...

We pick the row whose currency cell contains both USD and INR, and read
``Bank Buys`` (the first numeric cell) as the inward TT-buy rate.
"""

from __future__ import annotations

from typing import Sequence

from ..common.browser import render_page
from ..common.html import expand_table, parse_html
from ..common.normalize import (
    parse_decimal,
    parse_effective_date,
    today_ist,
)
from .base import BankParser, ParsedRate

PAGE_URL = "https://www.idfcfirst.bank.in/forex-rates-teletransfer"
WAIT_SELECTOR = "table tbody tr td"


class IDFCParser(BankParser):
    BANK_SLUG = "idfc"
    PARSER_VERSION = "0.1.0"
    SOURCE_URL = PAGE_URL

    def fetch(self) -> bytes:
        return render_page(self.source_url, wait_for_selector=WAIT_SELECTOR,
                           wait_ms=4000)

    def parse(self, payload: bytes) -> Sequence[ParsedRate]:
        soup = parse_html(payload)

        for table in soup.find_all("table"):
            grid = expand_table(table)
            # Pull the effective date from the table's own text, e.g.
            # "Updated At ( 2026-05-15 17:02:01 )". Falls back to today IST.
            table_text = table.get_text(" ", strip=True)
            effective = parse_effective_date(table_text) or today_ist()
            source_status = "ok" if parse_effective_date(table_text) else "date_inferred"

            for row in grid:
                pair = next((c for c in row if c and "USD" in c.upper() and "INR" in c.upper()), None)
                if not pair:
                    continue
                # First numeric cell after the currency column is "Bank Buys".
                pair_idx = row.index(pair)
                for cell in row[pair_idx + 1 :]:
                    rate = parse_decimal(cell)
                    if rate is not None:
                        return [
                            ParsedRate(
                                currency="USD",
                                rate_type="inward_tt_buy",
                                rate_value=rate,
                                effective_date=effective,
                                source_title="IDFC FIRST Bank Forex Rates (TT)",
                                source_status=source_status,
                            )
                        ]
        return []


__all__ = ["IDFCParser"]
