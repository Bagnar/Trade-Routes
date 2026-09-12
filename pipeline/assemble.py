"""assemble — puts extracted facts (data/facts) and structured rates (data/rates) onto the pages the site renders.

Rules this module must never break:
  - a fact reaches a page only with its verbatim quote, source URL and snapshot date (no quote, no claim);
  - rates on a page come only from data/rates (the rates layer), never from a model or from memory;
  - it never rewrites a page's hand-written or generated lines — it prepends sourced lines to the right block and
    leaves the honest "not collected" placeholders when nothing sourced exists for that block.

Matching: a fact applies to a corridor page when its country is the exporting or importing country and its
`hs_scope` is empty, matches the page's HS-6 by prefix, or is a Canadian chapter 98/99 special provision (which
applies to all goods). Block mapping: regime/sanctions -> regime; export/export_support -> export; import/cost/
documents/logistics -> import/cost/documents/logistics.

Run: python -m pipeline assemble            (all pages; daily-check.yml runs it after extract)
"""
from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Iterable

from . import monitor, rates

ROOT = Path(__file__).resolve().parent.parent
FACTS_DIR = ROOT / "data" / "facts"
PAGES_DIR = ROOT / "web" / "data" / "pages"

ASSEMBLED = "assembled by pipeline/assemble.py"


def load_facts(facts_dir: Path = FACTS_DIR) -> list[dict]:
    """Flattens data/facts/*.json into fact records that carry their source file's url/date."""
    out: list[dict] = []
    if not facts_dir.exists():
        return out
    for path in sorted(facts_dir.glob("*.json")):
        try:
            doc = json.loads(path.read_text(encoding="utf8"))
        except json.JSONDecodeError:
            continue
        for fact in doc.get("facts", []):
            out.append({**fact, "url": doc["url"], "source_id": doc["source_id"], "fetched_at": doc["fetched_at"]})
    return out


def scope_matches(hs_scope: list[str], hs6: str) -> bool:
    if not hs_scope:
        return True
    for prefix in hs_scope:
        digits = "".join(ch for ch in str(prefix) if ch.isdigit())
        if not digits:
            continue
        if digits.startswith(("98", "99")):  # Canadian chapters 98/99: special provisions that apply to all goods
            return True
        if hs6.startswith(digits[:6]):
            return True
    return False


def domain_of(url: str) -> str:
    return url.split("//", 1)[-1].split("/", 1)[0].removeprefix("www.")


def ru_date(iso: str) -> str:
    try:
        return monitor.ru_date(datetime.fromisoformat(iso.replace("Z", "+00:00")).date())
    except ValueError:
        return iso


def to_page_fact(fact: dict) -> dict:
    """PageContent Fact with a stamp that carries quote, URL and date (checked daily by monitor.py)."""
    ban = fact["block"] == "sanctions" and any(w in fact["statement"]["ru"].lower() for w in ("запрещ", "запрет"))
    return {
        "text": fact["statement"]["ru"],
        "quote": fact["quote"],
        "quoteLang": fact.get("quote_lang", ""),
        "ban": ban,
        "stamp": {
            "status": "ban" if ban else "ok",
            "source": domain_of(fact["url"]),
            "label": ("запрет, " if ban else "") + f"проверено {ru_date(fact['fetched_at'])}",
            "verifiedAt": fact["fetched_at"][:10],
            "url": fact["url"],
        },
        "_assembled": ASSEMBLED,
    }


BLOCK_TO_SECTION = {
    "regime": "regime",
    "sanctions": "regime",
    "export": "export",
    "export_support": "export",
    "import": "import",
    "cost": "import",
    "documents": "import",
    "logistics": "logistics",
}


def strip_assembled(items: list[dict]) -> list[dict]:
    return [f for f in items if f.get("_assembled") != ASSEMBLED]


def rate_fact(country_to: str, hs6: str) -> dict | None:
    rate = rates.get_rate(country_to, hs6)
    if rate is None:
        return None
    value = rate["value"]
    text = f"Пошлина при ввозе по режиму наибольшего благоприятствования: {value:g}% (простая средняя по группе HS-6, база WITS/TRAINS, данные за {rate['year']} год). Национальная подстрока и льготные ставки уточняются у брокера."
    return {
        "key": "Пошлина при ввозе",
        "text": text,
        "rate_ref": f"{country_to}:{hs6}:import_mfn",
        "quote": f"{hs6} {value:g}",
        "stamp": {
            "status": "ok",
            "source": "wits.worldbank.org",
            "label": f"таблица ставок, снимок {ru_date(rate['fetched_at'])}",
            "verifiedAt": str(rate["fetched_at"])[:10],
            "url": rate["url"],
        },
        "_assembled": ASSEMBLED,
    }


