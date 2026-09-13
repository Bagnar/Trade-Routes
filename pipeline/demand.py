"""demand — trade statistics for the "спрос" part of the rating (docs/concept.md: always an "ориентир").

Stage 1: World Bank WITS trade statistics (UN Comtrade data served by WITS, no key). Before any number is
used, `--probe` checks freshness: which years WITS has for a reporter, compared with what UN Comtrade itself
reports as available (public data-availability endpoint, no key). The comparison decides whether WITS is
fresh enough or the project needs a UN Comtrade API key.

Loader (stage 2): the same public endpoint, paced (one call per ~3 s, retry after a 429), at most
DEMAND_MAX_CALLS per run, results cached for 30 days in data/demand/{ISO2}.json. Reported imports first; for
countries that do not report at HS-6 (Iran) a partial mirror — exports to that country reported by a fixed list of
major partners — marked kind "mirror". Numbers on the site come only from these files, always with the data year,
and only as "ориентир" (docs/concept.md, principle 8); a latest year older than STALE_YEARS gets no score.

Run:  python -m pipeline demand --probe CA,CN,RU,IR,TR     (network: GitHub Actions, reference-data.yml)
      python -m pipeline demand --load                     (pairs from web/data/pages and data/rates; --importers CA --hs6 610910)
"""
from __future__ import annotations

import json
import os
import re
import time
from datetime import date, datetime, timezone
from pathlib import Path

from . import fetch, rates

# WITS "tradestats-trade" datasource (trade indicators). URL shapes are probed: WITS uses ISO3 for this datasource.
WITS_AVAILABILITY_SHAPES = (
    "https://wits.worldbank.org/API/V1/wits/datasource/tradestats-trade/dataavailability/country/{iso3}/year/{year}?format=JSON",
    "https://wits.worldbank.org/API/V1/wits/datasource/tradestats-trade/dataavailability/country/{iso3}/year/all?format=JSON",
    "https://wits.worldbank.org/API/V1/wits/datasource/tradestats-trade/dataavailability/country/{m49}/year/{year}?format=JSON",
)
WITS_SAMPLE_SHAPES = (
    "https://wits.worldbank.org/API/V1/SDMX/V21/datasource/tradestats-trade/reporter/{iso3}/year/{year}/partner/wld/product/610910/indicator/MPRT-TRD-VL",
    "https://wits.worldbank.org/API/V1/SDMX/V21/datasource/tradestats-trade/reporter/{iso3}/year/{year}/partner/wld/product/all/indicator/MPRT-TRD-VL?format=JSON",
)
# UN Comtrade public endpoints (no subscription key): data availability and a preview of the data itself.
COMTRADE_AVAILABILITY = "https://comtradeapi.un.org/public/v1/getDA/C/A/HS?reporterCode={m49}"
COMTRADE_PREVIEW = "https://comtradeapi.un.org/public/v1/preview/C/A/HS?reporterCode={m49}&period={year}&partnerCode=0&cmdCode=610910&flowCode=M"
# Mirror data for poor reporters: what every partner reports as exports (X) to the country as partner.
COMTRADE_MIRROR = "https://comtradeapi.un.org/public/v1/preview/C/A/HS?reporterCode=all&period={year}&partnerCode={m49}&cmdCode=610910&flowCode=X"


def total_value(body: str, mirror: bool = False) -> float | None:
    """The world total in a Comtrade reply: the record with no secondary partner, customs or transport breakdown.
    Mirror replies (many reporters) are summed over reporters."""
    try:
        data = json.loads(body).get("data") or []
    except json.JSONDecodeError:
        return None
    totals = [r for r in data if str(r.get("partner2Code", 0)) in ("0", "") and str(r.get("customsCode", "C00")) in ("C00", "") and str(r.get("motCode", 0)) in ("0", "")]
    if not totals:
        return None
    if mirror:
        return float(sum(float(r.get("primaryValue") or 0) for r in totals))
    return float(totals[0].get("primaryValue") or 0)


def _years(text: str) -> list[int]:
    """Years mentioned in an availability reply, whatever its exact shape (JSON or XML)."""
    found = {int(y) for y in re.findall(r"\b(19[89]\d|20[0-4]\d)\b", text)}
    return sorted(found)


