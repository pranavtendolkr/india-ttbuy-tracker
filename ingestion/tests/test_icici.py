"""Parser tests for ICICI Bank."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from ingestion.parsers.icici import ICICIParser


def test_icici_parses_inward_tt_buy(fixtures_dir: Path):
    payload = (fixtures_dir / "icici" / "sample.html").read_bytes()
    rates = list(ICICIParser().parse(payload))

    assert len(rates) == 1
    rate = rates[0]
    assert rate.currency == "USD"
    assert rate.rate_type == "inward_tt_buy"
    assert rate.rate_value == 94.17
    assert rate.effective_date == date(2026, 5, 15)
    assert rate.source_status == "ok"
