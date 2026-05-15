"""Parser tests for HDFC Bank."""

from __future__ import annotations

from datetime import date

from ingestion.parsers.hdfc import HDFCParser


SAMPLE_TEXT = "HDFC Bank Forex Card Rates - effective 15-MAY-2026"

SAMPLE_TABLE = [
    [
        "CURRENCY",
        "TT BUY",
        "TT SELL",
        "FCY/INR (Buy)",
        "FCY/INR (Sell)",
        "FOREX CARD BUY",
        "FOREX CARD SELL",
    ],
    ["USD", "84.0500", "85.2000", "83.95", "85.30", "83.50", "85.80"],
    ["GBP", "108.10", "109.50", "108.00", "109.60", "107.80", "110.10"],
]


def test_hdfc_parses_tt_buy(patch_pdf):
    patch_pdf(SAMPLE_TEXT, [SAMPLE_TABLE])
    rates = list(HDFCParser().parse(b"%PDF-stub"))
    assert len(rates) == 1
    rate = rates[0]
    assert rate.currency == "USD"
    assert rate.rate_value == 84.05
    assert rate.rate_type == "inward_tt_buy"
    assert rate.effective_date == date(2026, 5, 15)
