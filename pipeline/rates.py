"""rates — the structured rates layer. Numbers on the site come from here, never from a model.

Stage 1 source: World Bank WITS (UNCTAD TRAINS) — MFN applied ("AHS"/"MFN") simple average tariffs by HS-6
per importer, served as SDMX-ML: https://wits.worldbank.org/API/V1/SDMX/V21/datasource/TRN/reporter/{iso3}/
partner/000/product/all/year/{year}/datatype/reported. WITS is an international-organisation source
(data/sources.yaml, `international`). Later sources: national tariff schedules (CBSA T2026, EU TARIC, ЕТТ ЕАЭС).

Output: data/rates/{ISO2}.json
  {"country": "CA", "source": "WITS/TRAINS", "url": ..., "year": 2023, "fetched_at": ..., "kind": "import_mfn",
   "unit": "percent", "rates": {"610910": 18.0, ...}}

Run:  python -m pipeline rates --wits CA,CN     (network: GitHub Actions, reference-data.yml)
"""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from xml.etree import ElementTree

from . import fetch

ROOT = Path(__file__).resolve().parent.parent
RATES_DIR = ROOT / "data" / "rates"
WITS_URL = "https://wits.worldbank.org/API/V1/SDMX/V21/datasource/TRN/reporter/{reporter}/partner/000/product/all/year/{year}/datatype/reported"
# "reported" carries only ad valorem duties: tariff lines with a specific or compound duty ("10%, but not less than
# 1.75 EUR/kg") count as NBR_NA_LINES and the simple average shows 0. "aveestimated" is WITS's ad valorem equivalent
# for those lines (seen 2026-09-13: KZ 610910 reported 0 / NA lines 1, aveestimated 9.66). The loader takes the AVE
# and records which HS-6 groups are estimates, so the page can say so.
WITS_AVE_URL = WITS_URL.replace("/datatype/reported", "/datatype/aveestimated")
WITS_AVAILABILITY = "https://wits.worldbank.org/API/V1/wits/datasource/trn/dataavailability/country/{reporter}/year/{year}?format=JSON"

# UN M49 numeric codes as used by WITS/UNCTAD TRAINS (Comtrade-style codes for FR/IT/CH/NO/BE).
M49 = {
    "CA": "124", "CN": "156", "RU": "643", "IR": "364", "TR": "792", "US": "840", "DE": "276", "KZ": "398", "UZ": "860",
    "AE": "784", "IN": "356", "VN": "704", "BR": "076", "EG": "818", "JP": "392", "KR": "410", "GB": "826", "AU": "036",
    "MX": "484", "ID": "360", "SA": "682", "ZA": "710", "AR": "032", "PL": "616", "FR": "251", "IT": "381", "ES": "724",
    "NL": "528", "BE": "056", "SE": "752", "CH": "757", "NO": "579", "UA": "804", "BY": "112", "GE": "268", "AM": "051",
    "AZ": "031", "KG": "417", "TJ": "762", "MN": "496", "PK": "586", "BD": "050", "TH": "764", "MY": "458", "SG": "702",
    "PH": "608", "NG": "566", "KE": "404", "ET": "231", "MA": "504", "DZ": "012", "TN": "788", "IQ": "368", "QA": "634",
    "KW": "414", "OM": "512", "IL": "376", "JO": "400", "LB": "422", "CL": "152", "CO": "170", "PE": "604", "NZ": "554",
}

# ISO2 -> ISO3 for the reporters we load first; extend as countries are added.
ISO3 = {
    "CA": "CAN", "CN": "CHN", "RU": "RUS", "IR": "IRN", "TR": "TUR", "US": "USA", "DE": "DEU", "KZ": "KAZ", "UZ": "UZB",
    "AE": "ARE", "IN": "IND", "VN": "VNM", "BR": "BRA", "EG": "EGY", "JP": "JPN", "KR": "KOR", "GB": "GBR", "AU": "AUS",
    "MX": "MEX", "ID": "IDN", "SA": "SAU", "ZA": "ZAF", "AR": "ARG", "PL": "POL", "FR": "FRA", "IT": "ITA", "ES": "ESP",
    "NL": "NLD", "BE": "BEL", "SE": "SWE", "CH": "CHE", "NO": "NOR", "UA": "UKR", "BY": "BLR", "GE": "GEO", "AM": "ARM",
    "AZ": "AZE", "KG": "KGZ", "TJ": "TJK", "MN": "MNG", "PK": "PAK", "BD": "BGD", "TH": "THA", "MY": "MYS", "SG": "SGP",
    "PH": "PHL", "NG": "NGA", "KE": "KEN", "ET": "ETH", "MA": "MAR", "DZ": "DZA", "TN": "TUN", "IQ": "IRQ", "QA": "QAT",
    "KW": "KWT", "OM": "OMN", "IL": "ISR", "JO": "JOR", "LB": "LBN", "CL": "CHL", "CO": "COL", "PE": "PER", "NZ": "NZL",
}