def _try(label: str, url: str, timeout: float = 120.0) -> tuple[int | None, str]:
    try:
        snap = fetch.fetch_url(url, save=False, timeout=timeout)
        body = (snap.html or snap.text).replace("\n", " ")
        print(f"{label}: HTTP {snap.http_status} {len(body)} chars :: {url}\n    {body[:500]}")
        return snap.http_status, body
    except Exception as exc:
        print(f"{label}: {exc.__class__.__name__}: {str(exc)[:160]} :: {url}")
        return None, ""


def probe(iso2_list: list[str]) -> list[dict]:
    """Prints, per country, which years UN Comtrade has (public endpoint), whether its key-less preview returns
    HS-6 import values, and which WITS URL shapes answer at all."""
    today = date.today().year
    rows: list[dict] = []
    for iso2 in iso2_list:
        m49, iso3 = rates.M49.get(iso2.upper()), rates.ISO3.get(iso2.upper())
        row = {"country": iso2.upper(), "comtrade_latest": None, "preview": "", "wits": ""}
        if not m49:
            rows.append(row)
            continue
        status, body = _try(f"{iso2} comtrade availability", COMTRADE_AVAILABILITY.format(m49=int(m49)))
        years = [y for y in _years(body) if y <= today]
        row["comtrade_latest"] = years[-1] if years else None
        if years:
            # the newest annual dataset can be partial; test the three newest years, pacing the key-less
            # endpoint (it answers 429 "try again in 2 seconds" when called faster than that)
            found = []
            for y in years[-1:-4:-1]:
                time.sleep(3)
                status, body = _try(f"{iso2} comtrade preview {y}", COMTRADE_PREVIEW.format(m49=int(m49), year=y))
                v = total_value(body) if status == 200 else None
                if v is None:
                    time.sleep(3)
                    status, body = _try(f"{iso2} comtrade mirror {y}", COMTRADE_MIRROR.format(m49=int(m49), year=y))
                    mv = total_value(body, mirror=True) if status == 200 else None
                    found.append(f"{y}: mirror {mv:,.0f} USD" if mv else f"{y}: no value ({status})")
                else:
                    found.append(f"{y}: {v:,.0f} USD")
            row["preview"] = "; ".join(found)
        for shape in WITS_AVAILABILITY_SHAPES:
            status, body = _try(f"{iso2} wits availability", shape.format(iso3=iso3, m49=m49, year=today - 2))
            if status == 200 and "error" not in body[:200].lower():
                row["wits"] = f"availability ok: {shape.split('/country/')[1][:30]}"
                break
        for shape in WITS_SAMPLE_SHAPES:
            status, body = _try(f"{iso2} wits sample", shape.format(iso3=iso3, m49=m49, year=today - 2), timeout=180.0)
            if status == 200 and "error" not in body[:200].lower():
                row["wits"] += f"; sample ok ({len(body)} chars)"
                break
        rows.append(row)
    print("\n| country | Comtrade latest year | Comtrade key-less preview (610910 imports) | WITS |")
    print("|---|---|---|---|")
    for r in rows:
        print(f"| {r['country']} | {r['comtrade_latest']} | {r['preview']} | {r['wits'] or 'no usable reply'} |")
    return rows


def main(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="pipeline demand")
    parser.add_argument("--probe", help="comma-separated ISO2 importers to check data freshness for")
    parser.add_argument("--load", action="store_true", help="load import statistics for the site's pairs into data/demand")
    parser.add_argument("--importers", help="--load: comma-separated ISO2 importers (default: from pages and rates)")
    parser.add_argument("--hs6", help="--load: comma-separated HS-6 codes (default: from pages)")
    args, _ = parser.parse_known_args(argv)
    if args.probe:
        probe([c.strip() for c in args.probe.split(",") if c.strip()])
        return 0
    if args.load:
        load([c.strip().upper() for c in args.importers.split(",")] if args.importers else None, [c.strip() for c in args.hs6.split(",")] if args.hs6 else None)
        return 0
    parser.error("use --probe CA,CN,... or --load")
    return 2


# ---------------------------------------------------------------- loader and reader

