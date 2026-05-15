"""Run every registered parser against its live source URL and print results.

This is a developer utility. It does not touch Supabase. Useful for shaking
out parser issues against today's actual bank data.

Usage:
    python -m ingestion.tools.dryrun [slug ...]

If slugs are provided, only those parsers run; otherwise all are tried.
"""

from __future__ import annotations

import sys
import traceback
from pathlib import Path

from ..parsers import REGISTRY

DEBUG_DIR = Path("ingestion/_debug")


def _save(slug: str, payload: bytes) -> Path:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    ext = "pdf" if payload[:4] == b"%PDF" else "html"
    out = DEBUG_DIR / f"{slug}.{ext}"
    out.write_bytes(payload)
    return out


def main(argv: list[str]) -> int:
    only = set(argv[1:])
    slugs = sorted(REGISTRY.keys())
    if only:
        slugs = [s for s in slugs if s in only]
    width = max(len(s) for s in slugs) if slugs else 4
    print(f"{'slug':<{width}}  status      rate        date        notes")
    print("-" * 72)
    for slug in slugs:
        parser_cls = REGISTRY[slug]
        parser = parser_cls()
        try:
            payload = parser.fetch()
            saved = _save(slug, payload)
            try:
                parsed = list(parser.parse(payload))
            except Exception as exc:
                print(f"{slug:<{width}}  PARSE_ERR  -          -          {exc} (payload={saved})")
                traceback.print_exc(limit=2)
                continue
            if not parsed:
                print(f"{slug:<{width}}  no_data    -          -          payload={saved} url={parser.source_url}")
                continue
            for p in parsed:
                print(
                    f"{slug:<{width}}  ok         {p.rate_value:<10.4f} "
                    f"{p.effective_date.isoformat()} {p.source_status or ''}"
                )
        except Exception as exc:
            print(f"{slug:<{width}}  FETCH_ERR  -          -          {exc}")
            traceback.print_exc(limit=2)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
