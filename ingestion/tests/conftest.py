"""Shared pytest helpers for parser tests.

Most parsers ultimately call into ``ingestion.common.pdf`` (for PDFs) or
operate directly on HTML bytes. To avoid committing large binary fixtures
we synthesize PDF inputs by monkeypatching the helpers in tests, and load
HTML fixtures from disk under ``ingestion/tests/fixtures/<slug>/``.
"""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES_DIR


def fake_pdf(monkeypatch, *, text: str, tables: list[list[list[str]]]) -> None:
    """Replace pdf helpers with deterministic, in-memory data."""
    from ingestion.common import pdf as pdf_mod

    monkeypatch.setattr(pdf_mod, "all_text", lambda payload: text)
    monkeypatch.setattr(pdf_mod, "iter_pages_tables", lambda payload: iter(tables))

    # The parsers import these names directly, so patch the parser modules too.
    import importlib
    import pkgutil

    import ingestion.parsers as parsers_pkg

    for module_info in pkgutil.iter_modules(parsers_pkg.__path__):
        module = importlib.import_module(f"ingestion.parsers.{module_info.name}")
        if hasattr(module, "all_text"):
            monkeypatch.setattr(module, "all_text", lambda payload: text)
        if hasattr(module, "iter_pages_tables"):
            monkeypatch.setattr(module, "iter_pages_tables", lambda payload: iter(tables))


@pytest.fixture
def patch_pdf(monkeypatch):
    def _patch(text: str, tables: list[list[list[str]]]) -> None:
        fake_pdf(monkeypatch, text=text, tables=tables)
    return _patch
