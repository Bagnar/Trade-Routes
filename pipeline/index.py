"""index — the index layer: a cheap, rule-based score and the "where else to ship" table for any pair of countries
and any HS-6 group, computed only from structured data (docs/concept.md, sections 5 and 6):

  - duties        from data/rates/{ISO2}.json      (rates.py, WITS/TRAINS)          rule-based
  - obstacles     from sanctions program pages that the pipeline fetched (data/facts) and ban facts   rule-based
  - support       from export_support facts of the exporter (data/facts)             rule-based
  - demand        not connected yet (trade statistics)                               always "ориентир"
  - logistics     not connected yet (logistics indices)                              always "ориентир"

Rules this module must never break: a part without data gets score None and a basis that says so — a score without
a basis is never shown; a prohibition on the pair zeroes the total; third-country sanctions on the pair are an
obstacle, not a prohibition; nothing here comes from a model or from memory. "No sanctions" is never claimed —
only "program pages checked: none list this country" when the registry has pages for other targets.

Run:  python -m pipeline index --from CN --to CA --hs6 610910      (prints the computed rating and compare rows)
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml

from . import agreements, assemble, demand, rates

ROOT = Path(__file__).resolve().parent.parent
SOURCES_FILE = ROOT / "data" / "sources.yaml"
COUNTRIES_FILE = ROOT / "data" / "countries.json"

PART_NAMES = ("Пошлины и налоги", "Препятствия", "Господдержка", "Спрос", "Логистика")


def _countries() -> dict[str, dict]:
    try:
        return {c["code"]: c for c in json.loads(COUNTRIES_FILE.read_text(encoding="utf8"))}
    except (OSError, json.JSONDecodeError):
        return {}


def sanction_programs(sources_file: Path = SOURCES_FILE) -> list[dict]:
    """Official sanctions program pages from the registry: [{"authority", "domain", "url", "targets": [ISO2]}]."""
    doc = yaml.safe_load(sources_file.read_text(encoding="utf8"))
    out: list[dict] = []
    for entry in doc.get("sanctions_authorities") or []:
        for u in entry.get("urls") or []:
            if isinstance(u, dict) and u.get("targets"):
                out.append({"authority": entry.get("jurisdiction", ""), "domain": entry["domain"], "url": u["url"], "targets": [str(t).upper() for t in u["targets"]]})
    return out


def fetched_urls(facts: list[dict]) -> dict[str, str]:
    """URL -> date of the last successful fetch (from data/facts): evidence that the page exists and was read."""
    return {f["url"]: f["fetched_at"][:10] for f in facts}


def duty_part(country_to: str, hs6: str) -> tuple[int | None, str, str]:
    rate = rates.get_rate(country_to, hs6)
    if rate is None:
        return None, "ставка MFN для этой страны не загружена в таблицу ставок", "ставка не загружена"
    v = float(rate["value"])
    score = 5 if v == 0 else 4 if v <= 5 else 3 if v <= 10 else 2 if v <= 20 else 1 if v <= 35 else 0
    return score, f"пошлина MFN {v:g}% (WITS/TRAINS, {rate['year']} год); преференции и национальная подстрока — у брокера", f"{v:g}%"


def obstacles_part(fr: str, to: str, hs6: str, facts: list[dict], programs: list[dict]) -> tuple[int | None, str, str, bool]:
    """Returns (score, basis, short text for the compare table, banned)."""
    fetched = fetched_urls(facts)
    seen = [p for p in programs if p["url"] in fetched]
    hitting = sorted({p["authority"] for p in seen if set(p["targets"]) & {fr, to}})
    # A prohibition zeroes the score only when the source names this product group (non-empty hs_scope that
    # matches). Country-wide sanctions wording without a product scope is an obstacle, not a product ban
    # (docs/concept.md, section 5: "санкции на страны при разрешённом товаре — препятствие, не запрет").
    ban_facts = [f for f in facts if f.get("block") == "sanctions" and assemble.to_page_fact(f)["ban"] and (assemble.sanction_targets(f) & {fr, to})]
    banned = any(f.get("hs_scope") and assemble.scope_matches(f["hs_scope"], hs6) for f in ban_facts)
    if banned:
        return 0, "источник называет запрет для этой пары «страна — товар» (см. блок «Режим»): оценка обнулена", "запрет", True
    if hitting or ban_facts:
        who = ", ".join(hitting) if hitting else "третьих стран"
        return 2, f"санкционные режимы {who} действуют в отношении одной из стран пары — препятствие (расчёты, логистика, отдельные товарные запреты); запрет именно этой группы источники не называют", "есть: " + (", ".join(hitting) if hitting else "см. режим"), False
    if seen:
        return 4, f"проверенные страницы санкционных программ ({len(seen)}) не называют страны пары; полный список режимов не проверен", "в проверенных программах нет", False
    return None, "санкционные режимы для пары не проверены", "не проверено", False


def support_part(fr: str, hs6: str, facts: list[dict]) -> tuple[int | None, str, str]:
    n = sum(1 for f in facts if f.get("block") == "export_support" and f.get("country") == fr and assemble.scope_matches(f.get("hs_scope", []), hs6))
    if n == 0:
        return None, "программы поддержки экспортёра не собраны из источников", "не собрано"
    return (3 if n <= 2 else 4), f"{n} строк о программах поддержки из официальных источников", f"{n} стр."


def demand_part(to: str, hs6: str) -> tuple[int | None, str]:
    """Always an "ориентир": scored only from data/demand, never "проверено"; no score when stale or absent."""
    d = demand.get_demand(to, hs6)
    if d is None:
        return None, "торговая статистика для этой пары ещё не загружена (UN Comtrade) — ориентир появится после загрузки"
    if d["stale"]:
        return None, f"последние данные о ввозе за {d['latest_year']} год — старше {demand.STALE_YEARS} лет, балл не ставится (UN Comtrade, ориентир)"
    score = 3
    if d["value"] >= 100e6:
        score += 1
    if d["growth_pct"] is not None:
        if d["growth_pct"] >= 10:
            score += 1
        elif d["growth_pct"] <= -10:
            score -= 1
    score = max(1, min(5, score))
    growth = f", {'+' if d['growth_pct'] >= 0 else ''}{d['growth_pct']}% за {d['span_years']} года" if d["growth_pct"] is not None else ""
    kind = f" (зеркальные данные {d['partners']} партнёров, неполные)" if d["kind"] == "mirror" else ""
    return score, f"ввоз {demand.usd_text(d['value'])} в {d['latest_year']} году{growth}{kind} — UN Comtrade, ориентир"


def agreement_text(fr: str, to: str, doc: dict | None) -> str:
    if doc is None:  # database not loaded: never "no agreement", only "not checked"
        return "не проверено"
    found = agreements.between(fr, to, doc)
    if not found and found is not None and not doc.get("agreements"):
        return "не проверено"
    if not found:
        return "нет в базе РТС ВТО"
    return "; ".join(a["name"] for a in found[:2]) + (" (+)" if len(found) > 2 else "")


_UNSET: dict = {}  # sentinel: "load from disk"; an explicit None means "agreements database not loaded"


def compute(fr: str, to: str, hs6: str, facts: list[dict] | None = None, programs: list[dict] | None = None, agreements_doc: dict | None = _UNSET) -> dict:
    facts = assemble.load_facts() if facts is None else facts
    programs = sanction_programs() if programs is None else programs
    agreements_doc = agreements.load() if agreements_doc is _UNSET else agreements_doc
    d_score, d_basis, d_short = duty_part(to, hs6)
    o_score, o_basis, o_short, banned = obstacles_part(fr, to, hs6, facts, programs)
    s_score, s_basis, s_short = support_part(fr, hs6, facts)
    dm_score, dm_basis = demand_part(to, hs6)
    parts = [
        {"name": PART_NAMES[0], "score": d_score, "basis": d_basis},
        {"name": PART_NAMES[1], "score": o_score, "basis": o_basis},
        {"name": PART_NAMES[2], "score": s_score, "basis": s_basis},
        {"name": PART_NAMES[3], "score": dm_score, "basis": dm_basis},
        {"name": PART_NAMES[4], "score": None, "basis": "индексы логистики не подключены — ориентир появится позже, статус «проверено» не получает никогда"},
    ]
    scored = [p for p in parts if p["score"] is not None]
    total = 0 if banned else sum(p["score"] for p in scored)
    of = 5 * len(scored)
    if banned:
        verdict, status = "запрет: оценка обнулена", "warn"
    elif not scored:
        verdict, status = "не рассчитано: нет данных индексного слоя", "warn"
    else:
        ratio = total / of
        verdict, status = ("выгодно по проверенным частям", "ok") if ratio >= 0.7 else ("средне по проверенным частям", "mid") if ratio >= 0.45 else ("дорого или сложно по проверенным частям", "warn")
    return {
        "total": total, "of": of, "verdict": verdict, "verdictStatus": status, "parts": parts,
        "agreement": agreement_text(fr, to, agreements_doc),
        "duty": d_short, "sanctions": o_short, "support": s_short,
        "banned": banned,
    }


def compare_rows(fr: str, to: str, hs6: str, facts: list[dict] | None = None, destinations: list[str] | None = None) -> list[dict]:
    """Rows of "where else to ship": this destination plus every importer with a loaded rates table."""
    facts = assemble.load_facts() if facts is None else facts
    programs = sanction_programs()
    agreements_doc = agreements.load()
    names = _countries()
    if destinations is None:
        destinations = sorted({p.stem.upper() for p in rates.RATES_DIR.glob("*.json")} | {to})
    rows: list[dict] = []
    for dest in destinations:
        if dest == fr:
            continue
        c = compute(fr, dest, hs6, facts, programs, agreements_doc)
        here = dest == to
        name = names.get(dest, {}).get("name", dest)
        rows.append({
            "to": f"{name} — эта страница" if here else name,
            **({"here": True} if here else {}),
            "duty": c["duty"], "agreement": c["agreement"], "sanctions": c["sanctions"], "support": c["support"],
            "score": {"text": "запрет" if c["banned"] else "не рассчитано" if c["of"] == 0 else f"{c['total']} из {c['of']}", "status": c["verdictStatus"]},
            "_ratio": -1 if c["of"] == 0 else c["total"] / c["of"],
        })
    rows.sort(key=lambda r: (-r["_ratio"], r["to"]))
    for r in rows:
        r.pop("_ratio")
    return rows


def main(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="pipeline index")
    parser.add_argument("--from", dest="fr", required=True)
    parser.add_argument("--to", required=True)
    parser.add_argument("--hs6", required=True)
    args, _ = parser.parse_known_args(argv)
    result = compute(args.fr.upper(), args.to.upper(), args.hs6)
    result["compare"] = compare_rows(args.fr.upper(), args.to.upper(), args.hs6)
    print(json.dumps(result, ensure_ascii=False, indent=1))
    return 0
