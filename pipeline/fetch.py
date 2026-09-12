"""fetch — downloads pages from the whitelist only and keeps immutable snapshots with a hash and a date.

Rule this module must never break: `fetch_url()` refuses any URL that `registry.is_allowed()` does not cover.
Snapshots go to $SNAPSHOT_DIR (default ./snapshots, git-ignored): <sha1(url)>/<UTC timestamp>.html plus a
.txt with the extracted text and a .json with metadata. Retries with backoff; one request per host per second.
"""
from __future__ import annotations

import hashlib
import html
import json
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import httpx

from . import registry

USER_AGENT = os.environ.get("FETCH_USER_AGENT", "trade-rules-encyclopedia/0.1 (+https://github.com/Bagnar/Trade-Routes)")
SNAPSHOT_DIR = Path(os.environ.get("SNAPSHOT_DIR", "snapshots"))
_last_hit: dict[str, float] = {}


class NotWhitelisted(Exception):
    """Raised for any URL outside data/sources.yaml."""


@dataclass
class Snapshot:
    url: str
    fetched_at: str
    http_status: int
    content_hash: str
    text: str
    path: Path | None
    html: str = ""       # raw response body (HTML or other text) — for table/link parsers
    content: bytes = b""  # raw bytes — for binary exports (xlsx)


def html_to_text(raw: str) -> str:
    """Cheap, dependency-free text extraction: drops scripts, styles and tags, unescapes entities, squeezes space."""
    raw = re.sub(r"(?is)<(script|style|noscript|svg|template)\b.*?</\1>", " ", raw)
    raw = re.sub(r"(?is)<br\s*/?>|</p>|</div>|</li>|</tr>|</h[1-6]>", "\n", raw)
    raw = re.sub(r"(?is)</?(b|i|u|em|strong|span|a|sup|sub|small|mark|abbr|cite|q)\b[^>]*>", "", raw)  # inline: no space
    raw = re.sub(r"(?s)<[^>]+>", " ", raw)
    raw = html.unescape(raw)
    raw = re.sub(r"[ \t\r\f\v ]+", " ", raw)
    raw = re.sub(r"\n\s*\n+", "\n", raw)
    return raw.strip()


def normalize(text: str) -> str:
    """Whitespace- and case-insensitive form used to check whether a quote still appears in a page."""
    return re.sub(r"\s+", " ", text).strip().lower()


def quote_in_text(quote: str, text: str) -> bool:
    return normalize(quote) in normalize(text)


def _polite_wait(host: str, min_interval: float = 1.0) -> None:
    now = time.monotonic()
    last = _last_hit.get(host, 0.0)
    if now - last < min_interval:
        time.sleep(min_interval - (now - last))
    _last_hit[host] = time.monotonic()


def fetch_url(url: str, *, save: bool = True, retries: int = 3, timeout: float = 30.0, client: httpx.Client | None = None) -> Snapshot:
    if not registry.is_allowed(url):
        raise NotWhitelisted(url)
    host = registry.host_of(url)
    own_client = client is None
    client = client or httpx.Client(follow_redirects=True, headers={"User-Agent": USER_AGENT}, timeout=timeout)
    try:
        last_error: Exception | None = None
        for attempt in range(retries):
            _polite_wait(host)
            try:
                response = client.get(url)
                break
            except httpx.HTTPError as exc:  # network error: retry with backoff
                last_error = exc
                time.sleep(2**attempt)
        else:
            raise RuntimeError(f"fetch failed after {retries} attempts: {url}") from last_error
    finally:
        if own_client:
            client.close()

    text = html_to_text(response.text) if "html" in response.headers.get("content-type", "html") else response.text
    fetched_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    content_hash = hashlib.sha256(normalize(text).encode("utf8")).hexdigest()
    path = None
    if save:
        folder = SNAPSHOT_DIR / hashlib.sha1(url.encode("utf8")).hexdigest()
        folder.mkdir(parents=True, exist_ok=True)
        stem = fetched_at.replace(":", "-")
        (folder / f"{stem}.html").write_text(response.text, encoding="utf8")
        (folder / f"{stem}.txt").write_text(text, encoding="utf8")
        meta = {"url": url, "fetched_at": fetched_at, "http_status": response.status_code, "content_hash": content_hash}
        (folder / f"{stem}.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf8")
        path = folder / f"{stem}.html"
    return Snapshot(url=url, fetched_at=fetched_at, http_status=response.status_code, content_hash=content_hash, text=text, path=path, html=response.text, content=response.content)
