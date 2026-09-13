/**
 * Corridor assembly in the browser for any pair of countries and any HS-6 group (docs/concept.md, decision 15).
 *
 * A port of the pipeline's rules to TypeScript — pipeline/requests.py (blank page), pipeline/assemble.py
 * (sourced lines, duty and demand summary lines, sources table) and pipeline/index.py (five-part rating and
 * "where else to ship"). Same inputs, same wording, so a page assembled here matches the one the daily
 * assembler would write to web/data/pages for the same pair.
 *
 * Rules this module must never break (CLAUDE.md, "Принципы"):
 *   - a line reaches the page only with its verbatim quote, source URL and snapshot date;
 *   - rates come only from the rates tables (public/data/rates), never from memory;
 *   - a part of the rating without data gets no score and a basis that says so;
 *   - a prohibition needs a source naming the product group; country-wide sanctions are an obstacle, not a ban;
 *   - demand is always "ориентир", never "проверено"; nothing is invented to fill a gap.
 *
 * Pure functions, no fetching: `loadCorridorData` in the /c page fetches the files and passes them in.
 */
import type { CompareRow, CountryRef, Fact, PageContent, RatingPart, ScoreStatus, Section, Stamp } from "./page-content";

/* ---------- input data (shapes written by web/scripts/copy-data.mjs) ---------- */

export interface SourcedFact {
  block: string;
  country: string;
  hs_scope: string[];
  statement: { ru: string; en: string };
  quote: string;
  quote_lang?: string;
  targets?: string[];
  url: string;
  source_id: string;
  fetched_at: string;
}

export interface RatesMeta {
  year: number;
  source: string;
  url: string;
  fetched_at: string;
}

export interface DemandSeries {
  years: Record<string, number>;
  kind: "reported" | "mirror" | "none";
  partners?: number;
  fetched_at?: string;
}

export interface Agreement {
  name: string;
  members: string[];
}

export interface SanctionProgram {
  authority: string;
  domain: string;
  url: string;
  targets: string[];
}

export interface RegistrySummary {
  generated: string;
  countries: Record<string, { name: { ru?: string; en?: string }; sources: number; urls: number; verified: number }>;
  programs: SanctionProgram[];
  rates: Record<string, RatesMeta>;
  demand: string[];
  fetched: Record<string, string>;
  pages: { corridor: string; from: string; to: string; hs6: string }[];
  factsTotal: number;
}

export interface CorridorData {
  registry: RegistrySummary;
  countries: Record<string, CountryRef>;
  /** Product entry from the nomenclature, when the code exists. */
  product: { code: string; en: string; ru: string } | null;
  /** MFN rates of this HS-6's chapter: {ISO2: {hs6: percent}}. */
  rates: Record<string, Record<string, number>>;
  demand: Record<string, { source: string; series: Record<string, DemandSeries> }>;
  /** null = the agreements database is not loaded (never "no agreement", only "not checked"). */
  agreements: { agreements: Agreement[] } | null;
  /** Facts of the exporter, the importer, the country-less ones and all sanctions facts. */
  facts: SourcedFact[];
  today: Date;
}

export const ASSEMBLED = "assembled in the browser (web/lib/assemble-client.ts)";
export const STALE_YEARS = 3;
export const M49: Record<string, string> = {
  CA: "124", CN: "156", RU: "643", IR: "364", TR: "792", US: "840", DE: "276", KZ: "398", UZ: "860", AE: "784", IN: "356",
  VN: "704", BR: "076", EG: "818", JP: "392", KR: "410", GB: "826", AU: "036", MX: "484", ID: "360", SA: "682", ZA: "710",
  AR: "032", PL: "616", FR: "251", IT: "381", ES: "724",
};
const COMTRADE_PAGE = "https://comtradeplus.un.org/TradeFlow?Frequency=A&Flows=M&CommodityCodes={hs6}&Reporters={m49}&Partners=0";
const PART_NAMES = ["Пошлины и налоги", "Препятствия", "Господдержка", "Спрос", "Логистика"];
const SANCTION_TARGET_WORDS: Record<string, string> = { iran: "IR", russia: "RU", belarus: "BY", syria: "SY", "north-korea": "KP", dprk: "KP", cuba: "CU", venezuela: "VE", myanmar: "MM", burma: "MM" };

