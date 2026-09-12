"""extract — turns a snapshot of an official page into facts, each with a verbatim quote.

Rule this module must never break: a fact without a quote that appears verbatim in the fetched text is dropped
before it is written anywhere. The LLM proposes; `fetch.quote_in_text()` decides. Rates (percentages, amounts)
are accepted only when the quote itself contains the number — the model never adds numbers from memory.

Output: data/facts/<source-id>__<sha1(url)[:8]>.json
  {"url", "source_id", "fetched_at", "content_hash", "topic", "facts": [...], "dropped": n}
  fact = {"block", "country", "hs_scope", "statement": {"ru", "en"}, "quote", "quote_lang", "has_number", "targets"}

Requires ANTHROPIC_API_KEY (or an `ant auth login` profile). Model: claude-opus-5 unless PIPELINE_MODEL is set
(claude-sonnet-5 is the cheaper option).

Spending guards (all enforced here, not in the workflow):
  - unchanged pages are never re-sent to the model (content hash);
  - PIPELINE_MAX_PAGES (default 40) model calls per run;
  - PIPELINE_MAX_USD (default 5) estimated spend per run, computed from the API's own token usage;
  - PIPELINE_MONTHLY_USD (default 15) per calendar month, tracked in the committed ledger data/usage.json;
  - PIPELINE_MAX_PAGE_CHARS (default 200000): a larger page is skipped with a note, never truncated silently;
  - a credit/billing error stops the run.
Batch mode (--batch, used by daily-check.yml) sends the pages through the Message Batches API at half price;
a batch that is still processing when the run ends is remembered in the ledger and picked up next run.
Every run writes data/extract-report.md (pages, tokens, dollars this run and this month).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path

from . import fetch, registry
from .validate import find_circumvention

ROOT = Path(__file__).resolve().parent.parent
FACTS_DIR = ROOT / "data" / "facts"
USAGE_FILE = ROOT / "data" / "usage.json"
REPORT_FILE = ROOT / "data" / "extract-report.md"
MODEL = os.environ.get("PIPELINE_MODEL", "claude-opus-5")
MAX_PAGES = int(os.environ.get("PIPELINE_MAX_PAGES", "40"))
MAX_USD = float(os.environ.get("PIPELINE_MAX_USD", "5"))
MONTHLY_USD = float(os.environ.get("PIPELINE_MONTHLY_USD", "15"))
MAX_PAGE_CHARS = int(os.environ.get("PIPELINE_MAX_PAGE_CHARS", "200000"))
BATCH_WAIT_MIN = float(os.environ.get("PIPELINE_BATCH_WAIT_MIN", "45"))
MAX_TOKENS = 16000

# USD per 1M tokens (input, output), Anthropic API list prices as of 2026-09; batch requests cost half.
PRICES = {
    "claude-opus-5": (5.0, 25.0),
    "claude-sonnet-5": (2.0, 10.0),
    "claude-haiku-4-5": (1.0, 5.0),
    "claude-opus-4-8": (5.0, 25.0),
    "claude-sonnet-4-6": (3.0, 15.0),
}
# Conservative estimate used before a call is made (guards are checked against the real usage afterwards).
EST_OUTPUT_TOKENS = 5000

BLOCKS = ("regime", "export", "export_support", "export_control", "import", "cost", "logistics", "documents", "sanctions", "supply")

SYSTEM = """You extract facts for an encyclopedia of international trade rules. You will receive the text of ONE
official government page (customs, ministry, tax or sanctions authority, statistics office).

Return ONLY a JSON object: {"facts": [ ... ]}. Each fact:
  {"block": one of %s,
   "country": ISO-3166 alpha-2 code the rule belongs to (or "" for international bodies),
   "hs_scope": list of HS prefixes the fact is limited to (empty list if it applies to all goods),
   "statement": {"ru": "...", "en": "..."},   // plain-language restatement, one or two sentences
   "quote": "...",                              // VERBATIM fragment copied from the page text, 1-3 sentences
   "quote_lang": "en" | "fr" | "zh" | "ru" | "fa" | ...,
   "has_number": true|false,                    // true if the statement contains a rate, threshold or amount
   "targets": ["IR"]}                           // sanctions facts only: ISO codes of the countries the measure targets

