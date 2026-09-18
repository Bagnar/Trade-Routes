"""Generates mockups/corridor-china-canada-v2.html (design v2: answer cards + tabs) from the real assembled page
web/data/pages/cn-ca-610910-ru.json. Run: python scripts/mockup_from_page.py"""
import html, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
page = json.loads((ROOT / "web/data/pages/cn-ca-610910-ru.json").read_text(encoding="utf8"))
E = html.escape

def mode_text(t):
    return t if isinstance(t, str) else (t.get("b2b") or t.get("parcel") or "")

GROUPS = [
    ("Запреты и ограничения", r"запрещ|запрет|ограничен|санкц|принудительн|эмбарго|не допуск"),
    ("Пошлины и налоги", r"пошлин|налог|тариф|gst|hst|ндс|ставк|преференц|mfn|сбор"),
    ("Разрешения, лицензии, сертификаты", r"лиценз|разреш|сертифик|регистрац|carm|учёт|учет|аккредит"),
    ("Маркировка и требования к товару", r"маркиров|этикет|безопасност|стандарт|требован"),
    ("Документы и декларирование", r"деклар|документ|инвойс|коносамент|происхожден|заявлен"),
    ("Господдержка и возврат налогов", r"субсид|поддержк|возврат|страхов|кредит|льгот"),
]

def group_facts(facts):
    buckets = {name: [] for name, _ in GROUPS}
    buckets["Общие правила"] = []
    for f in facts:
        t = mode_text(f["text"]).lower()
        for name, pat in GROUPS:
            if re.search(pat, t):
                buckets[name].append(f); break
        else:
            buckets["Общие правила"].append(f)
    return [(k, v) for k, v in buckets.items() if v]

DOT = {"ok": "ok", "warn": "warn", "ban": "ban", "none": "none", "note": "note"}

def fact_html(f, compact=False):
    st = f["stamp"]; status = st.get("status", "none")
    ban = f.get("ban") or status == "ban"
    text = E(mode_text(f["text"]))
    src = E(st.get("source", ""))
    label = E(st.get("label", ""))
    url = st.get("url")
    quote = f.get("quote")
    meta = f'<span class="dot {DOT.get(status,"none")}"></span>'
    meta += f'<a href="{E(url)}" target="_blank" rel="noopener">{src}</a>' if url else f'<span>{src}</span>'
    meta += f'<span class="sep">·</span><span>{label}</span>'
    q = ""
    if quote:
        q = f'<details class="q"><summary>цитата</summary><blockquote lang="{E(f.get("quoteLang","") or "en")}">{E(quote)}</blockquote></details>'
    cls = "fact" + (" ban" if ban else "") + (" warn" if status == "warn" else "") + (" none" if status == "none" else "")
    return f'<li class="{cls}"><p>{text}</p><div class="meta">{meta}{q}</div></li>'

def section_html(sec):
    out = []
    if sec.get("lead"):
        out.append(f'<p class="lead">{E(sec["lead"])}</p>')
    groups = group_facts(sec["facts"])
    for name, facts in groups:
        out.append(f'<h3>{E(name)} <span class="n">{len(facts)}</span></h3><ul class="facts">' + "".join(fact_html(f) for f in facts) + "</ul>")
    for g in sec.get("groups", []) or []:
        out.append(f'<h3>{E(g.get("title",""))} <span class="n">{len(g["facts"])}</span></h3><ul class="facts">' + "".join(fact_html(f) for f in g["facts"]) + "</ul>")
    return "".join(out)

# ---------- answer cards
summary = {f.get("key"): f for f in page["summary"]["facts"]}
def stext(key):
    f = summary.get(key); return mode_text(f["text"]) if f else ""