const NOT_FOUND: Stamp = { status: "none", source: "источник не перечитан", label: "не собрано — статус not_found" };
const BROKER: Stamp = { status: "note", source: "подтвердите у брокера", label: "страница работает на уровне группы HS-6" };
const NOT_LOADED: Stamp = { status: "none", source: "таблица rates", label: "ставка не загружена" };

/* ---------- helpers (pipeline/monitor.py ru_date, pipeline/assemble.py) ---------- */

const MONTHS_RU = ["янв", "фев", "мар", "апр", "мая", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"];

export function ruDate(iso: string): string {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso);
  if (!m) return iso;
  return `${Number(m[3])} ${MONTHS_RU[Number(m[2]) - 1]} ${m[1]}`;
}

export function ruDateOf(d: Date): string {
  return `${d.getDate()} ${MONTHS_RU[d.getMonth()]} ${d.getFullYear()}`;
}

export function scopeMatches(hsScope: string[] | undefined, hs6: string): boolean {
  if (!hsScope || hsScope.length === 0) return true;
  for (const prefix of hsScope) {
    const digits = String(prefix).replace(/\D/g, "");
    if (!digits) continue;
    if (digits.startsWith("98") || digits.startsWith("99")) return true; // Canadian chapters 98/99: apply to all goods
    if (hs6.startsWith(digits.slice(0, 6))) return true;
  }
  return false;
}

export function domainOf(url: string): string {
  const host = url.split("//").pop()!.split("/")[0];
  return host.startsWith("www.") ? host.slice(4) : host;
}

export function fmt(v: number): string {
  // Python's `:g`: up to 6 significant digits, no trailing zeros.
  return String(Number(v.toPrecision(6)));
}

export function usdText(value: number): string {
  if (value >= 1e9) return `${(value / 1e9).toFixed(1)} млрд USD`;
  if (value >= 1e6) return `${Math.round(value / 1e6)} млн USD`;
  if (value >= 1e3) return `${Math.round(value / 1e3)} тыс. USD`;
  return `${Math.round(value)} USD`;
}

function isBanStatement(fact: SourcedFact): boolean {
  const s = fact.statement.ru.toLowerCase();
  return fact.block === "sanctions" && (s.includes("запрещ") || s.includes("запрет"));
}

export function toPageFact(fact: SourcedFact): Fact & { _assembled: string } {
  const ban = isBanStatement(fact);
  return {
    text: fact.statement.ru,
    quote: fact.quote,
    quoteLang: fact.quote_lang ?? "",
    ban,
    stamp: {
      status: ban ? "ban" : "ok",
      source: domainOf(fact.url),
      label: `${ban ? "запрет, " : ""}проверено ${ruDate(fact.fetched_at)}`,
      verifiedAt: fact.fetched_at.slice(0, 10),
      url: fact.url,
    },
    _assembled: ASSEMBLED,
  };
}

export function sanctionTargets(fact: SourcedFact): Set<string> {
  const targets = new Set((fact.targets ?? []).map((t) => String(t).toUpperCase()));
  if (targets.size) return targets;
  const url = fact.url.toLowerCase();
  return new Set(Object.entries(SANCTION_TARGET_WORDS).filter(([w]) => url.includes(w)).map(([, c]) => c));
}

const BLOCK_TO_SECTION: Record<string, "regime" | "export" | "exportControl" | "import" | "logistics"> = {
  regime: "regime", sanctions: "regime", export: "export", export_support: "export", export_control: "exportControl",
  import: "import", cost: "import", documents: "import", logistics: "logistics",
};

/* ---------- rates, demand, agreements readers ---------- */

export interface Rate {
  value: number;
  year: number;
  url: string;
  fetched_at: string;
}