Hard rules:
1. Every fact needs a quote copied character-for-character from the page. Do not fix typos, do not translate the quote.
2. Never state a rate, threshold, date or amount that is not inside the quote.
3. Do not include advice on avoiding or circumventing sanctions, controls or checks. Describe restrictions as they are.
   Use block "export_control" for export licensing, dual-use and strategic goods lists (drones, encryption, machine tools).
4. Skip navigation, disclaimers, contact details and anything that is not a rule, procedure, rate, program or restriction.
5. If the page contains no usable facts, return {"facts": []}.
""" % ", ".join(f'"{b}"' for b in BLOCKS)


def _client():
    import anthropic  # imported lazily so the rest of the pipeline works without the SDK/key

    return anthropic.Anthropic()


def is_billing_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return "credit balance" in message or "billing" in message or "insufficient" in message and "credit" in message


# ---------------------------------------------------------------- money: prices, ledger, per-run accounting


def price_usd(model: str, input_tokens: int, output_tokens: int, batch: bool = False) -> float:
    """Estimated cost of one call from the API's token counts. Unknown models are priced as Opus (the dearest)."""
    inp, out = PRICES.get(model, PRICES["claude-opus-5"])
    usd = input_tokens / 1e6 * inp + output_tokens / 1e6 * out
    return usd / 2 if batch else usd


def estimate_usd(model: str, page_text: str, batch: bool = False) -> float:
    """Pre-call estimate: ~4 characters per token for the page plus the system prompt, EST_OUTPUT_TOKENS out."""
    return price_usd(model, len(page_text) // 4 + len(SYSTEM) // 4, EST_OUTPUT_TOKENS, batch)


def load_ledger(path: Path = USAGE_FILE) -> dict:
    try:
        doc = json.loads(path.read_text(encoding="utf8"))
    except (OSError, json.JSONDecodeError):
        doc = {}
    doc.setdefault("runs", [])
    doc.setdefault("pending_batch", None)
    return doc


def save_ledger(doc: dict, path: Path = USAGE_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf8")


def month_spend(doc: dict, month: str | None = None) -> float:
    month = month or date.today().strftime("%Y-%m")
    return round(sum(float(r.get("usd", 0)) for r in doc.get("runs", []) if str(r.get("date", "")).startswith(month)), 4)


@dataclass
class Spend:
    """Accounting for one run; `stop` is set the moment a guard trips."""

    model: str = field(default_factory=lambda: MODEL)
    batch: bool = False
    max_usd: float = field(default_factory=lambda: MAX_USD)
    monthly_usd: float = field(default_factory=lambda: MONTHLY_USD)
    month_before: float = 0.0
    pages: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    usd: float = 0.0
    facts: int = 0
    dropped: int = 0
    skipped_large: list[str] = field(default_factory=list)
    stop: str | None = None

    def add(self, usage, facts: int = 0, dropped: int = 0) -> None:
        inp = int(getattr(usage, "input_tokens", 0) or 0) + int(getattr(usage, "cache_read_input_tokens", 0) or 0) + int(getattr(usage, "cache_creation_input_tokens", 0) or 0)
        out = int(getattr(usage, "output_tokens", 0) or 0)
        self.pages += 1
        self.input_tokens += inp
        self.output_tokens += out
        self.usd = round(self.usd + price_usd(self.model, inp, out, self.batch), 4)
        self.facts += facts
        self.dropped += dropped

    def would_exceed(self, extra_usd: float) -> str | None:
        """Guard checked before every call with a conservative estimate; returns the reason or None."""
        if self.usd + extra_usd > self.max_usd:
            return f"run cap PIPELINE_MAX_USD={self.max_usd:.2f} $ would be exceeded (spent {self.usd:.2f} $ + ~{extra_usd:.2f} $)"
        if self.month_before + self.usd + extra_usd > self.monthly_usd:
            return f"monthly cap PIPELINE_MONTHLY_USD={self.monthly_usd:.2f} $ would be exceeded (month {self.month_before + self.usd:.2f} $ + ~{extra_usd:.2f} $)"
        return None

    def record(self, doc: dict, note: str = "") -> None:
        doc["runs"].append({
            "date": date.today().isoformat(), "model": self.model, "batch": self.batch, "pages": self.pages,
            "input_tokens": self.input_tokens, "output_tokens": self.output_tokens, "usd": self.usd,
            "facts": self.facts, "dropped": self.dropped, "note": note,
        })


def write_report(spend: Spend, ledger: dict, note: str = "", path: Path = REPORT_FILE) -> None:
    month = month_spend(ledger)
    lines = [
        f"# Извлечение фактов — {date.today().isoformat()}",
        "",
        f"- модель: {spend.model}{' (пакетный режим, половина цены)' if spend.batch else ''}",
        f"- страниц отправлено модели: {spend.pages}; фактов принято: {spend.facts}; отброшено без цитаты: {spend.dropped}",
        f"- токенов: {spend.input_tokens} на входе, {spend.output_tokens} на выходе",
        f"- потрачено за запуск: {spend.usd:.2f} $ (лимит {spend.max_usd:.2f} $)",
        f"- потрачено за месяц: {month:.2f} $ (лимит {spend.monthly_usd:.2f} $)",
    ]
    if spend.skipped_large:
        lines.append(f"- пропущено как слишком большие (> {MAX_PAGE_CHARS} символов, не обрезаются): " + ", ".join(spend.skipped_large))
    if ledger.get("pending_batch"):
        pb = ledger["pending_batch"]
        lines.append(f"- пакет {pb['id']} ещё обрабатывается ({len(pb['pages'])} страниц), результаты заберёт следующий запуск")
    if note:
        lines.append(f"- {note}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf8")


# ---------------------------------------------------------------- model calls


def _parse_json(text: str) -> dict:
    text = text.strip()
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        return {"facts": []}
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return {"facts": []}


def _prompt(page_text: str, url: str, topic: str | None) -> str:
    hint = f"Topic of interest: {topic}.\n" if topic else ""
    return f"{hint}Source URL: {url}\n\n<page>\n{page_text}\n</page>"


def _facts_from_message(message) -> list[dict]:
    if getattr(message, "stop_reason", "") == "refusal":
        return []
    text = "".join(block.text for block in message.content if block.type == "text")
    facts = _parse_json(text).get("facts", [])
    return [f for f in facts if isinstance(f, dict)]


def propose_facts(page_text: str, url: str, topic: str | None = None, client=None, spend: Spend | None = None) -> list[dict]:
    """Asks the model for candidate facts (one synchronous call). Verification happens in `accept_facts`."""
    client = client or _client()
    with client.messages.stream(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM,
        messages=[{"role": "user", "content": _prompt(page_text, url, topic)}],
    ) as stream:
        message = stream.get_final_message()
    if spend is not None:
        spend.add(message.usage)
    return _facts_from_message(message)


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
                "targets": [str(t)[:2].upper() for t in (fact.get("targets") or []) if str(t).strip()],
            }
        )
    return kept, dropped


