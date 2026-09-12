"""validate — rule-based checks that replace human moderation. No LLM here.

Checks (each returns a list of Violation, empty = pass):
  - whitelist:      every stamp URL belongs to a domain in data/sources.yaml;
  - quotes:         a fact stamped "ok" (verified) must carry a non-empty quote and a URL — no quote, no claim;
  - numbers:        a fact about duty/VAT/export duty may contain a number only if it is backed by the rates
                    layer (`rate_ref`) — otherwise the number must not be published;
  - circumvention:  for sanctioned pairs, statements must not contain "how to get around" wording;
  - demo:           any fact whose stamp label says "демо" must live on a page flagged isDemo.

Rule this module must never break: it rejects, it never rewrites. Tests live in pipeline/tests.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from . import registry
from .monitor import PAGE_DIRS, iter_facts

# Wording that describes evading sanctions (docs/sanctions-policy.md, "Чего сайт не делает"). Lower-case stems.
CIRCUMVENTION_PATTERNS = [
    r"обойти санкци", r"обход санкци", r"в обход",
    # "через третьи страны" is fine as a description of a restriction; it is advice only after an action verb.
    r"(можно|используйте|используя|платите|оплатить|провести|проводите|поставляйте|отгружайте|переводите)\b[^.]{0,60}через (посредник|третью страну|третьи страны)",
    r"переоформ\w* происхожден", r"подмен\w* происхожден", r"сменить флаг", r"перефлаг", r"дружественн\w+ банк",
    r"теневой флот", r"скрыть\w* происхожден", r"избежать проверк", r"обойти проверк", r"обойти ограничени",
    r"circumvent", r"evade sanctions", r"sanctions evasion", r"shadow fleet", r"disguise the origin", r"reflag",
]

# Fact keys / statement stems where a bare number is a rate and must come from the rates table.
RATE_STEMS = ("пошлин", "ндс", "gst", "hst", "акциз", "ставк", "duty", "tariff", "vat")
NUMBER = re.compile(r"\d+(?:[.,]\d+)?\s?%")


@dataclass(frozen=True)
class Violation:
    rule: str
    page: str
    detail: str


def _text(fact: dict) -> str:
    text = fact.get("text", "")
    if isinstance(text, dict):
        text = " ".join(str(v) for v in text.values())
    return str(text)


def check_whitelist(doc: dict, page: str, sources=None) -> list[Violation]:
    sources = sources if sources is not None else registry.load_sources()
    out = []
    for fact in iter_facts(doc):
        url = fact["stamp"].get("url")
        if url and not registry.is_allowed(url, sources):
            out.append(Violation("whitelist", page, f"URL вне белого списка: {url}"))
    return out


def check_quotes(doc: dict, page: str) -> list[Violation]:
    if doc.get("isDemo"):
        return []  # demo fixtures reproduce the mockups' stamps; the page carries a "Демо-данные" band instead
    out = []
    for fact in iter_facts(doc):
        stamp = fact["stamp"]
        if stamp.get("status") in ("ok", "ban") and "демо" not in stamp.get("label", "").lower():
            if not fact.get("quote"):
                out.append(Violation("quotes", page, f"факт со статусом «проверено» без цитаты: {_text(fact)[:80]}"))
            if not stamp.get("url"):
                out.append(Violation("quotes", page, f"факт со статусом «проверено» без URL: {_text(fact)[:80]}"))
    return out


def check_numbers(doc: dict, page: str) -> list[Violation]:
    if doc.get("isDemo"):
        return []  # demo fixtures carry illustrative numbers by design and say so on the page
    out = []
    for fact in iter_facts(doc):
        text = _text(fact).lower()
        if any(stem in text for stem in RATE_STEMS) and NUMBER.search(text) and not fact.get("rate_ref"):
            out.append(Violation("numbers", page, f"процент без ссылки на таблицу rates: {text[:80]}"))
    return out


def find_circumvention(text: str) -> list[str]:
    lowered = text.lower()
    return [p for p in CIRCUMVENTION_PATTERNS if re.search(p, lowered)]


def check_circumvention(doc: dict, page: str) -> list[Violation]:
    if not doc.get("sanctions") and not doc.get("corridor", {}).get("is_sanctioned"):
        return []
    out = []
    texts = [_text(f) for f in iter_facts(doc)]
    texts += [i["text"] for k in ("pros", "cons") for i in doc.get("verdict", {}).get(k, [])]
    texts += [doc["sanctions"]["text"]] if doc.get("sanctions") else []
    for text in texts:
        hits = find_circumvention(text)
        # The site's own policy sentence ("не подсказывает, как их обойти") is allowed.
        if hits and not re.search(r"не подсказыва\w+, как", text.lower()):
            out.append(Violation("circumvention", page, f"{hits}: {text[:80]}"))
    return out


def check_demo(doc: dict, page: str) -> list[Violation]:
    out = []
    for fact in iter_facts(doc):
        if "демо" in fact["stamp"].get("label", "").lower() and not doc.get("isDemo"):
            out.append(Violation("demo", page, "печать «демо» на странице без isDemo"))
    return out


def validate_doc(doc: dict, page: str, sources=None) -> list[Violation]:
    return (
        check_whitelist(doc, page, sources)
        + check_quotes(doc, page)
        + check_numbers(doc, page)
        + check_circumvention(doc, page)
        + check_demo(doc, page)
    )


def validate_dirs(page_dirs: Iterable[Path] = PAGE_DIRS) -> list[Violation]:
    sources = registry.load_sources()
    violations: list[Violation] = []
    for folder in page_dirs:
        for path in sorted(folder.glob("*.json")):
            violations += validate_doc(json.loads(path.read_text(encoding="utf8")), path.name, sources)
    return violations


def main(argv=None) -> int:
    violations = validate_dirs()
    for v in violations:
        print(f"[{v.rule}] {v.page}: {v.detail}")
    print(f"{len(violations)} violation(s)")
    return 1 if violations else 0