def parse_wits_sdmx(xml_text: str) -> tuple[dict[str, float], int | None]:
    """Extracts {hs6: simple-average MFN rate} from a WITS TRAINS SDMX-ML response (see parse_wits_sdmx_full)."""
    rates, year, _ = parse_wits_sdmx_full(xml_text)
    return rates, year


def parse_wits_sdmx_full(xml_text: str) -> tuple[dict[str, float], int | None, dict[str, int]]:
    """Extracts {hs6: simple-average MFN rate}, the year and {hs6: NBR_NA_LINES} (tariff lines whose duty is not
    ad valorem and so is missing from the "reported" average) from a WITS TRAINS SDMX-ML response.

    WITS answers in the SDMX 2.1 *structure-specific* layout (seen 2026-09-12): dimensions are attributes of
    <Series PRODUCTCODE="010121" REPORTER="124" ...> and the observation carries the rest:
    <Obs TIME_PERIOD="2023" OBS_VALUE="0" TARIFFTYPE="MFN" OBS_VALUE_MEASURE="SimpleAverage" .../>.
    The *generic* layout (<SeriesKey><Value id=... value=.../></SeriesKey><Obs><ObsValue value=.../></Obs>) is
    handled too. Only the simple average of the MFN (or AHS) rate is kept; namespaces are ignored (local names)."""
    rates: dict[str, float] = {}
    na_lines: dict[str, int] = {}
    year: int | None = None

    def local(tag: str) -> str:
        return tag.rsplit("}", 1)[-1]

    root = ElementTree.fromstring(xml_text)
    for series in root.iter():
        if local(series.tag) != "Series":
            continue
        key: dict[str, str] = {k.upper(): v for k, v in series.attrib.items()}
        for el in series.iter():
            if local(el.tag) == "Value" and el.get("id"):
                key[el.get("id", "").upper()] = el.get("value", "")
        product = key.get("PRODUCTCODE", "")
        if not re.fullmatch(r"\d{6}", product):
            continue
        for obs in series.iter():
            if local(obs.tag) != "Obs":
                continue
            attrs = {**key, **{k.upper(): v for k, v in obs.attrib.items()}}
            value = attrs.get("OBS_VALUE")
            for el in obs.iter():
                if local(el.tag) == "ObsValue":
                    value = el.get("value")
                if local(el.tag) == "ObsDimension" and el.get("value", "").isdigit():
                    attrs["TIME_PERIOD"] = el.get("value", "")
                if local(el.tag) == "Value" and el.get("id"):
                    attrs[el.get("id", "").upper()] = el.get("value", "")
            indicator = attrs.get("INDICATOR", "").upper()
            measure = attrs.get("OBS_VALUE_MEASURE", "").replace(" ", "").upper()
            tariff_type = attrs.get("TARIFFTYPE", "").upper()
            if indicator and "SMPL-AVRG" not in indicator and "SIMPLE" not in indicator:
                continue
            if measure and "SIMPLEAVERAGE" not in measure:
                continue
            if tariff_type and tariff_type not in ("MFN", "AHS"):
                continue
            if str(attrs.get("TIME_PERIOD", "")).isdigit():
                year = int(attrs["TIME_PERIOD"])
            if value not in (None, "", "NaN"):
                try:
                    rates[product] = float(value)
                except ValueError:
                    pass
                na = attrs.get("NBR_NA_LINES", "")
                if str(na).isdigit() and int(na) > 0:
                    na_lines[product] = int(na)
    return rates, year, na_lines


