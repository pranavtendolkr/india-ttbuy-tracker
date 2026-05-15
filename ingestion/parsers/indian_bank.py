"""Indian Bank forex rates parser.

The Indian Bank service-charges page links to a daily PDF under
``/wp-content/uploads/``. We discover the most recent linked PDF and parse
its TT-buy column. If the listing page already includes the rates as an
HTML table we use that directly.
"""

from __future__ import annotations

from typing import Sequence
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from ..common.http import build_session, fetch_bytes
from ..common.normalize import (
    is_inward_tt_buy_label,
    normalize_currency,
    parse_decimal,
    parse_effective_date,
    today_ist,
)
from ..common.pdf import all_text, iter_pages_tables
from .base import BankParser, ParsedRate

LISTING_URL = "https://indianbank.bank.in/service-charges-forex-rates/"


class IndianBankParser(BankParser):
    BANK_SLUG = "indian_bank"
    PARSER_VERSION = "0.1.0"
    SOURCE_URL = LISTING_URL

    def fetch(self) -> bytes:
        session = build_session()
        listing = fetch_bytes(self.source_url, session=session)
        soup = BeautifulSoup(listing, "lxml")
        pdf_url = self._find_latest_rates_pdf(soup)
        if pdf_url:
            self.source_url = pdf_url
            return fetch_bytes(pdf_url, session=session)
        return listing

    def parse(self, payload: bytes) -> Sequence[ParsedRate]:
        if payload[:4] == b"%PDF":
            return self._parse_pdf(payload)
        return self._parse_html(payload)

    def _parse_pdf(self, payload: bytes) -> Sequence[ParsedRate]:
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
                        source_title="Indian Bank Forex Rates",
                        source_status=source_status,
                    )
                ]
        return []

    def _parse_html(self, payload: bytes) -> Sequence[ParsedRate]:
        soup = BeautifulSoup(payload, "lxml")
        page_text = soup.get_text(" ", strip=True)
        effective = parse_effective_date(page_text) or today_ist()
        source_status = "ok" if parse_effective_date(page_text) else "date_inferred"
        for table in soup.find_all("table"):
            headers = [_clean(th.get_text(" ", strip=True)) for th in table.find_all("th")]
            tt_col = _find_tt_buy_index(headers)
            if tt_col is None:
                continue
            for tr in table.find_all("tr"):
                cells = [_clean(td.get_text(" ", strip=True)) for td in tr.find_all("td")]
                if len(cells) <= tt_col:
                    continue
                if not any(normalize_currency(c) == "USD" for c in cells):
                    continue
                rate = parse_decimal(cells[tt_col])
                if rate is None:
                    continue
                return [
                    ParsedRate(
                        currency="USD",
                        rate_type="inward_tt_buy",
                        rate_value=rate,
                        effective_date=effective,
                        source_title="Indian Bank Forex Rates",
                        source_status=source_status,
                    )
                ]
        return []

    @staticmethod
    def _find_latest_rates_pdf(soup: BeautifulSoup) -> str | None:
        candidates: list[str] = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "wp-content/uploads" not in href:
                continue
            if not href.lower().endswith(".pdf"):
                continue
            text = (a.get_text(" ", strip=True) or "").lower()
            if "forex" in text or "rate" in text or "card" in text:
                candidates.append(urljoin(LISTING_URL, href))
        if not candidates:
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if "wp-content/uploads" in href and href.lower().endswith(".pdf"):
                    candidates.append(urljoin(LISTING_URL, href))
        return candidates[0] if candidates else None


def _clean(text: str) -> str:
    return " ".join((text or "").split())


def _find_tt_buy_column(table: list[list[str]]) -> int | None:
    for header in table[:3]:
        for idx, cell in enumerate(header):
            if is_inward_tt_buy_label(cell):
                return idx
    return None


def _find_tt_buy_index(headers: list[str]) -> int | None:
    for idx, header in enumerate(headers):
        if is_inward_tt_buy_label(header):
            return idx
    return None


__all__ = ["IndianBankParser"]
