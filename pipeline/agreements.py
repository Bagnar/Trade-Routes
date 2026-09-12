"""agreements — the index layer for trade agreements: which regional trade agreements (RTAs) are in force between
two countries, from the WTO RTA Information System (rtais.wto.org), an official WTO database listed in
data/sources.yaml (`international`, id `wto-rtais`).

Output: data/agreements.json
  {"source": "WTO RTA-IS", "url": ..., "fetched_at": ..., "agreements": [
     {"name": "EAEU - Iran", "type": "FTA", "in_force": "2025-05-15", "members": ["AM", "BY", "IR", ...]}]}

Rules this module must never break: the list comes only from the WTO page (no hand-typed agreements); a pair
without a match is reported as "not in the WTO RTA database", never as "no agreement" from memory; when the
file is absent the index says "not checked".

Run:  python -m pipeline agreements            (network: GitHub Actions, reference-data.yml)
      python -m pipeline agreements --between RU IR
"""
from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path

from . import fetch

ROOT = Path(__file__).resolve().parent.parent
AGREEMENTS_FILE = ROOT / "data" / "agreements.json"
COUNTRIES_FILE = ROOT / "data" / "countries.json"
RTAIS_URL = "https://rtais.wto.org/UI/PublicAllRTAList.aspx"

EU_MEMBERS = ["AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK", "SI", "ES", "SE"]
EFTA_MEMBERS = ["CH", "NO", "IS", "LI"]
EAEU_MEMBERS = ["RU", "BY", "KZ", "AM", "KG"]
GCC_MEMBERS = ["SA", "AE", "QA", "KW", "OM", "BH"]

# Names as RTA-IS writes them -> ISO2 (or a group). Everything not listed here falls back to data/countries.json.
ALIASES: dict[str, list[str]] = {
    "european union": EU_MEMBERS, "eu": EU_MEMBERS, "efta": EFTA_MEMBERS, "eurasian economic union": EAEU_MEMBERS,
    "eaeu": EAEU_MEMBERS, "gulf cooperation council": GCC_MEMBERS, "gcc": GCC_MEMBERS,
    "united states": ["US"], "united states of america": ["US"], "korea, republic of": ["KR"], "republic of korea": ["KR"],
    "russian federation": ["RU"], "russia": ["RU"], "iran": ["IR"], "iran, islamic republic of": ["IR"], "türkiye": ["TR"],
    "turkiye": ["TR"], "turkey": ["TR"], "viet nam": ["VN"], "vietnam": ["VN"], "hong kong, china": ["HK"], "macao, china": ["MO"],
    "chinese taipei": ["TW"], "taiwan": ["TW"], "united kingdom": ["GB"], "uk": ["GB"], "czech republic": ["CZ"], "czechia": ["CZ"],
    "north macedonia": ["MK"], "republic of moldova": ["MD"], "moldova": ["MD"], "lao pdr": ["LA"], "laos": ["LA"],
    "bolivia, plurinational state of": ["BO"], "venezuela, bolivarian republic of": ["VE"], "syrian arab republic": ["SY"],
    "tanzania": ["TZ"], "united republic of tanzania": ["TZ"], "kyrgyz republic": ["KG"], "kyrgyzstan": ["KG"], "brunei darussalam": ["BN"],
    "cote d'ivoire": ["CI"], "côte d'ivoire": ["CI"], "cabo verde": ["CV"], "eswatini": ["SZ"], "timor-leste": ["TL"],
    "democratic republic of the congo": ["CD"], "congo, democratic republic of the": ["CD"], "congo": ["CG"], "china": ["CN"],
    "japan": ["JP"], "canada": ["CA"], "australia": ["AU"], "new zealand": ["NZ"], "india": ["IN"], "mexico": ["MX"],
}


def _country_index() -> dict[str, list[str]]:
    index = dict(ALIASES)
    try:
        for row in json.loads(COUNTRIES_FILE.read_text(encoding="utf8")):
            index.setdefault(row["name_en"].lower(), [row["code"]])
    except (OSError, json.JSONDecodeError, KeyError):
        pass
    return index


def names_to_iso2(text: str, index: dict[str, list[str]] | None = None) -> list[str]:
    """'European Union; Viet Nam' -> ['AT', ..., 'VN']. Unknown names are dropped (never guessed)."""
    index = index or _country_index()
    out: list[str] = []
    for raw in re.split(r"\s*[;|\n]\s*", text):
        name = raw.strip().strip(".").lower()
        if not name:
            continue
        codes = index.get(name) or index.get(name.replace(" (the)", ""))
        for code in codes or []:
            if code not in out:
                out.append(code)
    return out