export function getRate(data: CorridorData, country: string, hs6: string): Rate | null {
  const meta = data.registry.rates[country];
  const value = data.rates[country]?.[hs6];
  if (!meta || value === undefined || value === null) return null;
  return { value: Number(value), year: meta.year, url: meta.url, fetched_at: meta.fetched_at };
}

export interface Demand {
  latest_year: number;
  value: number;
  growth_pct: number | null;
  span_years: number;
  kind: string;
  partners: number;
  stale: boolean;
  fetched_at: string;
  url: string;
}

export function getDemand(data: CorridorData, country: string, hs6: string): Demand | null {
  const entry = data.demand[country]?.series?.[hs6];
  if (!entry || !entry.years || Object.keys(entry.years).length === 0) return null;
  const years = Object.entries(entry.years).map(([y, v]) => [Number(y), Number(v)] as const).sort((a, b) => a[0] - b[0]);
  const [latestYear, latest] = years[years.length - 1];
  const [firstYear, first] = years[0];
  const growth = first && latestYear > firstYear ? Math.round((latest / first - 1) * 100) : null;
  const m49 = M49[country] ?? "";
  return {
    latest_year: latestYear, value: latest, growth_pct: growth, span_years: latestYear - firstYear,
    kind: entry.kind ?? "reported", partners: entry.partners ?? 0,
    stale: data.today.getFullYear() - latestYear > STALE_YEARS, fetched_at: entry.fetched_at ?? "",
    url: COMTRADE_PAGE.replace("{hs6}", hs6).replace("{m49}", m49 ? String(Number(m49)) : ""),
  };
}

export function agreementsBetween(a: string, b: string, doc: CorridorData["agreements"]): Agreement[] | null {
  if (!doc) return null;
  return doc.agreements.filter((x) => x.members.includes(a) && x.members.includes(b));
}

/* ---------- index layer (pipeline/index.py) ---------- */

type Part = [number | null, string, string];

function dutyPart(data: CorridorData, to: string, hs6: string): Part {
  const rate = getRate(data, to, hs6);
  if (!rate) return [null, "ставка MFN для этой страны не загружена в таблицу ставок", "ставка не загружена"];
  const v = rate.value;
  const score = v === 0 ? 5 : v <= 5 ? 4 : v <= 10 ? 3 : v <= 20 ? 2 : v <= 35 ? 1 : 0;
  return [score, `пошлина MFN ${fmt(v)}% (WITS/TRAINS, ${rate.year} год); преференции и национальная подстрока — у брокера`, `${fmt(v)}%`];
}

function obstaclesPart(data: CorridorData, fr: string, to: string, hs6: string): [number | null, string, string, boolean] {
  const pair = new Set([fr, to]);
  const seen = data.registry.programs.filter((p) => p.url in data.registry.fetched);
  const hitting = [...new Set(seen.filter((p) => p.targets.some((t) => pair.has(t))).map((p) => p.authority))].sort();
  const banFacts = data.facts.filter((f) => f.block === "sanctions" && isBanStatement(f) && [...sanctionTargets(f)].some((t) => pair.has(t)));
  const banned = banFacts.some((f) => f.hs_scope && f.hs_scope.length > 0 && scopeMatches(f.hs_scope, hs6));
  if (banned) return [0, "источник называет запрет для этой пары «страна — товар» (см. блок «Режим»): оценка обнулена", "запрет", true];
  if (hitting.length || banFacts.length) {
    const who = hitting.length ? hitting.join(", ") : "третьих стран";
    return [2, `санкционные режимы ${who} действуют в отношении одной из стран пары — препятствие (расчёты, логистика, отдельные товарные запреты); запрет именно этой группы источники не называют`, `есть: ${hitting.length ? hitting.join(", ") : "см. режим"}`, false];
  }
  if (seen.length) return [4, `проверенные страницы санкционных программ (${seen.length}) не называют страны пары; полный список режимов не проверен`, "в проверенных программах нет", false];
  return [null, "санкционные режимы для пары не проверены", "не проверено", false];
}