def facts_path(source_id: str, url: str, out_dir: Path = FACTS_DIR) -> Path:
    return out_dir / f"{source_id}__{hashlib.sha1(url.encode('utf8')).hexdigest()[:8]}.json"


def unchanged_since_last_extract(path: Path, content_hash: str) -> bool:
    """True when a facts file for this URL exists and was built from a page with the same content hash."""
    if not path.exists():
        return False
    try:
        return json.loads(path.read_text(encoding="utf8")).get("content_hash") == content_hash
    except (OSError, json.JSONDecodeError):
        return False


def write_facts(out: Path, url: str, source_id: str, fetched_at: str, content_hash: str, topic: str | None, facts: list[dict], dropped: int) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            {"url": url, "source_id": source_id, "fetched_at": fetched_at, "content_hash": content_hash, "topic": topic, "facts": facts, "dropped": dropped},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf8",
    )
    return out


def extract_url(url: str, topic: str | None = None, client=None, out_dir: Path = FACTS_DIR, force: bool = False, spend: Spend | None = None) -> Path | None:
    """Fetches the page and extracts facts. Returns None when the page has not changed since the last extraction
    (no model call, no cost) — the daily job therefore pays only for pages that actually changed."""
    source = registry.find_source(url)
    if source is None:
        raise fetch.NotWhitelisted(url)
    snapshot = fetch.fetch_url(url)
    out = facts_path(source.id, url, out_dir)
    if not force and unchanged_since_last_extract(out, snapshot.content_hash):
        return None
    if len(snapshot.text) > MAX_PAGE_CHARS:
        if spend is not None:
            spend.skipped_large.append(url)
        print(f"skip {source.id}: {url} is {len(snapshot.text)} chars > PIPELINE_MAX_PAGE_CHARS={MAX_PAGE_CHARS}; point the registry at a narrower page")
        return None
    if spend is not None:
        reason = spend.would_exceed(estimate_usd(spend.model, snapshot.text, spend.batch))
        if reason:
            spend.stop = reason
            return None
    candidates = propose_facts(snapshot.text, url, topic, client, spend)
    facts, dropped = accept_facts(candidates, snapshot.text)
    if spend is not None:
        spend.facts += len(facts)
        spend.dropped += dropped
    return write_facts(out, url, source.id, snapshot.fetched_at, snapshot.content_hash, topic, facts, dropped)