def stamp_line(key):
    f = summary.get(key)
    if not f: return ""
    st = f["stamp"]
    link = f'<a href="{E(st["url"])}" target="_blank" rel="noopener">{E(st["source"])}</a>' if st.get("url") else E(st.get("source",""))
    return f'<div class="meta"><span class="dot {DOT.get(st.get("status","none"),"none")}"></span>{link}<span class="sep">·</span><span>{E(st.get("label",""))}</span></div>'

duty_txt = stext("Пошлина при ввозе")
m = re.search(r"(≈|около )?(\d+(?:[.,]\d+)?)\s*%", duty_txt)
duty_num = (m.group(1) or "") + m.group(2) + "%" if m else "—"
year = re.search(r"за (\d{4}) год", duty_txt)
duty_sub = f"MFN, простая средняя по группе HS 6109.10, WITS/TRAINS {year.group(1) if year else ''}".strip()
tax_txt = stext("Налог на границе")

r = page["rating"]
verdict_cls = r["verdictStatus"]
parts_html = "".join(
    f'<li><span>{E(p["name"])}</span><b>{"—" if p["score"] is None else str(p["score"])+" / 5"}</b></li>' for p in r["parts"]
)
best = next((row for row in page["compare"]["rows"] if not row.get("here")), None)

def card(title, body, cls=""):
    return f'<article class="card {cls}"><h2>{E(title)}</h2>{body}</article>'

restr = summary.get("Ограничения"); sanc = summary.get("Санкции")
restr_body = ""
if restr:
    restr_body += f'<p class="banline"><span class="dot ban"></span>{E(mode_text(restr["text"]))}</p>' + stamp_line("Ограничения")
if sanc:
    restr_body += f'<p><span class="dot {DOT.get(sanc["stamp"]["status"],"ok")}"></span>{E(mode_text(sanc["text"]))}</p>' + stamp_line("Санкции")

cards = "".join([
    card("Пошлина при ввозе", f'<p class="big">{E(duty_num)}</p><p class="sub">{E(duty_sub)}</p><p class="small">{E(tax_txt)}</p>' + stamp_line("Пошлина при ввозе"), "duty"),
    card("Запреты и санкции", restr_body, "restr"),
    card("Соглашения", f'<p>{E(stext("Соглашение"))}</p>' + stamp_line("Соглашение"), "agr"),
    card("Выгодно ли", f'<p class="big"><span class="score {verdict_cls}">{r["total"]} <small>из {r["of"]}</small></span></p><p class="sub verdict {verdict_cls}">{E(r["verdict"])}</p><ul class="parts">{parts_html}</ul>' + (f'<p class="small">Лучше по оценке: {E(best["to"])} — {E(best["score"]["text"])}. <a href="#tab-compare" data-tab="compare">Сравнить рынки</a></p>' if best else "") + '<p class="small"><a href="#tab-rating" data-tab="rating">Как считали</a></p>', "score"),
])

more = []
for key in ("Лицензия на экспорт", "Спрос", "Код товара"):
    f = summary.get(key)
    if f:
        more.append(f'<div class="kv"><dt>{E(key)}</dt><dd>{E(mode_text(f["text"]))}{stamp_line(key)}</dd></div>')
more_html = '<dl class="more">' + "".join(more) + "</dl>" if more else ""

# ---------- rating tab
def pc(items, cls):
    return "".join(f'<li class="{cls} {E(i["kind"])}">{E(mode_text(i["text"]))}</li>' for i in items)
rating_tab = f'''
<p class="lead">{E(r["lead"])}</p>
<div class="rbox">
  <div class="rhead"><span class="score {verdict_cls} big2">{r["total"]} <small>из {r["of"]}</small></span><span class="verdict {verdict_cls}">{E(r["verdict"])}</span></div>
  <ul class="bars">{"".join(f'<li><span class="pname">{E(p["name"])}</span><span class="bar"><i style="width:{0 if p["score"] is None else p["score"]*20}%"></i></span><span class="pscore">{"нет основания" if p["score"] is None else str(p["score"])+" из 5"}</span><span class="pnote">{E(p["basis"])}</span></li>' for p in r["parts"])}</ul>
  <p class="small">{E(r["explanation"])}</p>
</div>
<div class="proscons">
  <div><h3>{E(page["verdict"]["prosTitle"])}</h3><ul class="vlist">{pc(page["verdict"]["pros"],"pro")}</ul></div>
  <div><h3>{E(page["verdict"]["consTitle"])}</h3><ul class="vlist">{pc(page["verdict"]["cons"],"con")}</ul></div>
</div>'''