function supportPart(data: CorridorData, fr: string, hs6: string): Part {
  const n = data.facts.filter((f) => f.block === "export_support" && f.country === fr && scopeMatches(f.hs_scope, hs6)).length;
  if (n === 0) return [null, "программы поддержки экспортёра не собраны из источников", "не собрано"];
  return [n <= 2 ? 3 : 4, `${n} строк о программах поддержки из официальных источников`, `${n} стр.`];
}

function demandPart(data: CorridorData, to: string, hs6: string): [number | null, string] {
  const d = getDemand(data, to, hs6);
  if (!d) return [null, "торговая статистика для этой пары ещё не загружена (UN Comtrade) — ориентир появится после загрузки"];
  if (d.stale) return [null, `последние данные о ввозе за ${d.latest_year} год — старше ${STALE_YEARS} лет, балл не ставится (UN Comtrade, ориентир)`];
  let score = 3;
  if (d.value >= 100e6) score += 1;
  if (d.growth_pct !== null) {
    if (d.growth_pct >= 10) score += 1;
    else if (d.growth_pct <= -10) score -= 1;
  }
  score = Math.max(1, Math.min(5, score));
  const growth = d.growth_pct !== null ? `, ${d.growth_pct >= 0 ? "+" : ""}${d.growth_pct}% за ${d.span_years} года` : "";
  const kind = d.kind === "mirror" ? ` (зеркальные данные ${d.partners} партнёров, неполные)` : "";
  return [score, `ввоз ${usdText(d.value)} в ${d.latest_year} году${growth}${kind} — UN Comtrade, ориентир`];
}

export function agreementText(fr: string, to: string, doc: CorridorData["agreements"]): string {
  if (!doc) return "не проверено";
  const found = agreementsBetween(fr, to, doc) ?? [];
  if (found.length === 0 && doc.agreements.length === 0) return "не проверено";
  if (found.length === 0) return "нет в базе РТС ВТО";
  return found.slice(0, 2).map((a) => a.name).join("; ") + (found.length > 2 ? " (+)" : "");
}

export interface Computed {
  total: number;
  of: number;
  verdict: string;
  verdictStatus: ScoreStatus;
  parts: RatingPart[];
  agreement: string;
  duty: string;
  sanctions: string;
  support: string;
  banned: boolean;
}

export function compute(data: CorridorData, fr: string, to: string, hs6: string): Computed {
  const [dScore, dBasis, dShort] = dutyPart(data, to, hs6);
  const [oScore, oBasis, oShort, banned] = obstaclesPart(data, fr, to, hs6);
  const [sScore, sBasis, sShort] = supportPart(data, fr, hs6);
  const [dmScore, dmBasis] = demandPart(data, to, hs6);
  const parts: RatingPart[] = [
    { name: PART_NAMES[0], score: dScore, basis: dBasis },
    { name: PART_NAMES[1], score: oScore, basis: oBasis },
    { name: PART_NAMES[2], score: sScore, basis: sBasis },
    { name: PART_NAMES[3], score: dmScore, basis: dmBasis },
    { name: PART_NAMES[4], score: null, basis: "индексы логистики не подключены — ориентир появится позже, статус «проверено» не получает никогда" },
  ];
  const scored = parts.filter((p) => p.score !== null);
  const total = banned ? 0 : scored.reduce((n, p) => n + (p.score ?? 0), 0);
  const of = 5 * scored.length;
  let verdict: string;
  let status: ScoreStatus;
  if (banned) [verdict, status] = ["запрет: оценка обнулена", "warn"];
  else if (scored.length === 0) [verdict, status] = ["не рассчитано: нет данных индексного слоя", "warn"];
  else {
    const ratio = total / of;
    [verdict, status] = ratio >= 0.7 ? ["выгодно по проверенным частям", "ok"] : ratio >= 0.45 ? ["средне по проверенным частям", "mid"] : ["дорого или сложно по проверенным частям", "warn"];
  }
  return { total, of, verdict, verdictStatus: status, parts, agreement: agreementText(fr, to, data.agreements), duty: dShort, sanctions: oShort, support: sShort, banned };
}