class _Tables(HTMLParser):
    """Collects every <table> as rows of cell texts (links and formatting removed)."""

    def __init__(self) -> None:
        super().__init__()
        self.tables: list[list[list[str]]] = []
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self.tables.append([])
        elif tag == "tr" and self.tables:
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = []
        elif tag == "br" and self._cell is not None:
            self._cell.append("; ")

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._cell is not None and self._row is not None:
            self._row.append(re.sub(r"\s+", " ", "".join(self._cell)).strip())
            self._cell = None
        elif tag == "tr" and self._row is not None:
            if self._row and self.tables:
                self.tables[-1].append(self._row)
            self._row = None

    def handle_data(self, data):
        if self._cell is not None:
            self._cell.append(data)


def _iso_date(text: str) -> str:
    """'15-May-2025' / '15/05/2025' / '2025-05-15' -> '2025-05-15'; anything else returned as-is."""
    months = {m: i for i, m in enumerate(("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"), 1)}
    m = re.match(r"^\s*(\d{1,2})[-/ ]([A-Za-z]{3})[a-z]*[-/ ](\d{4})", text)
    if m and m.group(2).lower() in months:
        return f"{m.group(3)}-{months[m.group(2).lower()]:02d}-{int(m.group(1)):02d}"
    m = re.match(r"^\s*(\d{1,2})/(\d{1,2})/(\d{4})", text)
    if m:
        return f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
    m = re.match(r"^\s*(\d{4}-\d{2}-\d{2})", text)
    return m.group(1) if m else text.strip()


def parse_rtais(html: str) -> list[dict]:
    """Finds the RTA table by its header ('RTA Name', '... signatories') and returns one record per agreement."""
    parser = _Tables()
    parser.feed(html)
    index = _country_index()
    out: list[dict] = []
    for table in parser.tables:
        if not table:
            continue
        header = [h.lower() for h in table[0]]
        if not any("rta name" in h for h in header) or not any("signator" in h for h in header):
            continue

        def col(*needles: str) -> int | None:
            for i, h in enumerate(header):
                if all(n in h for n in needles):
                    return i
            return None

        c_name, c_type, c_status = col("rta name"), col("type"), col("status")
        c_force = col("entry into force") if col("entry into force") is not None else col("force")
        c_members = col("current", "signator") if col("current", "signator") is not None else col("signator")
        for row in table[1:]:
            if c_name is None or c_members is None or len(row) <= max(c_name, c_members):
                continue
            status = row[c_status].lower() if c_status is not None and c_status < len(row) else "in force"
            if "force" not in status:
                continue
            members = names_to_iso2(row[c_members], index)
            if len(members) < 2:
                continue
            out.append({
                "name": row[c_name],
                "type": row[c_type] if c_type is not None and c_type < len(row) else "",
                "in_force": _iso_date(row[c_force]) if c_force is not None and c_force < len(row) else "",
                "members": members,
            })
    return out


def build(out: Path = AGREEMENTS_FILE) -> Path | None:
    snap = fetch.fetch_url(RTAIS_URL, save=False, timeout=180.0)
    if snap.http_status != 200:
        print(f"skip agreements: HTTP {snap.http_status} from {RTAIS_URL}")
        return None
    agreements = parse_rtais(snap.text)
    if not agreements:
        print(f"skip agreements: no RTA table recognised in {len(snap.text)} chars from {RTAIS_URL}")
        print(snap.text[:1500])
        return None
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"source": "WTO RTA-IS", "url": RTAIS_URL, "fetched_at": snap.fetched_at, "agreements": agreements}, ensure_ascii=False, indent=0) + "\n", encoding="utf8")
    print(f"ok   {len(agreements)} agreements in force -> {out}")
    return out


def load(path: Path = AGREEMENTS_FILE) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf8"))
    except json.JSONDecodeError:
        return None


def between(a: str, b: str, doc: dict | None = None) -> list[dict] | None:
    """Agreements in force that include both countries; None when the database has not been loaded."""
    doc = doc if doc is not None else load()
    if doc is None:
        return None
    a, b = a.upper(), b.upper()
    return [x for x in doc.get("agreements", []) if a in x["members"] and b in x["members"]]


def main(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="pipeline agreements")
    parser.add_argument("--between", nargs=2, metavar=("A", "B"), help="print agreements between two ISO2 codes")
    args, _ = parser.parse_known_args(argv)
    if args.between:
        found = between(*args.between)
        print("not loaded (run without --between from GitHub Actions)" if found is None else json.dumps(found, ensure_ascii=False, indent=1))
        return 0
    build()
    return 0
