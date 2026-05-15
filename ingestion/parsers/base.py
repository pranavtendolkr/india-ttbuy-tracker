"""Base parser interface shared by all bank-specific parsers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Sequence

from ..common.http import build_session, fetch_bytes


@dataclass
class ParsedRate:
    currency: str
    rate_type: str
    rate_value: float
    effective_date: date
    source_title: str | None = None
    source_status: str | None = None
    notes: str | None = None


class BankParser:
    """Subclass per bank. Override ``parse`` and class attributes."""

    BANK_SLUG: str = ""
    PARSER_VERSION: str = "0.1.0"
    SOURCE_URL: str = ""
    SUPPORTED_CURRENCIES: tuple[str, ...] = ("USD",)

    def __init__(self, source_url: str | None = None) -> None:
        self.source_url = source_url or self.SOURCE_URL

    def fetch(self) -> bytes:
        """Download the source artifact. Override for custom behavior."""
        session = build_session()
        return fetch_bytes(self.source_url, session=session)

    def parse(self, payload: bytes) -> Sequence[ParsedRate]:
        raise NotImplementedError
