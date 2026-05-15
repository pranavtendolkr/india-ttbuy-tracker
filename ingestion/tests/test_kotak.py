"""Parser tests for Kotak Mahindra Bank."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from ingestion.parsers.kotak import KotakParser


def test_kotak_parses_we_buy_telegraphic_transfer(fixtures_dir: Path):
    payload = (fixtures_dir / "kotak" / "sample.html").read_bytes()
    rates = list(KotakParser().parse(payload))

    assert len(rates) == 1
    rate = rates[0]
    assert rate.currency == "USD"
    assert rate.rate_type == "inward_tt_buy"
    assert rate.rate_value == 94.24
    assert rate.effective_date == date(2026, 5, 15)


def test_kotak_picks_buy_table_not_sell_table():
    """If only the We Sell table exists, the parser should yield nothing
    for the inward (buying) side rather than misreporting a sell rate."""
    html = b"""
    <html><body>
      <p>Card Rates valid for 15th May 2026</p>
      <h3>We Sell</h3>
      <table>
        <tr><th>CURRENCY</th><th>Cash</th><th>Telegraphic Transfer</th></tr>
        <tr><td>USD</td><td>96.50</td><td>95.30</td></tr>
      </table>
    </body></html>
    """
    assert list(KotakParser().parse(html)) == []
