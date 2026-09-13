"""demand — trade statistics for the "спрос" part of the rating (docs/concept.md: always an "ориентир").

Stage 1: World Bank WITS trade statistics (UN Comtrade data served by WITS, no key). Before any number is
used, `--probe` checks freshness: which years WITS has for a reporter, compared with what UN Comtrade itself
reports as available (public data-availability endpoint, no key). The comparison decides whether WITS is
fresh enough or the project needs a UN Comtrade API key.

Run:  python -m pipeline demand --probe CA,CN,RU,IR,TR     (network: GitHub Actions, reference-data.yml)
"""
from __future__ import annotations

import json
import re
from datetime import date

from . import fetch, rates

# WITS "tradestats-trade" datasource: import/export values by reporter, partner, product (HS-6), year.
WITS_AVAILABILITY = "https://wits.worldbank.org/API/V1/wits/datasource/tradestats-trade/dataavailability/country/{reporter}/year/all?format=JSON"
WITS_SAMPLE = "https://wits.worldbank.org/API/V1/SDMX/V21/datasource/tradestats-trade/reporter/{reporter}/year/{year}/partner/wld/product/{hs6}/indicator/MPRT-TRD-VL"
# UN Comtrade public data-availability endpoint (no subscription key): annual (A) goods (C) data by HS.
COMTRADE_AVAILABILITY = "https://comtradeapi.un.org/public/v1/getDA/C/A/HS?reporterCode={m49}"


def _years(text: str) -> list[int]:
    """Years mentioned in an availability reply, whatever its exact shape (JSON or XML)."""
    found = {int(y) for y in re.findall(r"\b(19[89]\d|20[0-4]\d)\b", text)}
    return sorted(found)


def probe(iso2_list: list[str]) -> list[dict]:
    """Prints, per country, the latest year in WITS and in UN Comtrade, plus a sample WITS value request."""
    today = date.today().year
    rows: list[dict] = []
    for iso2 in iso2_list:
        m49 = rates.M49.get(iso2.upper())
        row = {"country": iso2.upper(), "wits_latest": None, "comtrade_latest": None, "wits_years": [], "comtrade_years": [], "sample": ""}
        if not m49:
            print(f"{iso2}: no M49 code mapping")
            rows.append(row)
            continue
        for key, url in (("wits", WITS_AVAILABILITY.format(reporter=m49)), ("comtrade", COMTRADE_AVAILABILITY.format(m49=int(m49)))):
            try:
                snap = fetch.fetch_url(url, save=False, timeout=120.0)
                body = snap.html or snap.text
                years = [y for y in _years(body) if y <= today]
                row[f"{key}_years"] = years
                row[f"{key}_latest"] = years[-1] if years else None
                print(f"{iso2} {key}: HTTP {snap.http_status}, years {years[:3]}…{years[-3:] if years else ''} ({len(years)}) :: {body[:200].replace(chr(10), ' ')}")
            except Exception as exc:
                print(f"{iso2} {key}: {exc.__class__.__name__}: {str(exc)[:160]}")
        if row["wits_latest"]:
            url = WITS_SAMPLE.format(reporter=m49, year=row["wits_latest"], hs6="610910")
            try:
                snap = fetch.fetch_url(url, save=False, timeout=180.0)
                body = snap.html or snap.text
                row["sample"] = f"HTTP {snap.http_status}, {len(body)} chars"
                print(f"{iso2} sample {url}\n    {body[:600].replace(chr(10), ' ')}")
            except Exception as exc:
                row["sample"] = f"{exc.__class__.__name__}"
                print(f"{iso2} sample: {exc.__class__.__name__}: {str(exc)[:160]}")
        rows.append(row)
    print("\n| country | WITS latest | Comtrade latest | lag | verdict |")
    print("|---|---|---|---|---|")
    for r in rows:
        w, c = r["wits_latest"], r["comtrade_latest"]
        lag = (c - w) if (w and c) else None
        verdict = "no data" if not w else ("fresh" if (today - w) <= 2 and (lag is None or lag <= 1) else "stale: use Comtrade key" if lag and lag > 1 else "old (>2 years)")
        print(f"| {r['country']} | {w} | {c} | {lag} | {verdict} |")
    return rows


def main(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="pipeline demand")
    parser.add_argument("--probe", help="comma-separated ISO2 importers to check data freshness for")
    args, _ = parser.parse_known_args(argv)
    if not args.probe:
        parser.error("use --probe CA,CN,...")
    probe([c.strip() for c in args.probe.split(",") if c.strip()])
    return 0
