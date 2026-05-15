"""Parser tests for IDFC FIRST Bank.

The live source is JS-rendered, but ``parse()`` operates purely on rendered
HTML, so we feed it a small static fixture that mimics the post-render DOM.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from ingestion.parsers.idfc import IDFCParser


def test_idfc_parses_usdinr_bank_buys(fixtures_dir: Path):
    payload = (fixtures_dir / "idfc" / "sample.html").read_bytes()
    rates = list(IDFCParser().parse(payload))

    assert len(rates) == 1
    rate = rates[0]
    assert rate.currency == "USD"
    assert rate.rate_type == "inward_tt_buy"
    assert rate.rate_value == 94.24
    assert rate.effective_date == date(2026, 5, 15)
    assert rate.source_status == "ok"


def test_idfc_ignores_other_pairs():
    html = b"""
    <html><body><table>
      <tr><td>logo</td><td>Updated At ( 2026-05-15 09:30:00 )</td></tr>
      <tr><td rowspan="2">Currency Pair</td><td colspan="2">Telegraphic Transfer (TT)</td></tr>
      <tr><td>Bank Buys</td><td>Bank Sells</td></tr>
      <tr><td>EURINR</td><td>108.53</td><td>114.20</td></tr>
      <tr><td>GBPINR</td><td>124.88</td><td>131.40</td></tr>
    </table></body></html>
    """
    assert list(IDFCParser().parse(html)) == []
