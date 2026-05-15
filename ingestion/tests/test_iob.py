"""Parser tests for Indian Overseas Bank."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from ingestion.parsers.iob import IOBParser


def test_iob_parses_tt_buy(fixtures_dir: Path):
    payload = (fixtures_dir / "iob" / "sample.html").read_bytes()
    rates = list(IOBParser().parse(payload))

    assert len(rates) == 1
    rate = rates[0]
    assert rate.currency == "USD"
    assert rate.rate_type == "inward_tt_buy"
    assert rate.rate_value == 95.53
    assert rate.effective_date == date(2026, 5, 15)


def test_iob_picks_buying_side_despite_misleading_group_label():
    """IOB labels the group "SELLING RATE" but TT Buy is genuinely a buy rate."""
    html = b"""
    <html><body><table>
      <tr><td rowspan="2">CURRENCY</td><td colspan="2">SELLING RATE</td></tr>
      <tr><td>TT Buy</td><td>TT Sell</td></tr>
      <tr><td>USD</td><td>95.53</td><td>96.10</td></tr>
    </table></body></html>
    """
    rates = list(IOBParser().parse(html))
    assert len(rates) == 1
    assert rates[0].rate_value == 95.53
