"""Shared HTTP session with sensible defaults for bank scraping."""

from __future__ import annotations

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
DEFAULT_TIMEOUT = 30


def build_session(user_agent: str = DEFAULT_USER_AGENT) -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=1.5,
        status_forcelist=(500, 502, 503, 504),
        allowed_methods=("GET", "HEAD"),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update(
        {
            "User-Agent": user_agent,
            "Accept": "*/*",
            "Accept-Language": "en-IN,en;q=0.9",
        }
    )
    return session


def fetch_bytes(url: str, session: requests.Session | None = None) -> bytes:
    sess = session or build_session()
    response = sess.get(url, timeout=DEFAULT_TIMEOUT)
    response.raise_for_status()
    return response.content


def fetch_text(url: str, session: requests.Session | None = None) -> str:
    sess = session or build_session()
    response = sess.get(url, timeout=DEFAULT_TIMEOUT)
    response.raise_for_status()
    return response.text