# ---------- compare tab
cmp_rows = "".join(
    f'<tr class="{"here" if row.get("here") else ""}"><td>{E(row["to"])}</td><td>{E(row["duty"])}</td><td>{E(row["agreement"])}</td><td>{E(row["sanctions"])}</td><td>{E(row["support"])}</td><td><span class="pill {E(row["score"]["status"])}">{E(row["score"]["text"])}</span></td></tr>'
    for row in page["compare"]["rows"])
compare_tab = f'<p class="lead">{E(page["compare"]["lead"])}</p><div class="tbl"><table><thead><tr><th>Куда</th><th>Пошлина</th><th>Соглашение</th><th>Санкции</th><th>Поддержка</th><th>Оценка</th></tr></thead><tbody>{cmp_rows}</tbody></table></div>'

# ---------- cost tab (static)
c = page["cost"]
inputs_html = "".join(f'<label><span>{E(i["label"])}</span><input value="{E(str(i["value"]))}" readonly></label>' for i in c["inputs"] if i["kind"] != "checkbox")
cost_tab = f'<p class="lead">{E(c["lead"])}</p><div class="calc"><div class="inputs">{inputs_html}</div><p class="small">{E(c["note"])}</p></div>'

# ---------- documents tab
docs = page["documents"]
docs_tab = f'<p class="lead">{E(docs["lead"])}</p>' + "".join(
    f'<h3>{E(g["title"])}</h3><ul class="check">' + "".join(f'<li><span class="box"></span>{E(i)}</li>' for i in g["items"]) + "</ul>" for g in docs["groups"])

# ---------- sources tab
src_rows = "".join(f'<tr><td>{E(s["source"])}</td><td>{E(s["confirms"])}</td><td>{E(s["checked"])}</td><td><span class="pill {E(s["status"]["kind"])}">{E(s["status"]["text"])}</span></td></tr>' for s in page["sources"]["rows"])
sources_tab = f'<p class="lead">{E(page["sources"]["lead"])}</p><div class="tbl"><table><thead><tr><th>Источник</th><th>Что подтверждает</th><th>Проверено</th><th>Статус</th></tr></thead><tbody>{src_rows}</tbody></table></div>'

tabs = [
    ("rating", "Оценка", rating_tab),
    ("compare", "Куда ещё везти", compare_tab),
    ("regime", "Режим торговли", section_html(page["regime"])),
    ("export", "Вывоз из Китая", section_html(page["export"])),
    ("control", "Экспортный контроль", section_html(page["exportControl"])),
    ("import", "Ввоз в Канаду", section_html(page["import"])),
    ("cost", "Сколько платить", cost_tab),
    ("docs", "Документы", docs_tab),
    ("logistics", "Как везти", section_html(page["logistics"])),
    ("sources", "Источники", sources_tab),
]
counts = {"regime": len(page["regime"]["facts"]), "export": len(page["export"]["facts"]) + sum(len(g["facts"]) for g in page["export"].get("groups", [])), "control": len(page["exportControl"]["facts"]), "import": len(page["import"]["facts"]), "logistics": len(page["logistics"]["facts"]), "sources": len(page["sources"]["rows"]), "compare": len(page["compare"]["rows"])}
tab_buttons = "".join(f'<button role="tab" id="t-{k}" aria-controls="tab-{k}" aria-selected="{"true" if i==0 else "false"}" data-tab="{k}">{E(t)}{f"<span class=n>{counts[k]}</span>" if k in counts else ""}</button>' for i, (k, t, _) in enumerate(tabs))
tab_panels = "".join(f'<section role="tabpanel" id="tab-{k}" aria-labelledby="t-{k}" {"" if i==0 else "hidden"}><h2 class="ph">{E(t)}</h2>{body}</section>' for i, (k, t, body) in enumerate(tabs))

