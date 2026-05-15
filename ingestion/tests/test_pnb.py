"""Parser tests for Punjab National Bank."""

from __future__ import annotations

from datetime import date

from ingestion.parsers.pnb import PNBParser


SAMPLE_TEXT = "PNB Card Rates - w.e.f. 15.05.2026"

SAMPLE_TABLE = [
    ["Currency", "TT Buying", "TT Selling", "Bill Buying", "Bill Selling"],
    ["USD", "84.05", "85.10", "83.90", "85.30"],
    ["EUR", "91.20", "92.30", "91.10", "92.40"],
]


def test_pnb_parses_tt_buy(patch_pdf):
    patch_pdf(SAMPLE_TEXT, [SAMPLE_TABLE])
    rates = list(PNBParser().parse(b"%PDF-stub"))
    assert len(rates) == 1
    rate = rates[0]
    assert rate.currency == "USD"
    assert rate.rate_value == 84.05
    assert rate.effective_date == date(2026, 5, 15)
