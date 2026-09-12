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
WITS_URL = "https://wits.worldbank.org/API/V1/SDMX/V21/datasource/TRN/reporter/{iso3}/partner/000/product/all/year/{year}/datatype/reported"

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
    """Extracts {hs6: simple-average MFN rate} from a WITS TRAINS SDMX-ML response.

    The generic SDMX layout is <Series><SeriesKey><Value id="PRODUCTCODE" value="610910"/>...<Value id="TARIFFTYPE"
    value="MFN"/></SeriesKey><Obs><ObsDimension value="2023"/><ObsValue value="18"/></Obs></Series>, with the
    indicator name in a Value id="INDICATOR" (we keep "AHS-SMPL-AVRG"/"MFN-SMPL-AVRG": simple average). Namespaces
    vary between versions, so tags are matched by local name."""
    rates: dict[str, float] = {}
    year: int | None = None

    def local(tag: str) -> str:
        return tag.rsplit("}", 1)[-1]

    root = ElementTree.fromstring(xml_text)
    for series in root.iter():
        if local(series.tag) != "Series":
            continue
        key: dict[str, str] = {}
        for el in series.iter():
            if local(el.tag) == "Value" and el.get("id"):
                key[el.get("id", "").upper()] = el.get("value", "")
        product = key.get("PRODUCTCODE", "")
        indicator = key.get("INDICATOR", "").upper()
        tariff_type = key.get("TARIFFTYPE", "").upper()
        if not re.fullmatch(r"\d{6}", product):
            continue
        if indicator and "SMPL-AVRG" not in indicator and "SIMPLE" not in indicator:
            continue
        if tariff_type and tariff_type not in ("MFN", "AHS"):
            continue
        for obs in series.iter():
            if local(obs.tag) != "Obs":
                continue
            value = None
            for el in obs.iter():
                if local(el.tag) == "ObsValue":
                    value = el.get("value")
                if local(el.tag) == "ObsDimension" and el.get("value", "").isdigit():
                    year = int(el.get("value", "0"))
            if value not in (None, "", "NaN"):
                try:
                    rates[product] = float(value)
                except ValueError:
                    pass
    return rates, year


def load_wits(iso2: str, year: int | None = None, out_dir: Path = RATES_DIR) -> Path | None:
    iso3 = ISO3.get(iso2.upper())
    if not iso3:
        print(f"skip {iso2}: no ISO3 mapping yet")
        return None
    years = [year] if year else [date.today().year - 1, date.today().year - 2, date.today().year - 3]
    for y in years:
        url = WITS_URL.format(iso3=iso3, year=y)
        try:
            snap = fetch.fetch_url(url, save=False, timeout=120.0)
        except Exception as exc:
            print(f"skip {iso2} {y}: {exc.__class__.__name__}: {str(exc)[:120]}")
            continue
        if snap.http_status != 200 or "<" not in snap.text[:10]:
            print(f"skip {iso2} {y}: HTTP {snap.http_status}")
            continue
        rates, data_year = parse_wits_sdmx(snap.text)
        if not rates:
            print(f"skip {iso2} {y}: no HS-6 MFN series in response")
            continue
        out_dir.mkdir(parents=True, exist_ok=True)
        out = out_dir / f"{iso2.upper()}.json"
        out.write_text(
            json.dumps(
                {
                    "country": iso2.upper(),
                    "source": "World Bank WITS / UNCTAD TRAINS",
                    "url": url,
                    "year": data_year or y,
                    "fetched_at": snap.fetched_at,
                    "kind": "import_mfn",
                    "unit": "percent",
                    "rates": dict(sorted(rates.items())),
                },
                ensure_ascii=False,
                indent=0,
            )
            + "\n",
            encoding="utf8",
        )
        print(f"ok   {iso2}: {len(rates)} HS-6 rates for {data_year or y} -> {out}")
        return out
    return None


def get_rate(country: str, hs6: str, rates_dir: Path = RATES_DIR) -> dict | None:
    """Returns {"value", "year", "source", "url", "fetched_at"} for a country/HS-6 pair, or None when not loaded."""
    path = rates_dir / f"{country.upper()}.json"
    if not path.exists():
        return None
    doc = json.loads(path.read_text(encoding="utf8"))
    value = doc.get("rates", {}).get(hs6)
    if value is None:
        return None
    return {"value": value, "year": doc.get("year"), "source": doc.get("source"), "url": doc.get("url"), "fetched_at": doc.get("fetched_at")}


def main(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="pipeline rates")
    parser.add_argument("--wits", help="comma-separated ISO2 importers to load MFN rates for")
    parser.add_argument("--year", type=int)
    args, _ = parser.parse_known_args(argv)
    if not args.wits:
        parser.error("use --wits CA,CN,...")
    written = [load_wits(c.strip(), args.year) for c in args.wits.split(",") if c.strip()]
    print(f"{sum(1 for w in written if w)} rate file(s) written")
    return 0