ROOT = Path(__file__).resolve().parent.parent
DEMAND_DIR = ROOT / "data" / "demand"
PAGES_DIR = ROOT / "web" / "data" / "pages"
COMTRADE_IMPORTS = "https://comtradeapi.un.org/public/v1/preview/C/A/HS?reporterCode={m49}&period={year}&partnerCode=0&cmdCode={hs6}&flowCode=M"
COMTRADE_EXPORTS_TO = "https://comtradeapi.un.org/public/v1/preview/C/A/HS?reporterCode={reporter}&period={year}&partnerCode={m49}&cmdCode={hs6}&flowCode=X"
COMTRADE_PAGE = "https://comtradeplus.un.org/TradeFlow?Frequency=A&Flows=M&CommodityCodes={hs6}&Reporters={m49}&Partners=0"
MIRROR_PARTNERS = ("CN", "AE", "TR", "IN", "DE", "RU")  # partial mirror: major exporters, in this order
MAX_CALLS = int(os.environ.get("DEMAND_MAX_CALLS", "400"))
PACE_SECONDS = float(os.environ.get("DEMAND_PACE_SECONDS", "3"))
CACHE_DAYS = 30
STALE_YEARS = 3
YEARS_BACK = 4      # query the four years before the current one ...
KEEP_YEARS = 3      # ... and keep the three most recent that have a value


class _Budget:
    def __init__(self, max_calls: int = MAX_CALLS):
        self.max_calls = max_calls
        self.calls = 0
        self.stopped: str | None = None

    def call(self, url: str) -> str | None:
        """One paced GET; None when the budget is spent or the endpoint keeps refusing."""
        if self.stopped:
            return None
        if self.calls >= self.max_calls:
            self.stopped = f"DEMAND_MAX_CALLS={self.max_calls} reached; the rest waits for the next run"
            return None
        for attempt in range(2):
            time.sleep(PACE_SECONDS)
            self.calls += 1
            try:
                snap = fetch.fetch_url(url, save=False, timeout=120.0)
            except Exception as exc:
                print(f"demand: {exc.__class__.__name__} for {url[:120]}")
                return None
            body = snap.html or snap.text
            if snap.http_status == 429:
                m = re.search(r"(\d+) seconds", body)
                wait = int(m.group(1)) + 1 if m else 10
                if "day" in body.lower() or wait > 120:
                    self.stopped = f"UN Comtrade rate limit: {body[:100]}"
                    return None
                time.sleep(wait)
                continue
            if snap.http_status != 200:
                return None
            return body
        return None


def _load_file(iso2: str) -> dict:
    path = DEMAND_DIR / f"{iso2.upper()}.json"
    try:
        return json.loads(path.read_text(encoding="utf8"))
    except (OSError, json.JSONDecodeError):
        return {"country": iso2.upper(), "source": "UN Comtrade (public API, no key)", "series": {}}


def _save_file(doc: dict) -> None:
    DEMAND_DIR.mkdir(parents=True, exist_ok=True)
    (DEMAND_DIR / f"{doc['country']}.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf8")


def _fresh(entry: dict | None, today: date) -> bool:
    if not entry or not entry.get("fetched_at"):
        return False
    try:
        fetched = datetime.fromisoformat(entry["fetched_at"]).date()
    except ValueError:
        return False
    return (today - fetched).days < CACHE_DAYS


def fetch_series(iso2: str, hs6: str, budget: _Budget, today: date | None = None) -> dict | None:
    """Reported imports for the last years; a partial mirror when the country reports nothing at HS-6."""
    today = today or date.today()
    m49 = rates.M49.get(iso2.upper())
    if not m49:
        return None
    years: dict[str, float] = {}
    for y in range(today.year - 1, today.year - 1 - YEARS_BACK, -1):
        body = budget.call(COMTRADE_IMPORTS.format(m49=int(m49), year=y, hs6=hs6))
        if body is None and budget.stopped:
            return None
        v = total_value(body) if body else None
        if v:
            years[str(y)] = v
        if len(years) >= KEEP_YEARS:
            break
    kind, partners = "reported", 0
    if not years:
        # partial mirror: exports to this country as reported by major partners, latest two years only
        for y in range(today.year - 1, today.year - 3, -1):
            total, n = 0.0, 0
            for partner in MIRROR_PARTNERS:
                pm49 = rates.M49.get(partner)
                if not pm49 or partner == iso2.upper():
                    continue
                body = budget.call(COMTRADE_EXPORTS_TO.format(reporter=int(pm49), m49=int(m49), year=y, hs6=hs6))
                if body is None and budget.stopped:
                    return None
                v = total_value(body) if body else None
                if v:
                    total += v
                    n += 1
            if n:
                years[str(y)] = total
                partners = max(partners, n)
        kind = "mirror"
        if not years:
            return {"years": {}, "kind": "none", "partners": 0, "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    return {"years": years, "kind": kind, "partners": partners, "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}


