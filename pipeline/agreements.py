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
ASEAN = ["BN", "KH", "ID", "LA", "MY", "MM", "PH", "SG", "TH", "VN"]
CPTPP = ["AU", "BN", "CA", "CL", "JP", "MY", "MX", "NZ", "PE", "SG", "VN", "GB"]
RCEP = ASEAN + ["AU", "CN", "JP", "KR", "NZ"]
MERCOSUR = ["AR", "BR", "PY", "UY"]
PACIFIC_ALLIANCE = ["CL", "CO", "MX", "PE"]
SACU = ["BW", "LS", "NA", "ZA", "SZ"]
USMCA = ["US", "MX", "CA"]
CIS_FTA = ["AM", "BY", "KZ", "KG", "MD", "RU", "TJ", "UZ"]
ANDEAN = ["BO", "CO", "EC", "PE"]
CACM = ["CR", "SV", "GT", "HN", "NI"]
APTA = ["BD", "CN", "IN", "KR", "LA", "LK", "MN"]
ECO = ["AF", "AZ", "IR", "KZ", "KG", "PK", "TJ", "TR", "TM", "UZ"]
COMESA = ["BI", "KM", "CD", "DJ", "EG", "ER", "SZ", "ET", "KE", "LY", "MG", "MW", "MU", "RW", "SC", "SO", "SD", "TN", "UG", "ZM", "ZW"]
ECOWAS = ["BJ", "BF", "CV", "CI", "GM", "GH", "GN", "GW", "LR", "ML", "NE", "NG", "SN", "SL", "TG"]
EAC = ["BI", "CD", "KE", "RW", "SO", "SS", "TZ", "UG"]
SADC = ["AO", "BW", "KM", "CD", "SZ", "LS", "MG", "MW", "MU", "MZ", "NA", "SC", "ZA", "TZ", "ZM", "ZW"]
CEMAC = ["CM", "CF", "TD", "CG", "GQ", "GA"]
WAEMU = ["BJ", "BF", "CI", "GW", "ML", "NE", "SN", "TG"]
CARICOM = ["AG", "BS", "BB", "BZ", "DM", "GD", "GY", "HT", "JM", "KN", "LC", "VC", "SR", "TT"]
CEFTA = ["AL", "BA", "MD", "ME", "MK", "RS"]
AGADIR = ["EG", "JO", "MA", "TN"]

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
    "asean": ASEAN, "association of south east asian nations": ASEAN, "cptpp": CPTPP,
    "comprehensive and progressive agreement for trans-pacific partnership": CPTPP, "rcep": RCEP,
    "regional comprehensive economic partnership": RCEP, "mercosur": MERCOSUR, "southern common market": MERCOSUR,
    "pacific alliance": PACIFIC_ALLIANCE, "sacu": SACU, "southern african customs union": SACU, "usmca": USMCA, "cusma": USMCA,
    "united states - mexico - canada agreement": USMCA, "north american free trade agreement": USMCA, "nafta": USMCA,
    "cis": CIS_FTA, "commonwealth of independent states": CIS_FTA, "treaty on a free trade area between members of the cis": CIS_FTA,
    "andean community": ANDEAN, "can": ANDEAN, "central american common market": CACM, "cacm": CACM,
    "central america": CACM, "apta": APTA, "asia pacific trade agreement": APTA, "eco": ECO, "economic cooperation organization": ECO,
    "comesa": COMESA, "common market for eastern and southern africa": COMESA, "ecowas": ECOWAS, "economic community of west african states": ECOWAS,
    "eac": EAC, "east african community": EAC, "sadc": SADC, "southern african development community": SADC, "cemac": CEMAC,
    "economic and monetary community of central africa": CEMAC, "waemu": WAEMU, "uemoa": WAEMU, "west african economic and monetary union": WAEMU,
    "caricom": CARICOM, "caribbean community and common market": CARICOM, "cefta": CEFTA, "central european free trade agreement": CEFTA,
    "agadir agreement": AGADIR, "european free trade association": EFTA_MEMBERS, "eu treaty": EU_MEMBERS,
    "eu - efta": EU_MEMBERS + EFTA_MEMBERS, "european economic area": EU_MEMBERS + ["NO", "IS", "LI"], "eea": EU_MEMBERS + ["NO", "IS", "LI"],
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

    def lookup(name: str) -> list[str] | None:
        name = name.strip(" .").lower()
        if not name:
            return None
        name = re.sub(r"^(accession of|the)\s+", "", name)
        name = re.sub(r"^(accession of|the)\s+", "", name)
        candidates = [name, name.replace(" (the)", ""), name.split(",")[0].strip()]
        m = re.match(r"^(.*?)\s*\(([^)]*)\)\s*(\d{4})?$", name)  # "Eurasian Economic Union (EAEU)" -> both parts
        if m:
            candidates += [m.group(1).strip(), m.group(2).strip()]
        candidates.append(re.sub(r"\s*\([^)]*\)?\s*", " ", name).strip())  # "Costa Rica (Chile" -> "Costa Rica"
        for c in candidates:
            if c in index:
                return index[c]
        if " and " in name:  # "Colombia and Peru"
            found = [code for part in name.split(" and ") for code in (lookup(part) or [])]
            return found or None
        return None

    for raw in re.split(r"\s*[;|\n]\s*", text):
        for code in lookup(raw) or []:
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


