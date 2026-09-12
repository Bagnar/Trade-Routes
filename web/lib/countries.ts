/**
 * Country reference: every ISO 3166-1 country with the Russian phrases the query sentences need.
 * Source of truth: data/countries.json (repository root), built by scripts/build_countries.py.
 * Phrases carry their prepositions: from = "из Китая" / "с Кубы", to = "в Канаду" / "на Кубу", loc = "в Китае".
 * Server-only (reads the file system); client components receive the list as props.
 */
import { readFileSync } from "node:fs";
import path from "node:path";
import type { CountryRef } from "./page-content";

const FILE = path.join(process.cwd(), "..", "data", "countries.json");

let cache: Record<string, CountryRef> | null = null;

export function allCountries(): Record<string, CountryRef> {
  if (cache) return cache;
  const list = JSON.parse(readFileSync(FILE, "utf8")) as (CountryRef & { name_en: string })[];
  cache = Object.fromEntries(list.map((c) => [c.code, { code: c.code, name: c.name, from: c.from, to: c.to, loc: c.loc }]));
  return cache;
}

/** Countries for the search selects, MVP corridors first, then alphabetical (the file is already sorted by name). */
export function countryList(first: string[] = ["CN", "CA", "RU", "IR", "TR"]): CountryRef[] {
  const all = allCountries();
  const head = first.map((c) => all[c]).filter(Boolean);
  const rest = Object.values(all).filter((c) => !first.includes(c.code));
  return [...head, ...rest];
}

export function country(code: string): CountryRef {
  return allCountries()[code] ?? { code, name: code, from: `из ${code}`, to: `в ${code}`, loc: `в ${code}` };
}
