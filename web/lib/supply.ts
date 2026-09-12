/**
 * "Where to buy" page store. Stage 0: JSON demo fixtures in web/data/supply (all `isDemo: true`).
 * Later: the same functions read the `supply_pages` table.
 */
import { promises as fs } from "node:fs";
import path from "node:path";
import type { Lang } from "./page-content";
import type { SupplyContent, SupplyMeta } from "./supply-content";

const SUPPLY_DIR = path.join(process.cwd(), "data", "supply");

export async function getSupplyPage(country: string, hs: string, lang: Lang = "ru"): Promise<SupplyContent | null> {
  const name = `${country.toLowerCase()}-${hs}-${lang}.json`;
  try {
    const raw = await fs.readFile(path.join(SUPPLY_DIR, name), "utf8");
    return JSON.parse(raw) as SupplyContent;
  } catch {
    return null;
  }
}

export async function listSupplyPages(): Promise<SupplyMeta[]> {
  let names: string[] = [];
  try {
    names = (await fs.readdir(SUPPLY_DIR)).filter((n) => n.endsWith(".json")).sort();
  } catch {
    return [];
  }
  const metas: SupplyMeta[] = [];
  for (const name of names) {
    const page = JSON.parse(await fs.readFile(path.join(SUPPLY_DIR, name), "utf8")) as SupplyContent;
    metas.push({
      country: page.country,
      hs: page.product.hs,
      lang: page.lang,
      isDemo: page.isDemo,
      product: page.product,
      regionCount: page.regions.rows.length,
      topRegions: page.regions.rows.slice(0, 3).map((r) => r.region),
    });
  }
  return metas;
}

/** Finds a "where to buy" page for a country whose HS prefix matches the given HS-6 (exact or HS-4). */
export async function findSupplyFor(country: string, hs6: string, lang: Lang = "ru"): Promise<SupplyMeta | null> {
  const pages = await listSupplyPages();
  const candidates = pages.filter((p) => p.country.code === country && p.lang === lang);
  return candidates.find((p) => p.hs === hs6) ?? candidates.find((p) => hs6.startsWith(p.hs)) ?? null;
}