def rows_to_agreements(table: list[list[str]], index: dict[str, list[str]] | None = None) -> list[dict]:
    """One record per agreement in force from a table whose first row is the header ('RTA Name', 'Status', ...).
    Members come from the signatories column when present, else from the parties in the RTA name
    ('Moldova, Republic of - Azerbaijan', 'EAEU - Iran'); unknown names are dropped, never guessed."""
    index = index or _country_index()
    if not table:
        return []
    header = [h.lower() for h in table[0]]
    if not any("rta name" in h for h in header):
        return []

    def col(*needles: str) -> int | None:
        for i, h in enumerate(header):
            if all(n in h for n in needles):
                return i
        return None

    c_name, c_type, c_status = col("rta name"), col("type"), col("status")
    c_force = col("entry into force") if col("entry into force") is not None else col("force")
    c_members = col("current", "signator") if col("current", "signator") is not None else col("signator")
    out: list[dict] = []
    for row in table[1:]:
        if c_name is None or len(row) <= c_name:
            continue
        status = row[c_status].lower() if c_status is not None and c_status < len(row) else "in force"
        if "force" not in status:
            continue
        name = row[c_name]
        if c_members is not None and c_members < len(row) and row[c_members].strip():
            members = names_to_iso2(row[c_members], index)
        else:
            members = names_to_iso2(name.replace(" - ", ";").replace(" – ", ";"), index)
        if len(members) < 2:
            continue
        out.append({
            "name": name,
            "type": row[c_type] if c_type is not None and c_type < len(row) else "",
            "in_force": _iso_date(row[c_force]) if c_force is not None and c_force < len(row) else "",
            "status": row[c_status] if c_status is not None and c_status < len(row) else "In Force",
            "members": members,
        })
    return out


def parse_rtais(html: str) -> list[dict]:
    """Finds the RTA table(s) in an HTML page by the 'RTA Name' header."""
    parser = _Tables()
    parser.feed(html)
    index = _country_index()
    out: list[dict] = []
    for table in parser.tables:
        out.extend(rows_to_agreements(table, index))
    return out


def parse_xlsx_rows(data: bytes) -> list[list[str]]:
    """Rows of the first sheet of an .xlsx file (zip of XML) — no third-party dependency."""
    import io
    import zipfile
    from xml.etree import ElementTree

    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in z.namelist():
            for si in ElementTree.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", ns):
                shared.append("".join(t.text or "" for t in si.iter("{%s}t" % ns["m"])))
        sheets = sorted(n for n in z.namelist() if n.startswith("xl/worksheets/sheet") and n.endswith(".xml"))
        if not sheets:
            return []
        root = ElementTree.fromstring(z.read(sheets[0]))
    rows: list[list[str]] = []
    for row in root.iter("{%s}row" % ns["m"]):
        cells: dict[int, str] = {}
        for c in row.findall("m:c", ns):
            ref = re.match(r"([A-Z]+)", c.get("r", "A"))
            col_idx = 0
            for ch in (ref.group(1) if ref else "A"):
                col_idx = col_idx * 26 + (ord(ch) - 64)
            v = c.find("m:v", ns)
            is_ = c.find("m:is", ns)
            if c.get("t") == "s" and v is not None and v.text and v.text.isdigit() and int(v.text) < len(shared):
                text = shared[int(v.text)]
            elif is_ is not None:
                text = "".join(t.text or "" for t in is_.iter("{%s}t" % ns["m"]))
            else:
                text = v.text or "" if v is not None else ""
            cells[col_idx] = re.sub(r"\s+", " ", text).strip()
        if cells:
            width = max(cells)
            rows.append([cells.get(i, "") for i in range(1, width + 1)])
    return rows


def parse_csv_rows(text: str) -> list[list[str]]:
    import csv
    import io

    sample = text[:2000]
    delimiter = ";" if sample.count(";") > sample.count(",") else ("\t" if sample.count("\t") > sample.count(",") else ",")
    return [[re.sub(r"\s+", " ", c).strip() for c in row] for row in csv.reader(io.StringIO(text), delimiter=delimiter)]


