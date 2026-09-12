"""registry — the whitelist of official sources (data/sources.yaml).

Rule this module must never break: the pipeline reads only domains listed here. Anything else is refused by
`is_allowed()` before a single byte is fetched.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

import yaml

ROOT = Path(__file__).resolve().parent.parent
SOURCES_FILE = ROOT / "data" / "sources.yaml"


@dataclass(frozen=True)
class Source:
    id: str
    agency: str
    domain: str
    country: str | None
    topics: tuple[str, ...]
    priority: int
    status: str
    path_prefix: str | None = None
    urls: tuple[str, ...] = field(default_factory=tuple)


def load_sources(path: Path = SOURCES_FILE) -> list[Source]:
    doc = yaml.safe_load(path.read_text(encoding="utf8"))
    sources: list[Source] = []

    def add(entry: dict, country: str | None) -> None:
        sources.append(
            Source(
                id=entry["id"],
                agency=entry["agency"],
                domain=entry["domain"].lower(),
                country=country,
                topics=tuple(entry.get("topics", [])),
                priority=int(entry.get("priority", 2)),
                status=entry.get("status", "to_verify"),
                path_prefix=entry.get("path_prefix"),
                urls=tuple(u if isinstance(u, str) else u.get("url", "") for u in entry.get("urls", []) or []),
            )
        )

    for code, country in (doc.get("countries") or {}).items():
        for entry in country.get("sources", []):
            add(entry, code)
    for section in ("sanctions_authorities", "export_control_regimes", "international", "logistics_indices"):
        for entry in doc.get(section) or []:
            add(entry, None)
    return sources


def host_of(url: str) -> str:
    return (urlparse(url).hostname or "").lower()


def matches(source: Source, url: str) -> bool:
    host = host_of(url)
    if not (host == source.domain or host.endswith("." + source.domain)):
        return False
    if source.path_prefix:
        return urlparse(url).path.startswith(source.path_prefix)
    return True


def find_source(url: str, sources: list[Source] | None = None) -> Source | None:
    """Returns the registry entry that covers `url`, or None when the URL is outside the whitelist."""
    for source in sources if sources is not None else load_sources():
        if matches(source, url):
            return source
    return None


def is_allowed(url: str, sources: list[Source] | None = None) -> bool:
    return find_source(url, sources) is not None
