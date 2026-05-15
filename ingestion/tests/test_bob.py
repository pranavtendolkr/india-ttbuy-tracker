"""Parser tests for Bank of Baroda."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from ingestion.parsers.bob import BankOfBarodaParser


def test_bob_parses_tt_buy(fixtures_dir: Path):
    payload = (fixtures_dir / "bob" / "sample.html").read_bytes()
    rates = list(BankOfBarodaParser().parse(payload))

    assert len(rates) == 1
    rate = rates[0]
    assert rate.currency == "USD"
    assert rate.rate_type == "inward_tt_buy"
    assert rate.rate_value == 83.98
    assert rate.effective_date == date(2026, 5, 15)
