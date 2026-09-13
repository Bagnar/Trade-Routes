/** Live numbers for the home page, read from the repository data at build time (rebuilt daily by pages.yml). */
import { promises as fs } from "node:fs";
import path from "node:path";
import { allCountries } from "./countries";
import { listFactsFiles } from "./facts";
import { loadRegistry } from "./registry";

const ROOT = path.join(process.cwd(), "..");

export interface SiteStats {
  countries: number;
  hs6: number;
  hs6Ru: number;
  facts: number;
  sourcesRead: number;
  registrySources: number;
  ratesCountries: number;
  agreements: number;
  lastChecked: string;
}

export async function siteStats(): Promise<SiteStats> {
  const [facts, registry] = await Promise.all([listFactsFiles(), loadRegistry()]);
  let hs6 = 0;
  let hs6Ru = 0;
  try {
    const rows = JSON.parse(await fs.readFile(path.join(ROOT, "data", "hs6.json"), "utf8")) as { ru?: string }[];
    hs6 = rows.length;
    hs6Ru = rows.filter((r) => r.ru).length;
  } catch {
    // reference data not loaded yet
  }
  let ratesCountries = 0;
  try {
    ratesCountries = (await fs.readdir(path.join(ROOT, "data", "rates"))).filter((n) => n.endsWith(".json")).length;
  } catch {
    // none loaded
  }
  let agreements = 0;
  try {
    agreements = ((JSON.parse(await fs.readFile(path.join(ROOT, "data", "agreements.json"), "utf8")) as { agreements?: unknown[] }).agreements ?? []).length;
  } catch {
    // none loaded
  }
  let lastChecked = "";
  try {
    const report = await fs.readFile(path.join(ROOT, "data", "monitor-report.md"), "utf8");
    lastChecked = /(\d{4}-\d{2}-\d{2})/.exec(report)?.[1] ?? "";
  } catch {
    // no report yet
  }
  const registrySources = Object.values(registry.countries).reduce((n, c) => n + c.sources.length, 0) + Object.values(registry.blocs).reduce((n, c) => n + c.sources.length, 0) + registry.sanctions.length + registry.exportControl.length;
  return {
    countries: Object.keys(allCountries()).length,
    hs6,
    hs6Ru,
    facts: facts.reduce((n, f) => n + f.facts.length, 0),
    sourcesRead: facts.length,
    registrySources,
    ratesCountries,
    agreements,
    lastChecked,
  };
}

export function ruDate(iso: string): string {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleDateString("ru-RU", { day: "numeric", month: "long", year: "numeric" });
}
