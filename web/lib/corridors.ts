/**
 * Reads data/corridors.yaml (repository root) — the list of MVP corridors and their product groups.
 * The YAML is the editable master; nothing here is hard-coded.
 */
import { promises as fs } from "node:fs";
import path from "node:path";
import yaml from "js-yaml";
import type { Lang, Mode } from "./page-content";

export interface ProductGroup {
  hs6: string;
  name_ru: string;
  name_en: string;
  tests?: string;
}

export interface Corridor {
  id: string;
  from: string;
  to: string;
  modes: Mode[];
  languages: Lang[];
  rationale?: string;
  product_groups: ProductGroup[];
}

const CORRIDORS_FILE = path.join(process.cwd(), "..", "data", "corridors.yaml");

export async function listCorridors(): Promise<Corridor[]> {
  const raw = await fs.readFile(CORRIDORS_FILE, "utf8");
  const doc = yaml.load(raw) as { corridors?: Corridor[] };
  return (doc.corridors ?? []).map((c) => ({
    ...c,
    from: c.from.toUpperCase(),
    to: c.to.toUpperCase(),
    product_groups: (c.product_groups ?? []).map((g) => ({ ...g, hs6: String(g.hs6) })),
  }));
}
