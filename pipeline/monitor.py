"""monitor — re-reads every source behind a published fact and checks that the quote is still there.

This is the daily "AI re-check" of the site (docs/concept.md, section 6.4): it needs no LLM. For every fact in
web/data/pages and web/data/supply that carries a `quote` and a `stamp.url`:
  - fetch the URL (whitelist only, via fetch.py);
  - if the quote is still present   -> stamp becomes "ok", "проверено <date>";
  - if the page changed and the quote is gone -> stamp becomes "warn", "источник изменился <date> — требует проверки";
  - if the page cannot be fetched   -> stamp becomes "none", "источник недоступен с <date>" (status unavailable).
Facts without a quote are never upgraded to "ok" — no quote, no claim.

Rule this module must never break: it never rewrites a statement; it only changes stamp status/label/date.
Without changes there is nothing to report (and, later, no e-mails).

Writes data/monitor-report.md and returns exit code 0 (no changes), 3 (changes written) or 1 (error).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Iterable

from . import fetch, registry

ROOT = Path(__file__).resolve().parent.parent
PAGE_DIRS = (ROOT / "web" / "data" / "pages", ROOT / "web" / "data" / "supply")
REPORT = ROOT / "data" / "monitor-report.md"

MONTHS_RU = ["янв", "фев", "мар", "апр", "мая", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"]


def ru_date(d: date) -> str:
    return f"{d.day} {MONTHS_RU[d.month - 1]} {d.year}"


def iter_facts(doc: dict) -> Iterable[dict]:
    """Yields every dict that looks like a fact (has `stamp`) anywhere in the page content."""
    if isinstance(doc, dict):
        if "stamp" in doc and isinstance(doc.get("stamp"), dict):
            yield doc
        for value in doc.values():
            yield from iter_facts(value)
    elif isinstance(doc, list):
        for item in doc:
            yield from iter_facts(item)


@dataclass
class Result:
    checked: int = 0
    confirmed: int = 0
    changed: int = 0
    unavailable: int = 0
    skipped_no_quote: int = 0
    lines: list[str] = field(default_factory=list)


def check_fact(fact: dict, text: str | None, today: date) -> str:
    """Updates the fact's stamp in place; returns 'confirmed' | 'changed' | 'unavailable'."""
    stamp = fact["stamp"]
    if text is None:
        stamp["status"] = "none"
        stamp["label"] = f"источник недоступен с {ru_date(today)}"
        return "unavailable"
    if fetch.quote_in_text(fact["quote"], text):
        stamp["status"] = "ban" if fact.get("ban") else "ok"
        stamp["label"] = ("запрет, " if fact.get("ban") else "") + f"проверено {ru_date(today)}"
        stamp["verifiedAt"] = today.isoformat()
        return "confirmed"
    stamp["status"] = "warn"
    stamp["label"] = f"источник изменился {ru_date(today)} — требует проверки"
    return "changed"


def run(page_dirs: Iterable[Path] = PAGE_DIRS, today: date | None = None, fetcher=None) -> Result:
    today = today or date.today()
    fetcher = fetcher or (lambda url: fetch.fetch_url(url, save=False).text)
    sources = registry.load_sources()
    cache: dict[str, str | None] = {}
    result = Result()

    for folder in page_dirs:
        for path in sorted(folder.glob("*.json")):
            doc = json.loads(path.read_text(encoding="utf8"))
            dirty = False
            for fact in iter_facts(doc):
                quote, url = fact.get("quote"), fact["stamp"].get("url")
                if not quote or not url:
                    result.skipped_no_quote += 1
                    continue
                if not registry.is_allowed(url, sources):
                    result.lines.append(f"- {path.name}: URL вне белого списка, пропущено: {url}")
                    continue
                if url not in cache:
                    try:
                        cache[url] = fetcher(url)
                    except Exception as exc:  # unreachable source is a status, not a crash
                        cache[url] = None
                        result.lines.append(f"- недоступен: {url} ({exc.__class__.__name__})")
                before = dict(fact["stamp"])
                outcome = check_fact(fact, cache[url], today)
                result.checked += 1
                setattr(result, outcome if outcome != "confirmed" else "confirmed", getattr(result, outcome if outcome != "confirmed" else "confirmed") + 1)
                if fact["stamp"] != before:
                    dirty = True
                    if outcome != "confirmed":
                        result.lines.append(f"- {path.name}: {outcome} — {url}")
            if dirty:
                path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    return result


def write_report(result: Result, today: date | None = None, path: Path = REPORT) -> None:
    today = today or date.today()
    body = [
        f"# Проверка источников — {today.isoformat()}",
        "",
        f"- фактов с цитатой проверено: {result.checked}",
        f"- цитата на месте: {result.confirmed}",
        f"- источник изменился, требует проверки: {result.changed}",
        f"- источник недоступен: {result.unavailable}",
        f"- фактов без цитаты (не проверяются и не публикуются как «проверено»): {result.skipped_no_quote}",
        "",
    ]
    if result.lines:
        body += ["## Что изменилось", ""] + result.lines + [""]
    path.write_text("\n".join(body), encoding="utf8")


def main(argv=None) -> int:
    today = date.today()
    result = run(today=today)
    write_report(result, today)
    print(REPORT.read_text(encoding="utf8"))
    return 3 if (result.changed or result.unavailable or result.confirmed) else 0
