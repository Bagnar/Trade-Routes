/**
 * Read-only view of the source registry (data/sources.yaml, the whitelist) and of what the pipeline has done
 * with it: facts extracted per source and rates loaded per importer. Server-only (node:fs).
 */
import { promises as fs } from "node:fs";
import path from "node:path";
import yaml from "js-yaml";

export interface RegistryUrl {
  url: string;
  topic?: string;
  targets?: string[];
}

export interface RegistrySource {
  id: string;
  agency: string;
  domain: string;
  path_prefix?: string;
  topics: string[];
  priority: number;
  status: string;
  urls: RegistryUrl[];
  /** Country or bloc the source belongs to; jurisdiction for sanctions/export-control authorities. */
  jurisdiction?: string;
}

export interface CountryRegistry {
  code: string;
  name: { ru: string; en: string };
  languages: string[];
  sources: RegistrySource[];
  /** Blocs only: member ISO codes. */
  members?: string[];
}

export interface Registry {
  countries: Record<string, CountryRegistry>;
  blocs: Record<string, CountryRegistry>;
  sanctions: RegistrySource[];
  exportControl: RegistrySource[];
  international: RegistrySource[];
  logistics: RegistrySource[];
}

const ROOT = path.join(process.cwd(), "..");
const SOURCES_FILE = path.join(ROOT, "data", "sources.yaml");

type RawUrl = string | RegistryUrl;
type RawSource = Omit<RegistrySource, "urls" | "topics"> & { urls?: RawUrl[]; topics?: string[] };
type RawCountry = { name: { ru: string; en: string }; languages?: string[]; members?: string[]; sources?: RawSource[] };
type RawDoc = {
  countries?: Record<string, RawCountry>;
  blocs?: Record<string, RawCountry>;
  sanctions_authorities?: RawSource[];
  export_control_regimes?: RawSource[];
  international?: RawSource[];
  logistics_indices?: RawSource[];
};

function normSource(raw: RawSource): RegistrySource {
  return {
    ...raw,
    topics: raw.topics ?? [],
    priority: Number(raw.priority ?? 2),
    status: raw.status ?? "to_verify",
    urls: (raw.urls ?? []).map((u) => (typeof u === "string" ? { url: u } : { ...u, targets: u.targets?.map((t) => String(t).toUpperCase()) })),
  };
}

function normCountries(raw: Record<string, RawCountry> | undefined): Record<string, CountryRegistry> {
  const out: Record<string, CountryRegistry> = {};
  for (const [code, c] of Object.entries(raw ?? {})) {
    out[code.toUpperCase()] = {
      code: code.toUpperCase(),
      name: c.name,
      languages: c.languages ?? [],
      members: c.members?.map((m) => String(m).toUpperCase()),
      sources: (c.sources ?? []).map(normSource),
    };
  }
  return out;
}

let cache: Registry | null = null;

export async function loadRegistry(): Promise<Registry> {
  if (cache) return cache;
  const doc = yaml.load(await fs.readFile(SOURCES_FILE, "utf8")) as RawDoc;
  cache = {
    countries: normCountries(doc.countries),
    blocs: normCountries(doc.blocs),
    sanctions: (doc.sanctions_authorities ?? []).map(normSource),
    exportControl: (doc.export_control_regimes ?? []).map(normSource),
    international: (doc.international ?? []).map(normSource),
    logistics: (doc.logistics_indices ?? []).map(normSource),
  };
  return cache;
}

export interface RatesInfo {
  year: number;
  count: number;
  fetchedAt: string;
  url: string;
  source: string;
}

/** What the rates layer holds for an importer (data/rates/{ISO2}.json), or null when not loaded. */
export async function ratesInfo(code: string): Promise<RatesInfo | null> {
  try {
    const raw = await fs.readFile(path.join(ROOT, "data", "rates", `${code.toUpperCase()}.json`), "utf8");
    const doc = JSON.parse(raw) as { year: number; fetched_at: string; url: string; source: string; rates: Record<string, number> };
    return { year: doc.year, count: Object.keys(doc.rates).length, fetchedAt: String(doc.fetched_at).slice(0, 10), url: doc.url, source: doc.source };
  } catch {
    return null;
  }
}

export interface AgreementsInfo {
  fetchedAt: string;
  url: string;
  agreements: { name: string; type: string; in_force: string; members: string[] }[];
}

/** Regional trade agreements in force (data/agreements.json, WTO RTA-IS), or null when not loaded. */
export async function agreementsInfo(): Promise<AgreementsInfo | null> {
  try {
    const doc = JSON.parse(await fs.readFile(path.join(ROOT, "data", "agreements.json"), "utf8")) as { fetched_at: string; url: string; agreements: AgreementsInfo["agreements"] };
    return { fetchedAt: String(doc.fetched_at).slice(0, 10), url: doc.url, agreements: doc.agreements ?? [] };
  } catch {
    return null;
  }
}
