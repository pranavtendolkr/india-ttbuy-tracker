"""HTML table helpers.

Bank rate pages frequently use complex tables with multi-row headers, colspan,
and rowspan. We flatten each table into a uniform ``list[list[str]]`` grid so
parsers don't have to worry about merged cells.
"""

from __future__ import annotations

from typing import Iterable

from bs4 import BeautifulSoup, Tag


def parse_html(payload: bytes) -> BeautifulSoup:
    return BeautifulSoup(payload, "lxml")


def clean(text: str | None) -> str:
    if text is None:
        return ""
    return " ".join(text.split())


def expand_table(table: Tag) -> list[list[str]]:
    """Return ``table`` as a 2D grid with colspan/rowspan expanded."""
    grid: list[list[str]] = []
    pending: dict[tuple[int, int], str] = {}
    for r_idx, tr in enumerate(table.find_all("tr")):
        row: list[str] = []
        c_idx = 0
        for cell in tr.find_all(["td", "th"]):
            while (r_idx, c_idx) in pending:
                row.append(pending.pop((r_idx, c_idx)))
                c_idx += 1
            text = clean(cell.get_text(" ", strip=True))
            try:
                colspan = max(1, int(cell.get("colspan", "1")))
            except ValueError:
                colspan = 1
            try:
                rowspan = max(1, int(cell.get("rowspan", "1")))
            except ValueError:
                rowspan = 1
            for _ in range(colspan):
                row.append(text)
                for r_offset in range(1, rowspan):
                    pending[(r_idx + r_offset, c_idx)] = text
                c_idx += 1
        # Trailing pending cells (e.g. when the row ended early)
        while (r_idx, c_idx) in pending:
            row.append(pending.pop((r_idx, c_idx)))
            c_idx += 1
        grid.append(row)
    width = max((len(r) for r in grid), default=0)
    for row in grid:
        if len(row) < width:
            row.extend([""] * (width - len(row)))
    return grid


def merge_header_rows(grid: list[list[str]], n_header_rows: int = 2) -> list[str]:
    """Combine the first ``n_header_rows`` rows into a single header per column.

    Cells are joined with " | " so multi-level headers like
    ("Bank Buying Rate", "TT Buying rate") become "Bank Buying Rate | TT Buying rate".
    """
    if not grid:
        return []
    n = min(n_header_rows, len(grid))
    width = max(len(r) for r in grid[:n])
    header: list[str] = []
    for c in range(width):
        parts: list[str] = []
        for r in range(n):
            row = grid[r]
            if c < len(row):
                txt = row[c].strip()
                if txt and (not parts or parts[-1] != txt):
                    parts.append(txt)
        header.append(" | ".join(parts))
    return header


def iter_html_tables(payload: bytes) -> Iterable[list[list[str]]]:
    soup = parse_html(payload)
    for table in soup.find_all("table"):
        yield expand_table(table)
