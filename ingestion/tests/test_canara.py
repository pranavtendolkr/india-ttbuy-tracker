"""Parser tests for Canara Bank."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from ingestion.parsers.canara import CanaraParser


def test_canara_parses_buying_tt(fixtures_dir: Path):
    payload = (fixtures_dir / "canara" / "sample.html").read_bytes()
    rates = list(CanaraParser().parse(payload))

    assert len(rates) == 1
    rate = rates[0]
    assert rate.currency == "USD"
    assert rate.rate_type == "inward_tt_buy"
    assert rate.rate_value == 95.5125
    assert rate.effective_date == date(2026, 5, 15)
