"""Parser tests for Axis Bank."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from ingestion.parsers.axis import AxisParser


def test_axis_parses_inward_tt_buy(fixtures_dir: Path):
    payload = (fixtures_dir / "axis" / "sample.html").read_bytes()
    rates = list(AxisParser().parse(payload))

    assert len(rates) == 1
    rate = rates[0]
    assert rate.currency == "USD"
    assert rate.rate_type == "inward_tt_buy"
    assert rate.rate_value == 94.27
    assert rate.effective_date == date(2026, 5, 15)
    assert rate.source_status == "ok"


def test_axis_returns_empty_when_only_card_rates_present():
    html = b"""
    <html><body><table>
      <thead>
        <tr><th>Currency</th><th>Forex Card Buy</th><th>Forex Card Sell</th></tr>
      </thead>
      <tbody><tr><td>USD</td><td>83.95</td><td>85.10</td></tr></tbody>
    </table></body></html>
    """
    assert list(AxisParser().parse(html)) == []
