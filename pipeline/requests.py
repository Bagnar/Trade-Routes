"""requests — the corridor request queue (docs/expansion-plan.md, 1.9): "Запросить коридор" on the site opens a
prefilled GitHub issue (label `corridor-request`, template .github/ISSUE_TEMPLATE/corridor-request.yml); this
module reads those issues with the GitHub API, keeps the queue in data/requests.json and creates a blank page
for every parsable request so the daily assembler can fill it from official sources.

Rules this module must never break: a blank page contains no facts at all — every block is an honest
"not collected" placeholder (never copied from another corridor's demo page) until assemble.py adds sourced
lines; the queue never invents an HS-6 code — a request without one waits for a person.

Run:  python -m pipeline requests --sync           (GITHUB_REPOSITORY + GITHUB_TOKEN from Actions; corridor-requests.yml)
      python -m pipeline requests --apply          (create blank pages for queued requests, no network)
      python -m pipeline requests --parse "Коридор: дроны 880622 из CN в KZ"
"""
from __future__ import annotations

import json
import os
import re
import urllib.request
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
REQUESTS_FILE = ROOT / "data" / "requests.json"
CORRIDORS_FILE = ROOT / "data" / "corridors.yaml"
COUNTRIES_FILE = ROOT / "data" / "countries.json"
HS6_FILE = ROOT / "data" / "hs6.json"
PAGES_DIR = ROOT / "web" / "data" / "pages"
LABEL = "corridor-request"
BLANK = "blank page created by pipeline/requests.py"

NOT_FOUND = {"status": "none", "source": "источник не перечитан", "label": "не собрано — статус not_found"}
BROKER = {"status": "note", "source": "подтвердите у брокера", "label": "страница работает на уровне группы HS-6"}
NOT_LOADED = {"status": "none", "source": "таблица rates", "label": "ставка не загружена"}


def _countries() -> dict[str, dict]:
    rows = json.loads(COUNTRIES_FILE.read_text(encoding="utf8"))
    return {r["code"]: r for r in rows}


def _hs6() -> dict[str, dict]:
    try:
        return {r["code"]: r for r in json.loads(HS6_FILE.read_text(encoding="utf8"))}
    except (OSError, json.JSONDecodeError):
        return {}


def country_code(text: str, countries: dict[str, dict] | None = None) -> str | None:
    """'CN' / 'Китай' / 'China' / 'из Китая' -> 'CN'; None when not recognised (never guessed)."""
    countries = countries or _countries()
    t = text.strip().strip(".,;:()").lower()
    if re.fullmatch(r"[a-z]{2}", t) and t.upper() in countries:
        return t.upper()
    bare = re.sub(r"^(из|с|в|на|from|to|in)\s+", "", t)
    for code, c in countries.items():
        forms = {c["name"], c["name_en"], c["from"], c["to"], c.get("loc", "")}
        names = {f.lower() for f in forms} | {re.sub(r"^(из|с|в|на)\s+", "", f.lower()) for f in forms}
        if t in names or bare in names:
            return code
    return None


def _field(body: str, label: str) -> str:
    """Issue-form bodies render as '### Label\\n\\nvalue'; returns the value or ''."""
    m = re.search(rf"^###\s*{re.escape(label)}\s*\n+(.*?)(?=\n###|\Z)", body or "", re.S | re.M)
    return m.group(1).strip() if m else ""


def parse_issue(title: str, body: str = "", countries: dict[str, dict] | None = None) -> dict | None:
    """Extracts {product, hs6, from, to, mode} from an issue; hs6 or countries may be missing (None)."""
    countries = countries or _countries()
    product = _field(body, "Товар") or re.sub(r"^\s*Коридор\s*:\s*", "", title, flags=re.I)
    fr = country_code(_field(body, "Откуда (страна или код ISO)") or _field(body, "Откуда"), countries)
    to = country_code(_field(body, "Куда (страна или код ISO)") or _field(body, "Куда"), countries)
    if fr is None or to is None:
        m = re.search(r"\b(?:из|from)\s+(\S+(?:\s+\S+)?)\s+(?:в|на|to)\s+(\S+(?:\s+\S+)?)", f"{title} {product}", re.I)
        if m:
            fr = fr or country_code(m.group(1), countries) or country_code(m.group(1).split()[0], countries)
            to = to or country_code(m.group(2), countries) or country_code(m.group(2).split()[0], countries)
    hs = re.search(r"\b(\d{4})[.\s]?(\d{2})\b", f"{product} {title}")
    hs6 = (hs.group(1) + hs.group(2)) if hs else None
    mode_text = _field(body, "Режим").lower()
    mode = ["b2b", "parcel"] if "оба" in mode_text else ["parcel"] if "посыл" in mode_text else ["b2b"]
    name = re.sub(r"[,;]?\s*\b\d{4}[.\s]?\d{2}\b", "", product)
    name = re.sub(r"\s+\b(?:из|from)\s+\S+(?:\s+\S+)?\s+(?:в|на|to)\s+\S+(?:\s+\S+)?\s*$", "", name, flags=re.I).strip(" ,;") or product
    if not (product or hs6):
        return None
    return {"product": name, "hs6": hs6, "from": fr, "to": to, "modes": mode}


