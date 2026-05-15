"""Thin pdfplumber helpers for extracting text and tables from forex card PDFs."""

from __future__ import annotations

import io
from typing import Iterable

import pdfplumber


def open_pdf(data: bytes) -> pdfplumber.PDF:
    return pdfplumber.open(io.BytesIO(data))


def iter_pages_text(data: bytes) -> Iterable[str]:
    with open_pdf(data) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            yield text


def iter_pages_tables(data: bytes) -> Iterable[list[list[str]]]:
    with open_pdf(data) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables() or []:
                yield [
                    [(cell or "").strip() for cell in row]
                    for row in table
                ]


def all_text(data: bytes) -> str:
    return "\n".join(iter_pages_text(data))