export function compareRows(data: CorridorData, fr: string, to: string, hs6: string): CompareRow[] {
  const destinations = [...new Set([...Object.keys(data.registry.rates), to])].sort();
  const rows: (CompareRow & { _ratio: number })[] = [];
  for (const dest of destinations) {
    if (dest === fr) continue;
    const c = compute(data, fr, dest, hs6);
    const here = dest === to;
    const name = data.countries[dest]?.name ?? dest;
    rows.push({
      to: here ? `${name} — эта страница` : name,
      ...(here ? { here: true } : {}),
      duty: c.duty, agreement: c.agreement, sanctions: c.sanctions, support: c.support,
      score: { text: c.banned ? "запрет" : c.of === 0 ? "не рассчитано" : `${c.total} из ${c.of}`, status: c.verdictStatus },
      _ratio: c.of === 0 ? -1 : c.total / c.of,
    });
  }
  rows.sort((a, b) => b._ratio - a._ratio || a.to.localeCompare(b.to, "ru"));
  return rows.map((r) => {
    const { _ratio: _unused, ...row } = r;
    void _unused;
    return row;
  });
}

/* ---------- blank page (pipeline/requests.py blank_page) and assembly (pipeline/assemble.py) ---------- */

function section(id: string, number: number | undefined, title: string, lead: string, text: string): Section {
  return { id, ...(number !== undefined ? { number } : {}), title, lead, facts: [{ text, stamp: NOT_FOUND }] };
}

export function countryRef(data: CorridorData, code: string): CountryRef {
  return data.countries[code] ?? { code, name: code, from: `из ${code}`, to: `в ${code}`, loc: `в ${code}` };
}

export function blankPage(data: CorridorData, fr: string, to: string, hs6: string): PageContent {
  const cf = countryRef(data, fr);
  const ct = countryRef(data, to);
  const name = data.product?.ru || data.product?.en || `товары группы ${hs6}`;
  const label = `HS ${hs6.slice(0, 4)}.${hs6.slice(4)}`;
  return {
    corridor: { id: `${fr.toLowerCase()}-${to.toLowerCase()}`, from: cf, to: ct, modes: ["b2b"], languages: ["ru"] },
    product: { hs6, name, hsLabel: label },
    lang: "ru",
    isDemo: false,
    status: { sourcesTotal: 0, sourcesMissing: 0, lastChecked: "", text: `Страница собрана в браузере для группы ${label} из структурированных данных. Каждая строка появляется только с цитатой из официального источника. Это не юридическая консультация.` },
    summary: { id: "s0", title: "Коротко", facts: [
      { key: "Пошлина при ввозе", text: `Ставка MFN ${ct.loc || ct.name} для группы ${label} ещё не загружена в таблицу ставок.`, stamp: NOT_LOADED },
      { key: "Код товара", text: `Страница работает на уровне группы ${label}; национальную подстроку подтвердите у брокера или через предварительное решение таможни.`, stamp: BROKER },
      { key: "Соглашение", text: "Торговые соглашения между странами не проверены.", stamp: NOT_FOUND },
      { key: "Санкции", text: "Санкционные режимы для пары не проверены.", stamp: NOT_FOUND },
    ] },
    rating: { id: "sv", title: "Выгодно и что мешает", lead: "Оценка коридора складывается из пяти частей, каждую можно проверить. Запрет или санкции обнулили бы её независимо от остальных.", total: 0, of: 0, verdict: "не рассчитано", verdictStatus: "warn", explanation: "", parts: [] },
    verdict: { prosTitle: "Выгодно", consTitle: "Мешает", pros: [], cons: [] },
    compare: { id: "sw", title: `Куда ещё везти этот товар ${cf.from}`, lead: "Те же части для других рынков, отсортированы по оценке. Спрос и логистика в ней — ориентир, а не проверенный факт.", rows: [] },
    regime: section("s1", 1, "Режим торговли между странами", "Соглашения, санкции и торговые меры между странами пары.", "Режим торговли для этой пары не собран."),
    export: section("s2", 2, `Вывоз ${cf.from}`, "Разрешения, декларирование, экспортные пошлины и поддержка на стороне вывоза.", "Правила вывоза для этой группы не собраны."),
    exportControl: section("s2b", undefined, "Экспортный контроль и двойное назначение", "Лицензии на вывоз и списки товаров двойного назначения обеих стран показываются как есть. Принадлежность товара к спискам — по национальному коду у брокера.", "Контрольные списки для этой группы не проверены."),
    import: section("s3", 3, `Ввоз ${ct.to}`, "Пошлины, налоги, разрешения, маркировка и запреты на стороне ввоза.", "Правила ввоза для этой группы не собраны."),
    cost: { id: "s4", number: 4, title: "Сколько заплатить", lead: "Расчёт появится, когда ставки для группы будут в таблице ставок.", currency: "", inputs: [], lines: [], totalLabel: "Итого", note: "Ставки не загружены — калькулятор пуст." },
    logistics: section("s5", 5, "Как везти", "Маршруты, сроки и стоимость — всегда ориентир.", "Логистика для этого коридора не собрана."),
    documents: { id: "s6", number: 6, title: "Документы", lead: "Перечни появятся из официальных источников.", groups: [] },
    sources: { id: "s7", number: 7, title: "Источники", lead: "Официальные страницы, из которых собраны строки выше, с датой проверки.", rows: [] },
    rail: { disclaimer: "Не юридическая консультация. Код товара и ставки подтвердите у таможенного брокера.", reverseLabel: null as unknown as undefined, followSample: null },
  };
}

