"""Daily ingestion orchestrator.

For each enabled bank in Supabase, looks up its parser by slug, fetches the
source, parses the inward TT-buy rate(s), and upserts them. Failures are
contained to a single bank so one broken source does not poison the run.
"""

from __future__ import annotations

import logging
import os
import sys
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .common.supabase_client import (
    RateRecord,
    fetch_enabled_banks,
    get_client,
    upsert_rates,
)
from .parsers import REGISTRY, BankParser, ParsedRate

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger("ingestion.run")

DEBUG_DIR = Path("ingestion/_debug")


def _debug_enabled() -> bool:
    return os.environ.get("INGESTION_DEBUG", "").lower() in {"1", "true", "yes"}


def _save_debug_payload(slug: str, payload: bytes, ext: str) -> None:
    if not _debug_enabled() or not payload:
        return
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    out = DEBUG_DIR / f"{slug}.{ext}"
    out.write_bytes(payload[:5_000_000])  # cap at ~5MB for safety
    log.info("[%s] wrote debug artifact %s (%d bytes)", slug, out, len(payload))


@dataclass
class BankResult:
    slug: str
    name: str
    status: str
    rows_written: int = 0
    error: str | None = None


def run_one_bank(bank: dict) -> tuple[BankResult, list[RateRecord]]:
    slug = bank["slug"]
    name = bank["name"]
    parser_cls: type[BankParser] | None = REGISTRY.get(slug)
    if parser_cls is None:
        return (
            BankResult(slug=slug, name=name, status="no_parser",
                       error=f"No parser registered for slug={slug}"),
            [],
        )

    parser = parser_cls(source_url=bank.get("source_url"))
    log.info("[%s] fetching %s", slug, parser.source_url)
    payload = parser.fetch()
    ext = "pdf" if payload[:4] == b"%PDF" else "html"
    try:
        parsed: list[ParsedRate] = list(parser.parse(payload))
    except Exception:
        _save_debug_payload(slug, payload, ext)
        raise
    if not parsed:
        _save_debug_payload(slug, payload, ext)
        return (
            BankResult(slug=slug, name=name, status="no_data",
                       error=f"No TT-buy rate found at {parser.source_url}"),
            [],
        )

    scraped_at = datetime.now(timezone.utc)
    records: list[RateRecord] = [
        RateRecord(
            bank_id=bank["id"],
            currency=p.currency,
            rate_type=p.rate_type,
            rate_value=p.rate_value,
            effective_date=p.effective_date,
            source_url=parser.source_url,
            source_title=p.source_title,
            parser_version=parser.PARSER_VERSION,
            source_status=p.source_status,
            notes=p.notes,
            scraped_at=scraped_at,
        )
        for p in parsed
    ]
    return (
        BankResult(slug=slug, name=name, status="ok", rows_written=len(records)),
        records,
    )


def main() -> int:
    client = get_client()
    banks = fetch_enabled_banks(client)
    if not banks:
        log.warning("No enabled banks found in Supabase. Did the seed run?")
        return 1

    results: list[BankResult] = []
    successes = 0

    for bank in banks:
        slug = bank["slug"]
        try:
            result, records = run_one_bank(bank)
            if records:
                written = upsert_rates(client, records)
                result.rows_written = written
            results.append(result)
            if result.status == "ok":
                successes += 1
                log.info("[%s] OK: wrote %d row(s)", slug, result.rows_written)
            else:
                log.warning("[%s] %s: %s", slug, result.status, result.error or "")
        except Exception as exc:  # noqa: BLE001 - we want any failure contained
            tb = traceback.format_exc(limit=4)
            log.error("[%s] FAILED: %s\n%s", slug, exc, tb)
            results.append(
                BankResult(slug=slug, name=bank.get("name", slug),
                           status="error", error=str(exc))
            )

    log.info("=" * 72)
    log.info("ingestion summary  successes=%d  total=%d", successes, len(results))
    log.info("-" * 72)
    log.info("  %-12s %-12s %-5s %s", "slug", "status", "rows", "error")
    log.info("-" * 72)
    for r in results:
        log.info(
            "  %-12s %-12s %5d %s",
            r.slug, r.status, r.rows_written, r.error or "",
        )
    log.info("=" * 72)

    if successes == 0:
        log.error("All banks failed. Exiting with non-zero status.")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
