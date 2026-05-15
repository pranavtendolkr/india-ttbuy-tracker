"""Thin Supabase client wrapper for ingestion writes and bank lookups."""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from typing import Iterable

from supabase import Client, create_client


@dataclass
class RateRecord:
    bank_id: str
    currency: str
    rate_type: str
    rate_value: float
    effective_date: date
    source_url: str | None = None
    source_title: str | None = None
    parser_version: str | None = None
    source_status: str | None = None
    notes: str | None = None
    scraped_at: datetime | None = None

    def to_row(self) -> dict:
        row = asdict(self)
        if isinstance(row["effective_date"], date):
            row["effective_date"] = row["effective_date"].isoformat()
        if row["scraped_at"] is None:
            row["scraped_at"] = datetime.now(timezone.utc).isoformat()
        elif isinstance(row["scraped_at"], datetime):
            row["scraped_at"] = row["scraped_at"].isoformat()
        return row


def get_client() -> Client:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in the environment."
        )
    return create_client(url, key)


def fetch_enabled_banks(client: Client) -> list[dict]:
    response = (
        client.table("banks")
        .select("id, name, slug, source_url, parser_type, enabled")
        .eq("enabled", True)
        .order("slug")
        .execute()
    )
    return list(response.data or [])


def upsert_rates(client: Client, records: Iterable[RateRecord]) -> int:
    rows = [record.to_row() for record in records]
    if not rows:
        return 0
    response = (
        client.table("rates")
        .upsert(rows, on_conflict="bank_id,currency,rate_type,effective_date")
        .execute()
    )
    return len(response.data or rows)
