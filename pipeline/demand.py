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
import time
from datetime import date

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
                m = re.search(r'"primaryValue":\s*([0-9.eE+]+)', body)
                found.append(f"{y}: {float(m.group(1)):,.0f} USD" if (status == 200 and m) else f"{y}: no value ({status}, {body[:40]!r})")
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
    args, _ = parser.parse_known_args(argv)
    if not args.probe:
        parser.error("use --probe CA,CN,...")
    probe([c.strip() for c in args.probe.split(",") if c.strip()])
    return 0
