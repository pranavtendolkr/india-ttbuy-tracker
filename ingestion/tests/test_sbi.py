"""Parser tests for State Bank of India."""

from __future__ import annotations

from datetime import date

from ingestion.parsers.sbi import SBIParser


SAMPLE_TEXT = """
STATE BANK OF INDIA
FOREX CARD RATES
Date: 15-MAY-2026 11:00 AM
"""


SAMPLE_TABLE = [
    [
        "CURRENCY",
        "TT BUY",
        "TT SELL",
        "BILL BUY",
        "BILL SELL",
        "FOREX CARD BUY",
        "FOREX CARD SELL",
    ],
    ["USD/INR", "84.10", "84.85", "84.05", "84.95", "83.95", "85.10"],
    ["EUR/INR", "91.20", "92.10", "91.15", "92.20", "91.00", "92.30"],
]


def test_sbi_parses_usd_tt_buy(patch_pdf):
    patch_pdf(SAMPLE_TEXT, [SAMPLE_TABLE])
    parser = SBIParser()
    rates = list(parser.parse(b"%PDF-stub"))

    assert len(rates) == 1
    rate = rates[0]
    assert rate.currency == "USD"
    assert rate.rate_type == "inward_tt_buy"
    assert rate.rate_value == 84.10
    assert rate.effective_date == date(2026, 5, 15)
    assert rate.source_status == "ok"


def test_sbi_falls_back_to_today_when_date_missing(patch_pdf):
    patch_pdf("STATE BANK OF INDIA FOREX CARD RATES", [SAMPLE_TABLE])
    parser = SBIParser()
    rates = list(parser.parse(b"%PDF-stub"))
    assert len(rates) == 1
    assert rates[0].source_status == "date_inferred"


def test_sbi_returns_empty_when_no_tt_buy_column(patch_pdf):
    patch_pdf(
        SAMPLE_TEXT,
        [[
            ["CURRENCY", "FOREX CARD BUY", "FOREX CARD SELL"],
            ["USD/INR", "83.95", "85.10"],
        ]],
    )
    parser = SBIParser()
    assert list(parser.parse(b"%PDF-stub")) == []


def test_sbi_skips_non_usd_rows(patch_pdf):
    patch_pdf(
        SAMPLE_TEXT,
        [[
            ["CURRENCY", "TT BUY", "TT SELL"],
            ["EUR/INR", "91.20", "92.10"],
            ["GBP/INR", "108.00", "109.00"],
        ]],
    )
    parser = SBIParser()
    assert list(parser.parse(b"%PDF-stub")) == []