def _registry_urls(country: str | None) -> list[tuple[registry.Source, str]]:
    out = []
    for source in registry.load_sources():
        if country and source.country != country.upper():
            continue
        for url in source.urls:
            if url:
                out.append((source, url))
    return out


def extract_registry(country: str | None = None, out_dir: Path = FACTS_DIR, max_pages: int = MAX_PAGES, force: bool = False, batch: bool = False, ledger_path: Path = USAGE_FILE, report_path: Path = REPORT_FILE, client=None) -> list[Path]:
    """Extracts from every URL listed under `urls` in data/sources.yaml (optionally one country), within the
    spending guards documented at the top of this module. Records the run in the ledger and writes the report."""
    ledger = load_ledger(ledger_path)
    spend = Spend(batch=batch, month_before=month_spend(ledger))
    if spend.month_before >= spend.monthly_usd:
        note = f"stop: monthly cap PIPELINE_MONTHLY_USD={spend.monthly_usd:.2f} $ already reached ({spend.month_before:.2f} $) — no model calls"
        print(note)
        write_report(spend, ledger, note, report_path)
        return []
    client = client or _client()
    written: list[Path] = []
    note = ""
    try:
        if batch:
            written, note = _extract_batch(country, out_dir, max_pages, force, client, spend, ledger)
        else:
            written, note = _extract_sync(country, out_dir, max_pages, force, client, spend)
    finally:
        if spend.pages or spend.stop:
            spend.record(ledger, note or spend.stop or "")
        save_ledger(ledger, ledger_path)
        write_report(spend, ledger, note or spend.stop or "", report_path)
    return written


def _extract_sync(country, out_dir, max_pages, force, client, spend: Spend) -> tuple[list[Path], str]:
    written: list[Path] = []
    for source, url in _registry_urls(country):
        if spend.pages >= max_pages:
            note = f"stop: reached PIPELINE_MAX_PAGES={max_pages}; remaining URLs wait for the next run"
            print(note)
            return written, note
        try:
            result = extract_url(url, topic=",".join(source.topics), client=client, out_dir=out_dir, force=force, spend=spend)
        except Exception as exc:  # keep going: an unreachable source is a status, not a stop
            print(f"skip {source.id}: {url} ({exc.__class__.__name__}: {str(exc)[:160]})")
            if is_billing_error(exc):
                note = "stop: the API account has no credits — nothing else will succeed this run"
                print(note)
                return written, note
            continue
        if spend.stop:
            print(f"stop: {spend.stop}")
            return written, f"stop: {spend.stop}"
        if result is None:
            print(f"same {source.id}: {url} (unchanged or skipped, no model call)")
            continue
        written.append(result)
        print(f"ok   {source.id}: {url}")
    return written, ""


# ---------------------------------------------------------------- batch mode


def _batch_request(custom_id: str, page_text: str, url: str, topic: str | None) -> dict:
    return {
        "custom_id": custom_id,
        "params": {"model": MODEL, "max_tokens": MAX_TOKENS, "system": SYSTEM, "messages": [{"role": "user", "content": _prompt(page_text, url, topic)}]},
    }


def _wait_for_batch(client, batch_id: str, wait_min: float) -> bool:
    """Polls until the batch has ended or the wait budget is spent. Returns True when ended."""
    deadline = time.monotonic() + wait_min * 60
    while True:
        batch = client.messages.batches.retrieve(batch_id)
        if batch.processing_status == "ended":
            return True
        if time.monotonic() >= deadline:
            return False
        counts = getattr(batch, "request_counts", None)
        print(f"batch {batch_id}: {batch.processing_status}, processing {getattr(counts, 'processing', '?')}")
        time.sleep(30)