def parse_export(snap) -> list[dict]:
    """Agreements from whatever the RTA-IS export returns: an HTML table, an .xlsx workbook or a CSV/TSV file."""
    if snap.content[:2] == b"PK":
        return rows_to_agreements(parse_xlsx_rows(snap.content))
    if "<table" in snap.html.lower():
        return parse_rtais(snap.html)
    return rows_to_agreements(parse_csv_rows(snap.html))


def _links(html: str) -> list[tuple[str, str]]:
    out = []
    for m in re.finditer(r"<a\b([^>]*)>(.*?)</a>", html, re.I | re.S):
        href = re.search(r"href\s*=\s*[\"']([^\"']+)", m.group(1), re.I)
        text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", m.group(2))).strip()
        if href:
            out.append((href.group(1), text))
    return out


def _postback(page_html: str, url: str, target: str) -> "fetch.Snapshot":
    """ASP.NET postback: re-submits the page form with __EVENTTARGET (the export button). Whitelist enforced."""
    import httpx
    from datetime import datetime, timezone

    from . import registry

    if not registry.is_allowed(url):
        raise fetch.NotWhitelisted(url)
    form: dict[str, str] = {}
    for m in re.finditer(r"<input\b([^>]*)>", page_html, re.I):
        attrs = dict(re.findall(r"(\w+)\s*=\s*[\"']([^\"']*)", m.group(1)))
        if attrs.get("type", "").lower() in ("hidden", "text", "") and attrs.get("name"):
            form[attrs["name"]] = attrs.get("value", "")
    form["__EVENTTARGET"] = target
    form["__EVENTARGUMENT"] = ""
    with httpx.Client(follow_redirects=True, headers={"User-Agent": fetch.USER_AGENT}, timeout=300.0) as client:
        r = client.post(url, data=form)
    text = fetch.html_to_text(r.text) if "html" in r.headers.get("content-type", "") else ""
    return fetch.Snapshot(url=url, fetched_at=datetime.now(timezone.utc).isoformat(timespec="seconds"), http_status=r.status_code, content_hash="", text=text, path=None, html=r.text if "PK" != r.content[:2] else "", content=r.content)


def build(out: Path = AGREEMENTS_FILE) -> Path | None:
    """Loads the complete list of RTAs in force. The list page shows 20 rows per page, so the full set comes from the
    site's "Export all RTAs" link (a file or an ASP.NET postback); a partial list is never written."""
    snap = fetch.fetch_url(RTAIS_URL, save=False, timeout=180.0)
    if snap.http_status != 200:
        print(f"skip agreements: HTTP {snap.http_status} from {RTAIS_URL}")
        return None
    total = re.search(r"Result\(s\) found \((\d+)\)", snap.text)
    expected = int(total.group(1)) if total else None
    from urllib.parse import urljoin

    candidates = [(href, text) for href, text in _links(snap.html) if "export" in text.lower()]
    agreements: list[dict] = []
    used = RTAIS_URL
    for href, text in candidates:
        try:
            if href.lower().startswith("javascript:"):
                m = re.search(r"__doPostBack\('([^']+)'", href)
                if not m:
                    continue
                exp = _postback(snap.html, RTAIS_URL, m.group(1))
                used = f"{RTAIS_URL} (postback {m.group(1)})"
            else:
                used = urljoin(RTAIS_URL, href)
                exp = fetch.fetch_url(used, save=False, timeout=300.0)
            if exp.http_status != 200:
                print(f"export {text!r}: HTTP {exp.http_status}")
                continue
            agreements = parse_export(exp)
            print(f"export {text!r} -> {len(agreements)} agreements in force ({len(exp.content)} bytes)")
            if agreements:
                break
        except Exception as exc:  # diagnostics only; the next candidate is tried
            print(f"export {text!r} failed: {exc.__class__.__name__}: {str(exc)[:200]}")
    if not agreements:
        print(f"skip agreements: no complete list obtained. Links on the page: {[(h[:80], t[:40]) for h, t in _links(snap.html) if t][:40]}")
        return None
    if expected and len(agreements) < expected * 0.8:
        print(f"skip agreements: export has {len(agreements)} rows, the page reports {expected} in force — refusing a partial list")
        return None
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"source": "WTO RTA-IS", "url": RTAIS_URL, "export": used, "fetched_at": snap.fetched_at, "in_force_reported": expected, "agreements": agreements}, ensure_ascii=False, indent=0) + "\n", encoding="utf8")
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
