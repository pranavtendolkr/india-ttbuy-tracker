"""Parser tests for Indian Bank."""

from __future__ import annotations

from datetime import date

from bs4 import BeautifulSoup

from ingestion.parsers.indian_bank import IndianBankParser


def test_indian_bank_finds_latest_pdf_link(fixtures_dir):
    payload = (fixtures_dir / "indian_bank" / "listing.html").read_bytes()
    soup = BeautifulSoup(payload, "lxml")
    pdf_url = IndianBankParser._find_latest_rates_pdf(soup)
    assert pdf_url is not None
    assert pdf_url.endswith("Forex-Card-Rate-15052026.pdf")


SAMPLE_TEXT = "Indian Bank Forex Rates - 15/05/2026"

SAMPLE_TABLE = [
    ["Currency", "TT Buy (Inward Remittance)", "TT Sell"],
    ["USD", "84.10", "85.00"],
]


def test_indian_bank_parses_pdf(patch_pdf):
    patch_pdf(SAMPLE_TEXT, [SAMPLE_TABLE])
    parser = IndianBankParser()
    rates = list(parser.parse(b"%PDF-stub"))
    assert len(rates) == 1
    rate = rates[0]
    assert rate.currency == "USD"
    assert rate.rate_value == 84.10
    assert rate.effective_date == date(2026, 5, 15)
