"""Parser tests for Union Bank of India."""

from __future__ import annotations

from datetime import date

from ingestion.parsers.union import UnionBankParser


SAMPLE_TEXT = "Union Bank of India Card Rates - Effective 15-May-2026"

SAMPLE_TABLE = [
    ["Currency", "TT Buy (Inward Remittance)", "TT Sell"],
    ["US DOLLAR", "84.30", "85.20"],
]


def test_union_parses_tt_buy(patch_pdf):
    patch_pdf(SAMPLE_TEXT, [SAMPLE_TABLE])
    rates = list(UnionBankParser().parse(b"%PDF-stub"))
    assert len(rates) == 1
    rate = rates[0]
    assert rate.currency == "USD"
    assert rate.rate_value == 84.30
    assert rate.effective_date == date(2026, 5, 15)
