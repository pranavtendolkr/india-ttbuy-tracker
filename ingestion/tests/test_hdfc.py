"""Parser tests for HDFC Bank."""

from __future__ import annotations

from datetime import date

from ingestion.parsers.hdfc import HDFCParser


SAMPLE_TEXT = "HDFC Bank Forex Card Rates\nDATE:15-May-2026"

# 3 column-groups per row + a disclaimers column (None at the right).
SAMPLE_TABLE = [
    [
        "CurrencyPair:", "T.T.Buying(InwRem)", "T.T.Selling(O/wRem)",
        "CurrencyPair:", "T.T.Buying(InwRem)", "T.T.Selling(O/wRem)",
        "CurrencyPair:", "T.T.Buying(InwRem)", "T.T.Selling(O/wRem)",
        "Disclaimers",
    ],
    ["Eur-USD", "1.1198", "1.2120", "AUD-SAR", "2.5205", "2.8877", "SAR-BHD", "0.0944", "0.1070", None],
    ["USD-INR", "94.1300", "97.5800", "EUR-INR", "109.27", "114.09", "GBP-INR", "124.64", "131.79", None],
]


def test_hdfc_parses_usd_inr_tt_buy(patch_pdf):
    patch_pdf(SAMPLE_TEXT, [SAMPLE_TABLE])
    rates = list(HDFCParser().parse(b"%PDF-stub"))
    assert len(rates) == 1
    rate = rates[0]
    assert rate.currency == "USD"
    assert rate.rate_value == 94.13
    assert rate.rate_type == "inward_tt_buy"
    assert rate.effective_date == date(2026, 5, 15)


def test_hdfc_ignores_eur_usd_pair(patch_pdf):
    """The Eur-USD row must not be misread as the USD rate."""
    table = [
        ["CurrencyPair:", "T.T.Buying(InwRem)", "T.T.Selling(O/wRem)"],
        ["Eur-USD", "1.1198", "1.2120"],
    ]
    patch_pdf(SAMPLE_TEXT, [table])
    assert list(HDFCParser().parse(b"%PDF-stub")) == []
