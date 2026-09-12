"""extract — turns a snapshot of an official page into facts, each with a verbatim quote.

Rule this module must never break: a fact without a quote that appears verbatim in the fetched text is dropped
before it is written anywhere. The LLM proposes; `fetch.quote_in_text()` decides. Rates (percentages, amounts)
are accepted only when the quote itself contains the number — the model never adds numbers from memory.

Output: data/facts/<source-id>__<sha1(url)[:8]>.json
  {"url", "source_id", "fetched_at", "content_hash", "topic", "facts": [...], "dropped": n}
  fact = {"block", "country", "hs_scope", "statement": {"ru", "en"}, "quote", "quote_lang", "has_number"}

Requires ANTHROPIC_API_KEY (or an `ant auth login` profile). Model: claude-opus-5 unless PIPELINE_MODEL is set.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

from . import fetch, registry
from .validate import find_circumvention

ROOT = Path(__file__).resolve().parent.parent
FACTS_DIR = ROOT / "data" / "facts"
MODEL = os.environ.get("PIPELINE_MODEL", "claude-opus-5")

BLOCKS = ("regime", "export", "export_support", "import", "cost", "logistics", "documents", "sanctions", "supply")

SYSTEM = """You extract facts for an encyclopedia of international trade rules. You will receive the text of ONE
official government page (customs, ministry, tax or sanctions authority, statistics office).

Return ONLY a JSON object: {"facts": [ ... ]}. Each fact:
  {"block": one of %s,
   "country": ISO-3166 alpha-2 code the rule belongs to (or "" for international bodies),
   "hs_scope": list of HS prefixes the fact is limited to (empty list if it applies to all goods),
   "statement": {"ru": "...", "en": "..."},   // plain-language restatement, one or two sentences
   "quote": "...",                              // VERBATIM fragment copied from the page text, 1-3 sentences
   "quote_lang": "en" | "fr" | "zh" | "ru" | "fa" | ...,
   "has_number": true|false}                    // true if the statement contains a rate, threshold or amount

Hard rules:
1. Every fact needs a quote copied character-for-character from the page. Do not fix typos, do not translate the quote.
2. Never state a rate, threshold, date or amount that is not inside the quote.
3. Do not include advice on avoiding or circumventing sanctions, controls or checks. Describe restrictions as they are.
4. Skip navigation, disclaimers, contact details and anything that is not a rule, procedure, rate, program or restriction.
5. If the page contains no usable facts, return {"facts": []}.
""" % ", ".join(f'"{b}"' for b in BLOCKS)


def _client():
    import anthropic  # imported lazily so the rest of the pipeline works without the SDK/key

    return anthropic.Anthropic()


def _parse_json(text: str) -> dict:
    text = text.strip()
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        return {"facts": []}
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return {"facts": []}


def propose_facts(page_text: str, url: str, topic: str | None = None, client=None) -> list[dict]:
    """Asks the model for candidate facts. Pure I/O with the API; verification happens in `accept_facts`."""
    client = client or _client()
    hint = f"Topic of interest: {topic}.\n" if topic else ""
    prompt = f"{hint}Source URL: {url}\n\n<page>\n{page_text}\n</page>"
    with client.messages.stream(
        model=MODEL,
        max_tokens=16000,
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        message = stream.get_final_message()
    if message.stop_reason == "refusal":
        return []
    text = "".join(block.text for block in message.content if block.type == "text")
    facts = _parse_json(text).get("facts", [])
    return [f for f in facts if isinstance(f, dict)]


def accept_facts(candidates: list[dict], page_text: str) -> tuple[list[dict], int]:
    """Keeps only facts whose quote is verbatim in the page and whose wording passes the sanctions filter."""
    kept: list[dict] = []
    dropped = 0
    for fact in candidates:
        quote = str(fact.get("quote", "")).strip()
        statement = fact.get("statement") or {}
        if not quote or not fetch.quote_in_text(quote, page_text):
            dropped += 1
            continue
        if fact.get("block") not in BLOCKS or not isinstance(statement, dict) or not statement.get("ru"):
            dropped += 1
            continue
        texts = [str(v) for v in statement.values()] + [quote]
        if any(find_circumvention(t) for t in texts):
            dropped += 1
            continue
        kept.append(
            {
                "block": fact["block"],
                "country": str(fact.get("country", ""))[:2].upper(),
                "hs_scope": [str(h) for h in fact.get("hs_scope", []) or []],
                "statement": {"ru": statement.get("ru", ""), "en": statement.get("en", "")},
                "quote": quote,
                "quote_lang": str(fact.get("quote_lang", "")),
                "has_number": bool(fact.get("has_number", False)),
            }
        )
    return kept, dropped


def extract_url(url: str, topic: str | None = None, client=None, out_dir: Path = FACTS_DIR) -> Path:
    source = registry.find_source(url)
    if source is None:
        raise fetch.NotWhitelisted(url)
    snapshot = fetch.fetch_url(url)
    candidates = propose_facts(snapshot.text, url, topic, client)
    facts, dropped = accept_facts(candidates, snapshot.text)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{source.id}__{hashlib.sha1(url.encode('utf8')).hexdigest()[:8]}.json"
    out.write_text(
        json.dumps(
            {
                "url": url,
                "source_id": source.id,
                "fetched_at": snapshot.fetched_at,
                "content_hash": snapshot.content_hash,
                "topic": topic,
                "facts": facts,
                "dropped": dropped,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf8",
    )
    return out


def extract_registry(country: str | None = None, out_dir: Path = FACTS_DIR) -> list[Path]:
    """Extracts from every URL listed under `urls` in data/sources.yaml (optionally one country)."""
    written = []
    client = _client()
    for source in registry.load_sources():
        if country and source.country != country.upper():
            continue
        for url in source.urls:
            if not url:
                continue
            try:
                written.append(extract_url(url, topic=",".join(source.topics), client=client, out_dir=out_dir))
                print(f"ok   {source.id}: {url}")
            except Exception as exc:  # keep going: an unreachable source is a status, not a stop
                print(f"skip {source.id}: {url} ({exc.__class__.__name__}: {exc})")
    return written