def _section(sid: str, number: int | None, title: str, lead: str, text: str) -> dict:
    s = {"id": sid, "title": title, "lead": lead, "facts": [{"text": text, "stamp": NOT_FOUND}]}
    if number is not None:
        s["number"] = number
    return s


def blank_page(fr: str, to: str, hs6: str, product_name: str | None = None, modes: list[str] | None = None) -> dict:
    """A PageContent with only honest placeholders. assemble.py then adds sourced lines and the index rating."""
    countries = _countries()
    cf, ct = countries[fr], countries[to]
    hs = _hs6().get(hs6, {})
    name = product_name or hs.get("ru") or hs.get("en") or f"товары группы {hs6}"
    label = f"HS {hs6[:4]}.{hs6[4:]}"
    corridor_id = f"{fr.lower()}-{to.lower()}"
    modes = modes or ["b2b"]
    ref = lambda c: {"code": c["code"], "name": c["name"], "from": c["from"], "to": c["to"], "loc": c.get("loc", "")}  # noqa: E731
    page = {
        "corridor": {"id": corridor_id, "from": ref(cf), "to": ref(ct), "modes": modes, "languages": ["ru"]},
        "product": {"hs6": hs6, "name": name, "hsLabel": label},
        "lang": "ru",
        "isDemo": False,
        "_blank": BLANK,
        "status": {"sourcesTotal": 0, "sourcesMissing": 0, "lastChecked": "", "text": f"Страница создана по запросу для группы {label}: конвейер ещё не перечитывал источники. Каждая строка появится только с цитатой из официального источника. Это не юридическая консультация."},
        "summary": {"id": "s0", "title": "Коротко", "facts": [
            {"key": "Пошлина при ввозе", "text": f"Ставка MFN {ct['loc'] if ct.get('loc') else ct['name']} для группы {label} ещё не загружена в таблицу ставок.", "stamp": NOT_LOADED},
            {"key": "Код товара", "text": f"Страница работает на уровне группы {label}; национальную подстроку подтвердите у брокера или через предварительное решение таможни.", "stamp": BROKER},
            {"key": "Соглашение", "text": "Торговые соглашения между странами не проверены.", "stamp": NOT_FOUND},
            {"key": "Санкции", "text": "Санкционные режимы для пары не проверены.", "stamp": NOT_FOUND},
        ]},
        "rating": {"id": "sv", "title": "Выгодно и что мешает", "lead": "Оценка коридора складывается из пяти частей, каждую можно проверить. Запрет или санкции обнулили бы её независимо от остальных.", "total": 0, "of": 0, "verdict": "не рассчитано", "verdictStatus": "warn", "explanation": "", "parts": []},
        "verdict": {"prosTitle": "Выгодно", "consTitle": "Мешает", "pros": [], "cons": []},
        "compare": {"id": "sw", "title": f"Куда ещё везти этот товар {cf['from']}", "lead": "Те же части для других рынков, отсортированы по оценке. Спрос и логистика в ней — ориентир, а не проверенный факт.", "rows": []},
        "regime": _section("s1", 1, "Режим торговли между странами", "Соглашения, санкции и торговые меры между странами пары.", "Режим торговли для этой пары не собран."),
        "export": _section("s2", 2, f"Вывоз {cf['from']}", "Разрешения, декларирование, экспортные пошлины и поддержка на стороне вывоза.", "Правила вывоза для этой группы не собраны."),
        "exportControl": _section("s2b", None, "Экспортный контроль и двойное назначение", "Лицензии на вывоз и списки товаров двойного назначения обеих стран показываются как есть. Принадлежность товара к спискам — по национальному коду у брокера.", "Контрольные списки для этой группы не проверены."),
        "import": _section("s3", 3, f"Ввоз {ct['to']}", "Пошлины, налоги, разрешения, маркировка и запреты на стороне ввоза.", "Правила ввоза для этой группы не собраны."),
        "cost": {"id": "s4", "number": 4, "title": "Сколько заплатить", "lead": "Расчёт появится, когда ставки для группы будут в таблице ставок.", "currency": "", "inputs": [], "lines": [], "totalLabel": "Итого", "note": "Ставки не загружены — калькулятор пуст."},
        "logistics": _section("s5", 5, "Как везти", "Маршруты, сроки и стоимость — всегда ориентир.", "Логистика для этого коридора не собрана."),
        "documents": {"id": "s6", "number": 6, "title": "Документы", "lead": "Перечни появятся из официальных источников.", "groups": []},
        "sources": {"id": "s7", "number": 7, "title": "Источники", "lead": "Официальные страницы, из которых собраны строки выше, с датой проверки.", "rows": []},
        "rail": {"disclaimer": "Не юридическая консультация. Код товара и ставки подтвердите у таможенного брокера.", "reverseLabel": None, "followSample": None},
    }
    return page


