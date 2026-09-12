/**
 * HS-6 nomenclature for product search. Source of truth: data/hs6.json (official UN Comtrade reference list,
 * loaded by `python -m pipeline reference`) and data/hs_synonyms_ru.json (Russian search hints).
 * Server-only readers; the search component receives a compact index as props.
 */
import { readFileSync } from "node:fs";
import path from "node:path";

import type { HsEntry } from "./hs-types";

export type { HsEntry } from "./hs-types";
export { hsLabel } from "./hs-types";

const HS6_FILE = path.join(process.cwd(), "..", "data", "hs6.json");
const SYNONYMS_FILE = path.join(process.cwd(), "..", "data", "hs_synonyms_ru.json");

let hsCache: HsEntry[] | null = null;
let synCache: Record<string, string[]> | null = null;

export function allHs6(): HsEntry[] {
  if (hsCache) return hsCache;
  try {
    hsCache = JSON.parse(readFileSync(HS6_FILE, "utf8")) as HsEntry[];
  } catch {
    hsCache = []; // not loaded yet: the reference-data workflow fills it
  }
  return hsCache;
}

export function synonymsRu(): Record<string, string[]> {
  if (synCache) return synCache;
  try {
    const raw = JSON.parse(readFileSync(SYNONYMS_FILE, "utf8")) as Record<string, string[] | string>;
    synCache = Object.fromEntries(Object.entries(raw).filter(([k, v]) => !k.startsWith("_") && Array.isArray(v))) as Record<string, string[]>;
  } catch {
    synCache = {};
  }
  return synCache;
}