function rateFact(data: CorridorData, to: string, hs6: string): Fact | null {
  const rate = getRate(data, to, hs6);
  if (!rate) return null;
  const v = fmt(rate.value);
  return {
    key: "Пошлина при ввозе",
    text: `Пошлина при ввозе по режиму наибольшего благоприятствования: ${v}% (простая средняя по группе HS-6, база WITS/TRAINS, данные за ${rate.year} год). Национальная подстрока и льготные ставки уточняются у брокера.`,
    rate_ref: `${to}:${hs6}:import_mfn`,
    quote: `${hs6} ${v}`,
    stamp: { status: "ok", source: "wits.worldbank.org", label: `таблица ставок, снимок ${ruDate(rate.fetched_at)}`, verifiedAt: rate.fetched_at.slice(0, 10), url: rate.url },
  };
}

/** Everything the page can say about a pair and a group, assembled from the loaded data only. */
export function assemblePage(data: CorridorData, fr: string, to: string, hs6: string): PageContent {
  const page = blankPage(data, fr, to, hs6);
  const pair = new Set([fr, to]);
  const bySection: Record<"regime" | "export" | "exportControl" | "import" | "logistics", Fact[]> = { regime: [], export: [], exportControl: [], import: [], logistics: [] };
  for (const fact of data.facts) {
    const country = fact.country ?? "";
    if (!scopeMatches(fact.hs_scope, hs6)) continue;
    if (fact.block === "sanctions") {
      if (![...sanctionTargets(fact)].some((t) => pair.has(t))) continue;
    } else if (country !== "" && !pair.has(country)) continue;
    const sec = BLOCK_TO_SECTION[fact.block];
    if (!sec) continue;
    if (sec === "export" && country !== "" && country !== fr) continue;
    if (sec === "import" && country !== "" && country !== to) continue;
    bySection[sec].push(toPageFact(fact));
  }
  for (const sec of ["regime", "export", "exportControl", "import", "logistics"] as const) {
    const block = sec === "exportControl" ? page.exportControl! : page[sec];
    block.facts = [...bySection[sec], ...block.facts];
  }

  // Summary: duty from the rates layer replaces the "not loaded" placeholder; demand as an "ориентир" line.
  let summary = page.summary.facts;
  const duty = rateFact(data, to, hs6);
  if (duty) summary = [duty, ...summary.filter((f) => f.key !== "Пошлина при ввозе")];
  const agreement = agreementText(fr, to, data.agreements);
  if (data.agreements) {
    summary = summary.map((f) => f.key === "Соглашение" ? {
      key: "Соглашение",
      text: agreement === "нет в базе РТС ВТО" ? "Региональных торговых соглашений между странами пары нет в базе РТС ВТО (соглашения в силе, уведомлённые в ВТО)." : `Соглашения между странами пары в базе РТС ВТО: ${agreement}. Условия применения преференций — в тексте соглашения и у брокера.`,
      stamp: { status: "ok", source: "rtais.wto.org", label: `база РТС ВТО, соглашения в силе`, url: "https://rtais.wto.org/UI/PublicMaintainRTAHome.aspx" },
    } : f);
  }
  const d = getDemand(data, to, hs6);
  if (d && !d.stale) {
    const growth = d.growth_pct !== null ? `, изменение ${d.growth_pct >= 0 ? "+" : ""}${d.growth_pct}% за ${d.span_years} года` : "";
    const kind = d.kind === "mirror" ? " Зеркальные данные партнёров, неполные." : "";
    summary.push({
      key: "Спрос",
      text: `Ввоз этой группы ${page.corridor.to.to}: ${usdText(d.value)} в ${d.latest_year} году${growth}.${kind} Это ориентир по торговой статистике, не проверенный факт.`,
      stat_ref: `comtrade:${to}:${hs6}:${d.latest_year}`,
      stamp: { status: "note", source: "comtradeplus.un.org", label: `ориентир, данные за ${d.latest_year} год, снимок ${ruDate(d.fetched_at)}`, verifiedAt: d.fetched_at.slice(0, 10), url: d.url },
    });
  }
  page.summary.facts = summary;

  // Sources table: one row per distinct source URL used above.
  const urls = new Map<string, { source: string; checked: string }>();
  for (const sec of ["regime", "export", "exportControl", "import", "logistics"] as const) {
    for (const f of bySection[sec]) {
      if (f.stamp.url && !urls.has(f.stamp.url)) urls.set(f.stamp.url, { source: f.stamp.source, checked: f.stamp.label.split("проверено ").pop()! });
    }
  }
  if (duty?.stamp.url && !urls.has(duty.stamp.url)) urls.set(duty.stamp.url, { source: "wits.worldbank.org", checked: duty.stamp.label.split("снимок ").pop()! });
  page.sources.rows = [...urls.values()].map((v) => ({ source: v.source, confirms: "цитата проверена", checked: v.checked, status: { text: "актуально", kind: "ok" as const } }));

  // Rating and "where else": the index layer.
  const computed = compute(data, fr, to, hs6);
  page.rating = {
    ...page.rating,
    total: computed.total, of: computed.of, verdict: computed.verdict, verdictStatus: computed.verdictStatus, parts: computed.parts,
    explanation: "Пошлины, препятствия и господдержка считаются по правилам из структурированных данных (таблица ставок, база РТС ВТО, страницы санкционных программ, собранные факты). Спрос и логистика — ориентир; часть без данных балла не получает, итог считается из оценённых частей.",
  };
  page.compare.rows = compareRows(data, fr, to, hs6);

  // Status band: what is sourced and, honestly, which side of the pair the registry does not cover yet.
  const sourced = Object.values(bySection).reduce((n, v) => n + v.length, 0) + (duty ? 1 : 0);
  const missing = [fr, to].filter((c) => !data.registry.countries[c]).map((c) => countryRef(data, c).name);
  const parts = [`Страница собрана в браузере ${ruDateOf(data.today)} из данных, которые конвейер загрузил из официальных источников (снимок данных ${ruDate(data.registry.generated)}).`];
  if (sourced) parts.push(`На странице ${sourced} строк с дословной цитатой или ссылкой на таблицу (${urls.size} источников); остальные помечены «не собрано».`);
  else parts.push("Строк из источников для этой пары и группы пока нет: все блоки помечены «не собрано».");
  if (missing.length) parts.push(`В реестре источников пока нет страниц для: ${missing.join(", ")} — правила этой стороны не собраны, а не «отсутствуют».`);
  parts.push("Это не юридическая консультация: код товара и ставки подтвердите у таможенного брокера.");
  page.status = { sourcesTotal: urls.size, sourcesMissing: missing.length, lastChecked: data.today.toISOString().slice(0, 10), text: parts.join(" ") };
  return page;
}
