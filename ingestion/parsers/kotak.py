"""Kotak Mahindra Bank inward TT-buy parser (JS-rendered).

The Kotak rates page renders two tables: ``We Buy`` and ``We Sell``. For
inward remittance we want the ``Telegraphic Transfer`` column inside the
``We Buy`` table. Layout:
    row above table: "Card Rates valid for 15th May 2026"
    section title:   "We Buy"
    header:          [CURRENCY, Cash, Forex Card, Bills, Telegraphic Transfer]
    USD row:         [USD, 93.15, 93.79, 92.97, 94.24]
"""

from __future__ import annotations

from typing import Sequence

from ..common.browser import render_page
from ..common.html import expand_table, parse_html
from ..common.normalize import (
    normalize_currency,
    parse_decimal,
    parse_effective_date,
    today_ist,
)
from .base import BankParser, ParsedRate

PAGE_URL = "https://www.kotak.bank.in/en/rates/forex-rates.html"
WAIT_SELECTOR = "table tbody tr td"


class KotakParser(BankParser):
    BANK_SLUG = "kotak"
    PARSER_VERSION = "0.1.0"
    SOURCE_URL = PAGE_URL

    def fetch(self) -> bytes:
        return render_page(self.source_url, wait_for_selector=WAIT_SELECTOR,
                           wait_ms=4000)

    def parse(self, payload: bytes) -> Sequence[ParsedRate]:
        soup = parse_html(payload)

        for table in soup.find_all("table"):
            grid = expand_table(table)
            if not grid:
                continue
            tt_col = _find_tt_column(grid)
            if tt_col is None:
                continue
            # Confirm we're in the "We Buy" table by scanning preceding text.
            if not _is_buy_table(table):
                continue
            # Pull the effective date from text immediately above this table
            # (e.g. "Card Rates valid for 15th May 2026"), not the whole page
            # which has many unrelated "effective from ..." mentions.
            local_text = _local_context_text(table)
            effective = parse_effective_date(local_text) or today_ist()
            source_status = "ok" if parse_effective_date(local_text) else "date_inferred"

            for row in grid:
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
                        source_title="Kotak Mahindra Bank Card Rates (We Buy / TT)",
                        source_status=source_status,
                    )
                ]
        return []


def _local_context_text(table) -> str:
    """Walk back from ``table`` and return text closest-first.

    Joining closest-first means ``parse_effective_date`` will find the date
    nearest to the rate table (e.g. "Card Rates valid for 15th May 2026")
    before any unrelated "Effective ..." mentions higher up the page.
    """
    pieces: list[str] = []
    chars = 0
    for s in table.find_all_previous(string=True, limit=40):
        text = (s or "").strip()
        if not text:
            continue
        pieces.append(text)
        chars += len(text)
        if chars > 250:
            break
    return " ".join(pieces)


def _find_tt_column(grid: list[list[str]]) -> int | None:
    for header in grid[:3]:
        for idx, cell in enumerate(header):
            label = (cell or "").strip().lower()
            if label in {"telegraphic transfer", "tt", "tt buy", "tt buying"}:
                return idx
    return None


def _is_buy_table(table) -> bool:
    """Walk back from the table to find a "We Buy" / "We Sell" section header."""
    for prev in table.find_all_previous(string=True, limit=80):
        text = (prev or "").strip().lower()
        if not text:
            continue
        if "we buy" in text:
            return True
        if "we sell" in text:
            return False
    # Default to True if no marker found (some renderings inline the heading).
    return True


__all__ = ["KotakParser"]