def pairs_from_pages(pages_dir: Path = PAGES_DIR) -> tuple[list[str], list[str]]:
    """Importers = every page's destination plus every country with a rates table; HS-6 = every page's group."""
    importers, hs6s = set(), set()
    for path in sorted(pages_dir.glob("*.json")):
        try:
            page = json.loads(path.read_text(encoding="utf8"))
        except (OSError, json.JSONDecodeError):
            continue
        importers.add(page["corridor"]["to"]["code"])
        hs6s.add(page["product"]["hs6"])
    importers |= {p.stem.upper() for p in rates.RATES_DIR.glob("*.json")}
    return sorted(importers), sorted(hs6s)


def load(importers: list[str] | None = None, hs6s: list[str] | None = None, max_calls: int = MAX_CALLS, today: date | None = None) -> int:
    today = today or date.today()
    if importers is None or hs6s is None:
        auto_importers, auto_hs6 = pairs_from_pages()
        importers = importers or auto_importers
        hs6s = hs6s or auto_hs6
    budget = _Budget(max_calls)
    updated = 0
    for iso2 in importers:
        doc = _load_file(iso2)
        changed = False
        for hs6 in hs6s:
            if _fresh(doc["series"].get(hs6), today):
                continue
            series = fetch_series(iso2, hs6, budget, today)
            if series is None:
                break
            doc["series"][hs6] = series
            changed = True
            updated += 1
            print(f"demand {iso2} {hs6}: {series['kind']} {series['years']}")
        if changed:
            doc["fetched_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
            _save_file(doc)
        if budget.stopped:
            break
    print(f"demand: {updated} series updated, {budget.calls} calls" + (f"; stop: {budget.stopped}" if budget.stopped else ""))
    return updated


def get_demand(country: str, hs6: str, demand_dir: Path | None = None, today: date | None = None) -> dict | None:
    """Reader for the index layer: {"latest_year", "value", "growth_pct", "span_years", "kind", "partners",
    "stale", "fetched_at", "url"} or None when nothing is loaded for the pair."""
    today = today or date.today()
    path = (demand_dir or DEMAND_DIR) / f"{country.upper()}.json"
    try:
        doc = json.loads(path.read_text(encoding="utf8"))
    except (OSError, json.JSONDecodeError):
        return None
    entry = doc.get("series", {}).get(hs6)
    if not entry or not entry.get("years"):
        return None
    years = sorted((int(y), float(v)) for y, v in entry["years"].items())
    latest_year, latest = years[-1]
    first_year, first = years[0]
    growth = round((latest / first - 1) * 100) if first and latest_year > first_year else None
    m49 = rates.M49.get(country.upper(), "")
    return {
        "latest_year": latest_year, "value": latest, "growth_pct": growth, "span_years": latest_year - first_year,
        "kind": entry.get("kind", "reported"), "partners": entry.get("partners", 0),
        "stale": (today.year - latest_year) > STALE_YEARS, "fetched_at": entry.get("fetched_at", ""),
        "url": COMTRADE_PAGE.format(hs6=hs6, m49=int(m49) if m49 else ""),
    }


def usd_text(value: float) -> str:
    if value >= 1e9:
        return f"{value / 1e9:.1f} млрд USD"
    if value >= 1e6:
        return f"{value / 1e6:.0f} млн USD"
    if value >= 1e3:
        return f"{value / 1e3:.0f} тыс. USD"
    return f"{value:.0f} USD"