st = page["status"]
first_sentence = re.sub(r"\.\s.*$", "", st["text"])
status_line = E(first_sentence) + ". Не юридическая консультация: код товара и ставки подтвердите у таможенного брокера."

doc = f'''<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Футболки из Китая в Канаду — страница коридора (макет v2)</title>
<style>
  :root{{
    --ink:#1B2A3A; --ink-soft:#4B5D70; --muted:#7A8794;
    --paper:#FFFFFF; --page:#F5F6F8; --rule:#DDE2E7; --rule-soft:#ECEFF2;
    --ok:#1F6F4A; --ok-bg:#EAF4EE; --warn:#8F6208; --warn-bg:#FFF3D6; --ban:#A62B26; --ban-bg:#FBEAE8;
    --none:#5B6470; --note:#5B6470; --accent:#1C3A5B;
    --sans: -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  }}
  *{{box-sizing:border-box}}
  html{{background:var(--page)}}
  body{{margin:0; color:var(--ink); font-family:var(--sans); font-size:16px; line-height:1.5; -webkit-font-smoothing:antialiased}}
  a{{color:var(--accent)}}
  .wrap{{max-width:1040px; margin:0 auto; padding:0 24px; min-width:0}}
  body{{overflow-x:hidden}}
  .narrow{{max-width:760px}}

  /* header */
  .top{{background:var(--paper); border-bottom:1px solid var(--rule)}}
  .top .wrap{{display:flex; align-items:center; gap:20px; height:52px}}
  .brand{{display:flex; align-items:center; gap:8px; font-weight:600; text-decoration:none; color:var(--ink)}}
  .brand svg{{width:22px; height:22px}}
  .brand .tag{{font-weight:400; color:var(--muted); font-size:13px}}
  .langs{{margin-left:auto; display:flex; gap:4px}}
  .langs button{{border:1px solid var(--rule); background:var(--paper); border-radius:6px; padding:4px 9px; font-size:13px; cursor:pointer; color:var(--ink)}}
  .langs button[aria-current="true"]{{background:var(--ink); color:#fff; border-color:var(--ink)}}

  /* query */
  .query-band{{background:var(--paper); border-bottom:1px solid var(--rule)}}
  .query{{padding:18px 0 16px; font-size:19px; line-height:1.7}}
  .query select{{max-width:100%; text-overflow:ellipsis; font:inherit; font-size:19px; color:var(--ink); border:0; border-bottom:2px solid var(--ink); background:transparent; padding:0 24px 0 4px; appearance:none; -webkit-appearance:none; cursor:pointer;
    background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8'%3E%3Cpath d='M1 1l5 5 5-5' fill='none' stroke='%231B2A3A' stroke-width='1.8'/%3E%3C/svg%3E"); background-repeat:no-repeat; background-position:right 6px center}}
  .mode{{display:inline-flex; border:1.5px solid var(--ink); border-radius:6px; overflow:hidden; vertical-align:middle; margin-left:6px; font-size:14px}}
  .mode button{{border:0; background:#fff; padding:5px 11px; cursor:pointer; color:var(--ink); font:inherit}}
  .mode button[aria-pressed="true"]{{background:var(--ink); color:#fff}}
  .status{{font-size:13px; color:var(--ink-soft); padding:10px 0 12px; border-top:1px solid var(--rule-soft)}}

  /* answer */
  .answer{{padding:28px 0 8px}}
  .cards{{display:grid; grid-template-columns:repeat(4, minmax(0,1fr)); gap:14px}}
  .card{{background:var(--paper); border:1px solid var(--rule); border-radius:10px; padding:16px 18px 14px; min-width:0}}
  .card h2{{margin:0 0 8px; font-size:13px; font-weight:600; letter-spacing:.02em; text-transform:uppercase; color:var(--muted)}}
  .card p{{margin:0 0 6px}}
  .card .big{{font-size:34px; font-weight:600; line-height:1.1; letter-spacing:-.01em}}
  .card .sub{{font-size:14px; color:var(--ink-soft)}}
  .card .small, .rbox .small, .calc .small{{font-size:13px; color:var(--ink-soft); margin-top:8px}}
  .card.restr{{border-left:4px solid var(--ban)}}
  .card .banline{{color:var(--ban)}}
  .score.ok{{color:var(--ok)}} .score.mid{{color:var(--warn)}} .score.warn{{color:var(--ban)}}
  .score small{{font-size:15px; font-weight:400; color:var(--muted)}}
  .verdict.ok{{color:var(--ok)}} .verdict.mid{{color:var(--warn)}} .verdict.warn{{color:var(--ban)}}
  .parts{{list-style:none; margin:8px 0 0; padding:0; font-size:13px; color:var(--ink-soft)}}
  .parts li{{display:flex; justify-content:space-between; gap:8px; padding:2px 0; border-top:1px dashed var(--rule-soft)}}
  .parts b{{font-weight:600; color:var(--ink)}}
  .meta{{font-size:12.5px; color:var(--muted); margin-top:6px; display:flex; flex-wrap:wrap; align-items:center; gap:6px}}
  .meta a{{color:var(--muted)}}
  .sep{{color:var(--rule)}}
  .dot{{display:inline-block; width:8px; height:8px; border-radius:50%; background:var(--none); flex:none}}
  .dot.ok{{background:var(--ok)}} .dot.warn{{background:var(--warn)}} .dot.ban{{background:var(--ban)}} .dot.note{{background:#9AA5B1}} .dot.none{{background:#C7CED6}}
  p .dot{{margin-right:7px; vertical-align:middle}}
  .more{{display:grid; grid-template-columns:repeat(3, minmax(0,1fr)); gap:14px; margin:14px 0 0; font-size:14px}}
  .more .kv{{background:var(--paper); border:1px solid var(--rule-soft); border-radius:8px; padding:10px 14px}}
  .more dt{{font-size:12px; text-transform:uppercase; letter-spacing:.02em; color:var(--muted); margin-bottom:4px}}
  .more dd{{margin:0; color:var(--ink)}}

  /* tabs */
  .tabs{{position:sticky; top:0; z-index:5; background:var(--page); border-bottom:1px solid var(--rule); margin-top:22px}}
  .tabs .wrap{{display:flex; flex-wrap:wrap; gap:0 2px}}
  .tabs button{{flex:none; border:0; background:transparent; padding:11px 10px 9px; font:inherit; font-size:13.5px; color:var(--ink-soft); cursor:pointer; border-bottom:2px solid transparent; margin-bottom:-1px; white-space:nowrap}}
  .tabs button[aria-selected="true"]{{color:var(--ink); border-bottom-color:var(--ink); font-weight:600}}
  .n{{display:inline-block; margin-left:6px; font-size:11.5px; font-weight:500; color:var(--muted); background:var(--rule-soft); border-radius:10px; padding:1px 7px; vertical-align:1px}}
  h3 .n{{font-size:12px}}
  .panels{{padding:26px 0 60px}}
  section[role="tabpanel"]{{max-width:760px}}
  .ph{{font-size:22px; font-weight:600; margin:0 0 6px; letter-spacing:-.01em}}
  .lead{{color:var(--ink-soft); margin:0 0 18px; font-size:15px}}
  h3{{font-size:15px; font-weight:600; margin:24px 0 8px; padding-bottom:6px; border-bottom:1px solid var(--rule)}}

  /* facts */
  .facts{{list-style:none; margin:0; padding:0}}
  .fact{{padding:12px 0 12px 16px; border-bottom:1px solid var(--rule-soft); border-left:3px solid transparent}}
  .fact p{{margin:0}}
  .fact.ban{{border-left-color:var(--ban)}} .fact.ban p{{color:var(--ban)}}
  .fact.warn{{border-left-color:var(--warn)}}
  .fact.none p{{color:var(--muted)}}
  details.q{{display:inline}} details.q summary{{cursor:pointer; color:var(--muted); text-decoration:underline dotted; list-style:none}} details.q summary::-webkit-details-marker{{display:none}}
  details.q[open]{{display:block; width:100%}}
  details.q blockquote{{margin:8px 0 0; padding:8px 12px; border-left:2px solid var(--rule); color:var(--ink-soft); font-size:13.5px; font-style:italic}}

  /* rating tab */
  .rbox{{background:var(--paper); border:1px solid var(--rule); border-radius:10px; padding:18px 20px}}
  .rhead{{display:flex; align-items:baseline; gap:16px; margin-bottom:12px}}
  .big2{{font-size:40px; font-weight:600; line-height:1}}
  .bars{{list-style:none; margin:0; padding:0}}
  .bars li{{display:grid; grid-template-columns:150px 1fr 110px; gap:8px 12px; align-items:center; padding:8px 0; border-top:1px solid var(--rule-soft); font-size:14px}}
  .bars .pname{{font-weight:600}}
  .bars .bar{{height:6px; background:var(--rule-soft); border-radius:3px; overflow:hidden}} .bars .bar i{{display:block; height:100%; background:var(--accent)}}
  .bars .pscore{{text-align:right; color:var(--ink-soft); white-space:nowrap}}
  .bars .pnote{{grid-column:1 / -1; font-size:13px; color:var(--muted); margin-top:-4px}}
  .proscons{{display:grid; grid-template-columns:1fr 1fr; gap:20px; margin-top:22px}}
  .proscons h3{{margin-top:0; border:0}}
  .vlist{{list-style:none; margin:0; padding:0; font-size:14.5px}}
  .vlist li{{padding:8px 12px; margin-bottom:8px; border-radius:6px; border-left:3px solid}}
  .vlist .pro, .vlist .pro-check{{border-color:var(--ok); background:var(--ok-bg)}}
  .vlist .con{{border-color:var(--warn); background:var(--warn-bg)}}
  .vlist .con-ban{{border-color:var(--ban); background:var(--ban-bg)}}

  /* tables */
  .tbl{{overflow-x:auto}}
  table{{width:100%; border-collapse:collapse; font-size:14px}}
  th{{text-align:left; font-weight:600; color:var(--muted); font-size:12px; text-transform:uppercase; letter-spacing:.02em; padding:8px 10px 8px 0; border-bottom:1px solid var(--rule)}}
  td{{padding:9px 10px 9px 0; border-bottom:1px solid var(--rule-soft); vertical-align:top}}
  tr.here td{{background:#F9FAFB; font-weight:600}}
  .pill{{display:inline-block; font-size:12.5px; padding:2px 8px; border-radius:10px; border:1px solid; white-space:nowrap}}
  .pill.ok{{color:var(--ok); border-color:#B9DCC7; background:var(--ok-bg)}} .pill.mid{{color:var(--warn); border-color:#E9D39B; background:var(--warn-bg)}} .pill.warn{{color:var(--ban); border-color:#EBB8B4; background:var(--ban-bg)}} .pill.none{{color:var(--none); border-color:var(--rule); background:var(--rule-soft)}}

  /* docs, calc */
  .check{{list-style:none; margin:0; padding:0}} .check li{{display:flex; gap:10px; padding:7px 0; border-bottom:1px solid var(--rule-soft); font-size:15px}}
  .check .box{{width:16px; height:16px; border:1.5px solid var(--rule); border-radius:4px; flex:none; margin-top:3px}}
  .calc{{background:var(--paper); border:1px solid var(--rule); border-radius:10px; padding:16px 18px}}
  .inputs{{display:grid; grid-template-columns:1fr 1fr; gap:12px}} .inputs label{{display:flex; flex-direction:column; font-size:13px; color:var(--muted); gap:4px}}
  .inputs input{{font:inherit; font-size:15px; padding:7px 9px; border:1px solid var(--rule); border-radius:6px; color:var(--ink)}}

  /* footer strip */
  .foot{{border-top:1px solid var(--rule); background:var(--paper)}}
  .foot .wrap{{display:flex; flex-wrap:wrap; gap:8px 24px; padding:14px 24px; font-size:13px; color:var(--ink-soft)}}
  .foot a{{color:var(--ink-soft)}}

  @media (max-width:900px){{ .cards{{grid-template-columns:1fr 1fr}} .more{{grid-template-columns:1fr}} }}
  @media (max-width:560px){{ .query select.product{{display:block; width:100%; margin:2px 0 4px}} .cards{{grid-template-columns:1fr}} .proscons{{grid-template-columns:1fr}} .bars li{{grid-template-columns:1fr 80px}} .bars .bar{{grid-column:1 / -1}} .query{{font-size:17px}} .query select{{font-size:17px}} }}
</style>
</head>
<body>
<header class="top"><div class="wrap">
  <a class="brand" href="#"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="5" cy="17" r="2"/><circle cx="19" cy="7" r="2"/><path d="M7 16c3-1 5-4 6-7" stroke-linecap="round"/></svg>TradeRoutes <span class="tag">все коридоры</span></a>
  <div class="langs"><button aria-current="true">RU</button><button>EN</button><button>中文</button></div>
</div></header>

<div class="query-band"><div class="wrap">
  <div class="query">Везу <select class="product"><option>футболки хлопковые трикотажные, HS 6109.10</option><option>другие группы…</option></select> <select><option>из Китая</option><option>другие…</option></select> <select><option>в Канаду</option><option>другие…</option></select> как <span class="mode"><button aria-pressed="true">коммерческую партию</button><button aria-pressed="false">посылки покупателям</button></span></div>
  <div class="status">{status_line}</div>
</div></div>

<main>
  <div class="wrap answer">
    <div class="cards">{cards}</div>
    {more_html}
  </div>

  <nav class="tabs" role="tablist" aria-label="Разделы страницы"><div class="wrap">{tab_buttons}</div></nav>
  <div class="wrap panels">{tab_panels}</div>
</main>

<footer class="foot"><div class="wrap">
  <a href="#">Где купить футболки в Китае</a>
  <a href="#">Обратное направление: из Канады в Китай</a>
  <a href="#">Следить за коридором</a>
  <a href="#">Сообщить о неточности</a>
  <span>Собрано автоматически из официальных источников. Не консультация.</span>
</div></footer>

<script>
  const buttons = document.querySelectorAll('[data-tab]');
  function show(id, scroll) {{
    document.querySelectorAll('[role=tab]').forEach(b => b.setAttribute('aria-selected', b.dataset.tab === id ? 'true' : 'false'));
    document.querySelectorAll('[role=tabpanel]').forEach(p => p.hidden = p.id !== 'tab-' + id);
    if (scroll) document.querySelector('.tabs').scrollIntoView({{behavior:'smooth'}});
    history.replaceState(null, '', '#' + id);
  }}
  buttons.forEach(b => b.addEventListener('click', e => {{ e.preventDefault(); show(b.dataset.tab, b.getAttribute('role') !== 'tab'); }}));
  if (location.hash.length > 1 && document.getElementById('tab-' + location.hash.slice(1))) show(location.hash.slice(1), false);
</script>
</body>
</html>
'''
out = ROOT / "mockups/corridor-china-canada-v2.html"
out.write_text(doc, encoding="utf8")
print(out, len(doc))