def probe(iso2: str) -> None:
    """Diagnostics for the WITS endpoint: prints status and the first bytes of the reply for several URL shapes."""
    iso3, m49 = ISO3.get(iso2.upper(), ""), M49.get(iso2.upper(), "")
    year = date.today().year - 2
    candidates = [
        WITS_AVAILABILITY.format(reporter=m49, year=year),
        WITS_URL.format(reporter=m49, year=year),
        WITS_URL.format(reporter=iso3, year=year),
        WITS_URL.format(reporter=m49, year=year).replace("/product/all/", "/product/Total/"),
        WITS_URL.format(reporter=m49, year=year).replace("/product/all/", "/product/010121/"),
        f"https://wits.worldbank.org/API/V1/SDMX/V21/datasource/TRN/reporter/{m49}/partner/000/product/all/year/{year}/datatype/reported?format=JSON",
        f"https://wits.worldbank.org/API/V1/SDMX/V21/rest/data/DF_WITS_Tariff_TRAINS/A.{m49}.000.all.reported/?startPeriod={year}&endPeriod={year}",
    ]
    for url in candidates:
        try:
            snap = fetch.fetch_url(url, save=False, timeout=120.0)
            body = snap.text.replace("\n", " ")[:300]
            print(f"HTTP {snap.http_status}  {url}\n    {body}")
        except Exception as exc:
            print(f"ERR  {url}\n    {exc.__class__.__name__}: {str(exc)[:200]}")
    # Specific and compound duties ("10%, но не менее 1,75 евро за 1 кг"): does "reported" show 0 while
    # "aveestimated" carries the ad-valorem equivalent? Compared on a few products with such duties.
    for product in ("610910", "020130", "040610", "220421"):
        for datatype in ("reported", "aveestimated"):
            for y in range(year, year - 5, -1):  # the latest year TRAINS has for this reporter
                url = WITS_URL.format(reporter=m49, year=y).replace("/product/all/", f"/product/{product}/").replace("/datatype/reported", f"/datatype/{datatype}")
                try:
                    snap = fetch.fetch_url(url, save=False, timeout=120.0)
                except Exception as exc:
                    print(f"ERR  {url}\n    {exc.__class__.__name__}: {str(exc)[:200]}")
                    break
                if snap.http_status != 200:
                    continue
                obs = re.findall(r"<Obs\b[^>]*>", snap.text)[:3]
                print(f"HTTP {snap.http_status}  {url}\n    {' | '.join(o[:260] for o in obs) if obs else snap.text.replace(chr(10), ' ')[:300]}")
                break
            else:
                print(f"no data for product {product} datatype {datatype} in {year - 4}..{year}")
    # Structure of a successful reply: first bytes plus the distinct element names and Value ids seen.
    for y in (year, year - 1):
        url = WITS_URL.format(reporter=m49, year=y)
        try:
            snap = fetch.fetch_url(url, save=False, timeout=180.0)
        except Exception as exc:
            print(f"ERR  {url}: {exc}")
            continue
        print(f"--- {url}: HTTP {snap.http_status}, {len(snap.text)} chars")
        print(snap.text[:2500])
        if snap.http_status == 200 and snap.text.lstrip().startswith("<"):
            try:
                root = ElementTree.fromstring(snap.text)
                tags: dict[str, int] = {}
                ids: dict[str, set[str]] = {}
                for el in root.iter():
                    tag = el.tag.rsplit("}", 1)[-1]
                    tags[tag] = tags.get(tag, 0) + 1
                    if el.get("id"):
                        ids.setdefault(el.get("id", ""), set()).add(el.get("value", "")[:20])
                print("TAGS:", sorted(tags.items(), key=lambda kv: -kv[1])[:25])
                for k, v in list(ids.items())[:30]:
                    print(f"ID {k}: {sorted(v)[:8]} ({len(v)} distinct)")
            except ElementTree.ParseError as exc:
                print("XML parse error:", exc)
            break


