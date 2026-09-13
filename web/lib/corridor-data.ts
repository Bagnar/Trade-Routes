"use client";

/**
 * Loads the browser-side inputs of the corridor assembler from public/data (written by scripts/copy-data.mjs)
 * for one pair of countries and one HS-6 group. Small, chapter-sized files: the nomenclature chapter, the rates
 * chapter, the two countries' facts, the sanctions facts, demand, agreements and the registry summary.
 */
import type { CountryRef } from "./page-content";
import type { CorridorData, RegistrySummary, SourcedFact } from "./assemble-client";

const BASE = process.env.NEXT_PUBLIC_BASE_PATH ?? "";
const cache = new Map<string, Promise<unknown>>();

function getJson<T>(rel: string, fallback: T): Promise<T> {
  let p = cache.get(rel) as Promise<T> | undefined;
  if (!p) {
    p = fetch(`${BASE}/data/${rel}`)
      .then((r) => (r.ok ? (r.json() as Promise<T>) : fallback))
      .catch(() => fallback);
    cache.set(rel, p);
  }
  return p;
}

export async function loadCorridorData(fr: string, to: string, hs6: string): Promise<CorridorData> {
  const chapter = hs6.slice(0, 2);
  const [registry, countryRows, chapterRows, rates, demand, agreements, factsFrom, factsTo, factsAny, factsSanctions] = await Promise.all([
    getJson<RegistrySummary | null>("registry.json", null),
    getJson<(CountryRef & { name_en?: string })[]>("countries.json", []),
    getJson<{ code: string; en: string; ru: string }[]>(`hs6/${chapter}.json`, []),
    getJson<CorridorData["rates"]>(`rates/${chapter}.json`, { rates: {}, specific: {} }),
    getJson<CorridorData["demand"]>("demand.json", {}),
    getJson<CorridorData["agreements"]>("agreements.json", null),
    getJson<SourcedFact[]>(`facts/${fr}.json`, []),
    fr === to ? Promise.resolve([] as SourcedFact[]) : getJson<SourcedFact[]>(`facts/${to}.json`, []),
    getJson<SourcedFact[]>("facts/_any.json", []),
    getJson<SourcedFact[]>("facts/_sanctions.json", []),
  ]);
  return {
    registry: registry ?? { generated: "", countries: {}, programs: [], rates: {}, demand: [], fetched: {}, pages: [], factsTotal: 0 },
    countries: Object.fromEntries(countryRows.map((c) => [c.code, { code: c.code, name: c.name, from: c.from, to: c.to, loc: c.loc }])),
    product: chapterRows.find((e) => e.code === hs6) ?? null,
    rates: rates && rates.rates ? rates : { rates: {}, specific: {} },
    demand,
    agreements: agreements && Array.isArray(agreements.agreements) ? agreements : null,
    facts: [...factsFrom, ...factsTo, ...factsAny, ...factsSanctions],
    today: new Date(),
  };
}