def load_queue(path: Path = REQUESTS_FILE) -> list[dict]:
    try:
        return json.loads(path.read_text(encoding="utf8"))
    except (OSError, json.JSONDecodeError):
        return []


def save_queue(items: list[dict], path: Path = REQUESTS_FILE) -> None:
    path.write_text(json.dumps(items, ensure_ascii=False, indent=1) + "\n", encoding="utf8")


def github_issues(repo: str, token: str | None) -> list[dict]:
    """Open issues with the corridor-request label (GitHub REST API, queue infrastructure — not a content source)."""
    url = f"https://api.github.com/repos/{repo}/issues?state=open&labels={LABEL}&per_page=100"
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "trade-rules-pipeline", **({"Authorization": f"Bearer {token}"} if token else {})})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return [i for i in json.loads(resp.read().decode("utf8")) if "pull_request" not in i]


def sync(repo: str | None = None, token: str | None = None, path: Path = REQUESTS_FILE) -> list[dict]:
    repo = repo or os.environ.get("GITHUB_REPOSITORY", "")
    token = token or os.environ.get("GITHUB_TOKEN")
    if not repo:
        raise SystemExit("GITHUB_REPOSITORY is not set")
    queue = {str(i["issue"]): i for i in load_queue(path)}
    for issue in github_issues(repo, token):
        parsed = parse_issue(issue.get("title", ""), issue.get("body") or "")
        key = str(issue["number"])
        entry = queue.get(key, {"issue": issue["number"], "url": issue.get("html_url"), "created": issue.get("created_at", "")[:10], "status": "queued"})
        if parsed:
            entry.update(parsed)
        else:
            entry["status"] = "needs_person"
        queue[key] = entry
    items = sorted(queue.values(), key=lambda i: i["issue"])
    save_queue(items, path)
    print(f"requests: {len(items)} in queue -> {path}")
    return items


def apply(path: Path = REQUESTS_FILE, pages_dir: Path = PAGES_DIR) -> int:
    """Creates a blank page for every queued request with a known pair and HS-6; marks the rest for a person."""
    items = load_queue(path)
    created = 0
    for item in items:
        if item.get("status") == "page_created":
            continue
        if not (item.get("from") and item.get("to") and item.get("hs6")):
            item["status"] = "needs_person"
            item["reason"] = "страна или код HS-6 не распознаны — уточнить в issue"
            continue
        out = pages_dir / f"{item['from'].lower()}-{item['to'].lower()}-{item['hs6']}-ru.json"
        if not out.exists():
            out.write_text(json.dumps(blank_page(item["from"], item["to"], item["hs6"], item.get("product"), item.get("modes")), ensure_ascii=False, indent=2) + "\n", encoding="utf8")
            created += 1
        item["status"] = "page_created"
        item["page"] = f"/corridor/{item['from'].lower()}-{item['to'].lower()}/{item['hs6']}"
        item["page_created"] = date.today().isoformat()
    save_queue(items, path)
    print(f"requests: {created} blank page(s) created")
    return created


def main(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="pipeline requests")
    parser.add_argument("--sync", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--parse", help="parse one issue title (diagnostics)")
    args, _ = parser.parse_known_args(argv)
    if args.parse:
        print(json.dumps(parse_issue(args.parse), ensure_ascii=False))
        return 0
    if args.sync:
        sync()
    if args.apply:
        apply()
    if not (args.sync or args.apply):
        parser.error("use --sync and/or --apply")
    return 0