def load_wits(iso2: str, year: int | None = None, out_dir: Path = RATES_DIR) -> Path | None:
    reporters = [M49[iso2.upper()]] if iso2.upper() in M49 else [c for c in (ISO3.get(iso2.upper()),) if c]  # WITS accepts M49 only
    if not reporters:
        print(f"skip {iso2}: no reporter code mapping yet")
        return None
    years = [year] if year else [date.today().year - n for n in range(1, 9)]  # TRAINS lags: RU/IR had nothing for 2023
    for y in years:
        for reporter in reporters:
            url = WITS_URL.format(reporter=reporter, year=y)
            try:
                snap = fetch.fetch_url(url, save=False, timeout=180.0)
            except Exception as exc:
                print(f"skip {iso2} {y} ({reporter}): {exc.__class__.__name__}: {str(exc)[:120]}")
                continue
            if snap.http_status != 200 or "<" not in snap.text[:10]:
                print(f"skip {iso2} {y} ({reporter}): HTTP {snap.http_status} {snap.text[:160]!r}")
                continue
            rates, data_year, na_lines = parse_wits_sdmx_full(snap.text)
            if not rates:
                print(f"skip {iso2} {y} ({reporter}): no HS-6 MFN series in response")
                continue
            # Ad valorem equivalents for the groups whose lines carry specific/compound duties.
            ave_url = WITS_AVE_URL.format(reporter=reporter, year=y)
            specific = sorted(na_lines)
            try:
                ave_snap = fetch.fetch_url(ave_url, save=False, timeout=180.0)
                ave, _, _ = parse_wits_sdmx_full(ave_snap.text) if ave_snap.http_status == 200 and "<" in ave_snap.text[:10] else ({}, None, {})
            except Exception as exc:
                print(f"warn {iso2} {y}: ad valorem equivalents not loaded: {exc.__class__.__name__}: {str(exc)[:120]}")
                ave = {}
            if ave:
                for hs6 in specific:
                    if hs6 in ave:
                        rates[hs6] = ave[hs6]
            else:
                print(f"warn {iso2} {y}: no aveestimated data; {len(specific)} groups with specific duties keep the reported (partial) average")
            out_dir.mkdir(parents=True, exist_ok=True)
            out = out_dir / f"{iso2.upper()}.json"
            out.write_text(
                json.dumps(
                    {
                        "country": iso2.upper(),
                        "source": "World Bank WITS / UNCTAD TRAINS",
                        "url": url,
                        "url_ave": ave_url if ave else "",
                        "year": data_year or y,
                        "fetched_at": snap.fetched_at,
                        "kind": "import_mfn",
                        "unit": "percent",
                        "specific": specific if ave else [],
                        "rates": dict(sorted(rates.items())),
                    },
                    ensure_ascii=False,
                    indent=0,
                )
                + "\n",
                encoding="utf8",
            )
            print(f"ok   {iso2}: {len(rates)} HS-6 rates for {data_year or y}, {len(specific) if ave else 0} ad valorem equivalents -> {out}")
            return out
    return None


def get_rate(country: str, hs6: str, rates_dir: Path | None = None) -> dict | None:
    """Returns {"value", "year", "source", "url", "fetched_at", "estimated"} for a country/HS-6 pair, or None when not
    loaded. "estimated" = the value is WITS's ad valorem equivalent of a specific or compound duty."""
    path = (rates_dir or RATES_DIR) / f"{country.upper()}.json"
    if not path.exists():
        return None
    doc = json.loads(path.read_text(encoding="utf8"))
    value = doc.get("rates", {}).get(hs6)
    if value is None:
        return None
    estimated = hs6 in set(doc.get("specific", []))
    return {"value": value, "year": doc.get("year"), "source": doc.get("source"), "url": (doc.get("url_ave") or doc.get("url")) if estimated else doc.get("url"), "fetched_at": doc.get("fetched_at"), "estimated": estimated}


def main(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="pipeline rates")
    parser.add_argument("--wits", help="comma-separated ISO2 importers to load MFN rates for")
    parser.add_argument("--year", type=int)
    parser.add_argument("--probe", help="diagnostics: try several WITS URL shapes for one ISO2 and print replies")
    args, _ = parser.parse_known_args(argv)
    if args.probe:
        probe(args.probe)
        return 0
    if not args.wits:
        parser.error("use --wits CA,CN,...")
    written = [load_wits(c.strip(), args.year) for c in args.wits.split(",") if c.strip()]
    print(f"{sum(1 for w in written if w)} rate file(s) written")
    return 0
