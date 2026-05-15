"""Playwright-backed fetcher for JavaScript-rendered bank pages.

Most banks serve their rates as static HTML or PDF, which we fetch with
plain ``requests``. A few private banks (IDFC, Kotak) only render the rate
table after a client-side fetch + decrypt, so we need a real browser. This
module is imported lazily by parsers that need it, and Playwright is
declared as an optional dependency in ``requirements.txt``.

Install once:
    python -m playwright install chromium
"""

from __future__ import annotations

import logging
from contextlib import contextmanager

log = logging.getLogger(__name__)

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


@contextmanager
def chromium_page(user_agent: str = DEFAULT_USER_AGENT):
    """Yield a Playwright Page with a sensible default UA."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            context = browser.new_context(user_agent=user_agent)
            page = context.new_page()
            try:
                yield page
            finally:
                context.close()
        finally:
            browser.close()


def render_page(
    url: str,
    *,
    wait_for_selector: str | None = None,
    wait_ms: int = 5000,
    timeout_ms: int = 30000,
) -> bytes:
    """Open ``url`` in headless Chromium, optionally wait for a selector,
    and return the fully-rendered HTML.
    """
    with chromium_page() as page:
        log.info("playwright: GET %s", url)
        page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
        if wait_for_selector:
            try:
                page.wait_for_selector(wait_for_selector, timeout=timeout_ms)
            except Exception as exc:  # noqa: BLE001
                log.warning("playwright: selector %r not found: %s",
                            wait_for_selector, exc)
        else:
            page.wait_for_timeout(wait_ms)
        html = page.content()
    return html.encode("utf-8")