SANCTION_TARGET_WORDS = {"iran": "IR", "russia": "RU", "belarus": "BY", "syria": "SY", "north-korea": "KP", "dprk": "KP", "cuba": "CU", "venezuela": "VE", "myanmar": "MM", "burma": "MM"}


def sanction_targets(fact: dict) -> set[str]:
    """Countries a sanctions fact is about: the extractor's `targets` when present, else keywords in the program URL."""
    targets = {str(t).upper() for t in fact.get("targets", []) or []}
    if targets:
        return targets
    url = fact.get("url", "").lower()
    return {code for word, code in SANCTION_TARGET_WORDS.items() if word in url}


def assemble_page(page: dict, facts: Iterable[dict]) -> dict:
    """Returns the page with sourced lines merged in. Idempotent: previously assembled lines are replaced."""
    fr, to = page["corridor"]["from"]["code"], page["corridor"]["to"]["code"]
    hs6 = page["product"]["hs6"]
    by_section: dict[str, list[dict]] = {"regime": [], "export": [], "import": [], "logistics": []}
    for fact in facts:
        country = fact.get("country", "")
        if not scope_matches(fact.get("hs_scope", []), hs6):
            continue
        if fact["block"] == "sanctions":
            # third-country sanctions (CA/US/EU/UK) attach to pages whose exporter or importer is a target
            if not (sanction_targets(fact) & {fr, to}):
                continue
        elif country not in (fr, to, ""):
            continue
        # export-side facts belong to the exporting country, import-side to the importing one
        section = BLOCK_TO_SECTION.get(fact["block"])
        if section is None:
            continue
        if section == "export" and country not in (fr, ""):
            continue
        if section == "import" and country not in (to, ""):
            continue
        by_section[section].append(to_page_fact(fact))

    for section in ("regime", "export", "import", "logistics"):
        block = page[section]
        block["facts"] = by_section[section] + strip_assembled(block["facts"])

    # Summary: sourced import duty from the rates layer replaces the "not loaded" placeholder.
    summary = strip_assembled(page["summary"]["facts"])
    duty = rate_fact(to, hs6)
    if duty:
        summary = [duty] + [f for f in summary if f.get("key") != "Пошлина при ввозе"]
    page["summary"]["facts"] = summary

    # Sources table: one row per distinct source URL used above.
    urls: dict[str, dict] = {}
    for section in ("regime", "export", "import", "logistics"):
        for f in page[section]["facts"]:
            if f.get("_assembled") == ASSEMBLED and f["stamp"].get("url"):
                urls.setdefault(f["stamp"]["url"], {"source": f["stamp"]["source"], "checked": f["stamp"]["label"].split("проверено ")[-1]})
    if duty:
        urls.setdefault(duty["stamp"]["url"], {"source": "wits.worldbank.org", "checked": duty["stamp"]["label"].split("снимок ")[-1]})
    rows = [
        {"source": v["source"], "confirms": "цитата проверена", "checked": v["checked"], "status": {"text": "актуально", "kind": "ok"}, "_assembled": ASSEMBLED}
        for v in urls.values()
    ]
    page["sources"]["rows"] = rows + [r for r in page["sources"]["rows"] if r.get("_assembled") != ASSEMBLED]

    sourced = sum(len(by_section[s]) for s in by_section) + (1 if duty else 0)
    page["status"]["sourcesTotal"] = len(urls)
    page["status"]["lastChecked"] = date.today().isoformat()
    if sourced:
        page["status"]["text"] = (
            f"На странице {sourced} строк из официальных источников с дословной цитатой ({len(urls)} источников), "
            f"проверено {monitor.ru_date(date.today())}. Остальные строки помечены как демо или «не собрано». "
            "Это не юридическая консультация: код товара и ставки подтвердите у таможенного брокера."
        )
    page["_assembled"] = ASSEMBLED
    return page


def run(pages_dir: Path = PAGES_DIR, facts_dir: Path = FACTS_DIR) -> int:
    facts = load_facts(facts_dir)
    changed = 0
    for path in sorted(pages_dir.glob("*.json")):
        page = json.loads(path.read_text(encoding="utf8"))
        before = json.dumps(page, ensure_ascii=False, sort_keys=True)
        page = assemble_page(page, facts)
        after = json.dumps(page, ensure_ascii=False, sort_keys=True)
        if before != after:
            path.write_text(json.dumps(page, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
            changed += 1
    print(f"assemble: {len(facts)} facts, {changed} page(s) updated")
    return changed


def main(argv=None) -> int:
    run()
    return 0