def _collect_batch(client, pending: dict, texts: dict[str, str], out_dir: Path, spend: Spend) -> list[Path]:
    """Turns an ended batch into facts files. Pages whose text is not in memory are re-fetched (free)."""
    pages = {p["custom_id"]: p for p in pending["pages"]}
    written: list[Path] = []
    for result in client.messages.batches.results(pending["id"]):
        page = pages.get(result.custom_id)
        if page is None:
            continue
        kind = result.result.type
        if kind != "succeeded":
            print(f"batch item {result.custom_id}: {kind} — will be retried next run")
            continue
        text = texts.get(result.custom_id)
        if text is None:
            try:
                snap = fetch.fetch_url(page["url"])
                text = snap.text
                if snap.content_hash != page["content_hash"]:
                    print(f"batch item {result.custom_id}: page changed since submission; quotes checked against the new text")
            except Exception as exc:
                print(f"batch item {result.custom_id}: cannot re-fetch page for quote check ({exc.__class__.__name__}); skipped")
                continue
        message = result.result.message
        facts, dropped = accept_facts(_facts_from_message(message), text)
        spend.add(message.usage, len(facts), dropped)
        out = write_facts(out_dir / page["file"], page["url"], page["source_id"], page["fetched_at"], page["content_hash"], page.get("topic"), facts, dropped)
        written.append(out)
        print(f"ok   {page['source_id']}: {page['url']} ({len(facts)} facts, {dropped} dropped)")
    return written


def _extract_batch(country, out_dir, max_pages, force, client, spend: Spend, ledger: dict) -> tuple[list[Path], str]:
    written: list[Path] = []
    texts: dict[str, str] = {}
    # 1. A batch left over from the previous run comes first — its cost is already committed.
    pending = ledger.get("pending_batch")
    if pending:
        if _wait_for_batch(client, pending["id"], BATCH_WAIT_MIN):
            written += _collect_batch(client, pending, texts, out_dir, spend)
            ledger["pending_batch"] = None
        else:
            note = f"batch {pending['id']} still processing; nothing new submitted"
            print(note)
            return written, note
    # 2. Fetch candidate pages (no cost), apply the guards with a pre-call estimate.
    pages: list[dict] = []
    estimate = 0.0
    note = ""
    for source, url in _registry_urls(country):
        if len(pages) >= max_pages:
            note = f"stop: reached PIPELINE_MAX_PAGES={max_pages}; remaining URLs wait for the next run"
            break
        try:
            snap = fetch.fetch_url(url)
        except Exception as exc:
            print(f"skip {source.id}: {url} ({exc.__class__.__name__}: {str(exc)[:160]})")
            continue
        out = facts_path(source.id, url, out_dir)
        if not force and unchanged_since_last_extract(out, snap.content_hash):
            print(f"same {source.id}: {url} (unchanged, no model call)")
            continue
        if len(snap.text) > MAX_PAGE_CHARS:
            spend.skipped_large.append(url)
            print(f"skip {source.id}: {url} is {len(snap.text)} chars > PIPELINE_MAX_PAGE_CHARS={MAX_PAGE_CHARS}")
            continue
        page_cost = estimate_usd(spend.model, snap.text, batch=True)
        reason = spend.would_exceed(estimate + page_cost)
        if reason:
            note = f"stop: {reason}; remaining URLs wait for the next run"
            break
        estimate += page_cost
        custom_id = out.stem
        texts[custom_id] = snap.text
        pages.append({"custom_id": custom_id, "file": out.name, "url": url, "source_id": source.id, "topic": ",".join(source.topics), "fetched_at": snap.fetched_at, "content_hash": snap.content_hash})
    if not pages:
        return written, note or "nothing to extract: every registry page is unchanged"
    # 3. Submit, wait, collect.
    try:
        batch = client.messages.batches.create(requests=[_batch_request(p["custom_id"], texts[p["custom_id"]], p["url"], p["topic"]) for p in pages])
    except Exception as exc:
        if is_billing_error(exc):
            return written, "stop: the API account has no credits — batch not submitted"
        raise
    ledger["pending_batch"] = {"id": batch.id, "model": spend.model, "submitted": datetime.now(timezone.utc).isoformat(timespec="seconds"), "pages": pages, "estimate_usd": round(estimate, 4)}
    print(f"batch {batch.id}: {len(pages)} pages submitted, estimated {estimate:.2f} $ (half price)")
    if _wait_for_batch(client, batch.id, BATCH_WAIT_MIN):
        written += _collect_batch(client, ledger["pending_batch"], texts, out_dir, spend)
        ledger["pending_batch"] = None
    else:
        note = (note + "; " if note else "") + f"batch {batch.id} still processing after {BATCH_WAIT_MIN:g} min; results are collected next run"
        print(note)
    return written, note
