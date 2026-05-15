"""ICICI Bank Micro Card / Inward Remittance rate parser."""

from __future__ import annotations

from typing import Sequence

from bs4 import BeautifulSoup

from ..common.normalize import (
    is_inward_tt_buy_label,
    normalize_currency,
    parse_decimal,
    parse_effective_date,
    today_ist,
)
from .base import BankParser, ParsedRate


class ICICIParser(BankParser):
    BANK_SLUG = "icici"
    PARSER_VERSION = "0.1.0"
    SOURCE_URL = (
        "https://instantforex.icicibank.com/instantforex/forms/MicroCardRateView.aspx"
    )

    def parse(self, payload: bytes) -> Sequence[ParsedRate]:
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
                        source_title="ICICI Bank Forex Rates",
                        source_status=source_status,
                    )
                ]
        return []


def _clean(text: str) -> str:
    return " ".join((text or "").split())


def _find_tt_buy_index(headers: list[str]) -> int | None:
    for idx, header in enumerate(headers):
        if is_inward_tt_buy_label(header):
            return idx
    return None


__all__ = ["ICICIParser"]
