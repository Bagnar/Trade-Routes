// Exports the repository's structured data (data/*) into public/data so the browser can assemble a corridor page
// for any pair of countries and any HS-6 group without a server (docs/concept.md, decision 15). Runs before
// `next dev` and `next build`. Nothing here invents data: every file is a re-cut of what the pipeline loaded.
//
//   hs6.json, hs_synonyms_ru.json, countries.json      product search and country phrases (as before)
//   hs6/{chapter}.json                                  the nomenclature split by chapter (cheap product lookup)
//   rates/{chapter}.json                                {ISO2: {hs6: MFN %}} for every importer with a rates table
//   demand.json                                         {ISO2: series} — UN Comtrade import statistics (ориентир)
//   agreements.json                                     WTO RTA-IS agreements in force
//   facts/{ISO2}.json, facts/_sanctions.json, facts/_any.json   extracted facts with quote, URL and snapshot date
//   registry.json                                       what the pipeline has: registry countries, sanctions
//                                                       program pages (with targets), rates/demand availability,
//                                                       URLs fetched (with dates), prebuilt pages
import { copyFileSync, existsSync, mkdirSync, readdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import path from "node:path";
import yaml from "js-yaml";

const root = path.resolve(process.cwd(), "..", "data");
const pagesDir = path.resolve(process.cwd(), "data", "pages");
const out = path.resolve(process.cwd(), "public", "data");
mkdirSync(out, { recursive: true });

function readJson(file) {
  try {
    return JSON.parse(readFileSync(file, "utf8"));
  } catch {
    return null;
  }
}
function writeJson(rel, value) {
  const file = path.join(out, rel);
  mkdirSync(path.dirname(file), { recursive: true });
  writeFileSync(file, JSON.stringify(value));
}
function listJson(dir) {
  try {
    return readdirSync(dir).filter((n) => n.endsWith(".json")).sort();
  } catch {
    return [];
  }
}

for (const name of ["hs6.json", "hs_synonyms_ru.json", "countries.json", "agreements.json"]) {
  const src = path.join(root, name);
  if (existsSync(src)) copyFileSync(src, path.join(out, name));
  else console.warn(`copy-data: ${name} not found yet (reference-data workflow fills it)`);
}

// HS-6 by chapter.
const hs6 = readJson(path.join(root, "hs6.json")) ?? [];
rmSync(path.join(out, "hs6"), { recursive: true, force: true });
const byChapter = {};
for (const e of hs6) (byChapter[e.code.slice(0, 2)] ??= []).push(e);
for (const [ch, rows] of Object.entries(byChapter)) writeJson(`hs6/${ch}.json`, rows);

// Rates by chapter: one small file per chapter with every importer's MFN rates; metadata per importer in registry.
rmSync(path.join(out, "rates"), { recursive: true, force: true });
const ratesMeta = {};
const ratesByChapter = {};
for (const name of listJson(path.join(root, "rates"))) {
  const doc = readJson(path.join(root, "rates", name));
  if (!doc || !doc.rates) continue;
  const cc = name.slice(0, -5).toUpperCase();
  ratesMeta[cc] = { year: doc.year, source: doc.source, url: doc.url, fetched_at: doc.fetched_at, kind: doc.kind, unit: doc.unit };
  for (const [code, value] of Object.entries(doc.rates)) {
    const ch = code.slice(0, 2);
    ((ratesByChapter[ch] ??= {})[cc] ??= {})[code] = value;
  }
}
for (const [ch, rows] of Object.entries(ratesByChapter)) writeJson(`rates/${ch}.json`, rows);

// Demand: everything loaded, in one file (only the site's pairs are loaded, so it stays small).
const demand = {};
for (const name of listJson(path.join(root, "demand"))) {
  const doc = readJson(path.join(root, "demand", name));
  if (doc && doc.series) demand[name.slice(0, -5).toUpperCase()] = { source: doc.source, series: doc.series };
}
writeJson("demand.json", demand);

// Facts: flattened like pipeline/assemble.py load_facts (url, source_id, fetched_at on every fact), grouped by
// country; sanctions facts in their own file (they attach to any pair whose exporter or importer is a target).
rmSync(path.join(out, "facts"), { recursive: true, force: true });
const factsByCountry = {};
const sanctionsFacts = [];
const fetched = {};
let factsTotal = 0;
for (const name of listJson(path.join(root, "facts"))) {
  const doc = readJson(path.join(root, "facts", name));
  if (!doc || !Array.isArray(doc.facts)) continue;
  fetched[doc.url] = String(doc.fetched_at ?? "").slice(0, 10);
  for (const fact of doc.facts) {
    const rec = { ...fact, url: doc.url, source_id: doc.source_id, fetched_at: doc.fetched_at };
    factsTotal += 1;
    if (fact.block === "sanctions") sanctionsFacts.push(rec);
    else (factsByCountry[(fact.country || "_any").toUpperCase()] ??= []).push(rec);
  }
}
for (const [cc, rows] of Object.entries(factsByCountry)) writeJson(`facts/${cc === "_ANY" ? "_any" : cc}.json`, rows);
writeJson("facts/_sanctions.json", sanctionsFacts);

// Registry summary (from the whitelist data/sources.yaml) and what the pipeline has done with it.
let sources = {};
try {
  sources = yaml.load(readFileSync(path.join(root, "sources.yaml"), "utf8")) ?? {};
} catch {
  console.warn("copy-data: data/sources.yaml not readable");
}
const countries = {};
for (const [code, c] of Object.entries(sources.countries ?? {})) {
  const srcs = c.sources ?? [];
  countries[code.toUpperCase()] = {
    name: c.name ?? {},
    sources: srcs.length,
    urls: srcs.reduce((n, s) => n + (s.urls ?? []).length, 0),
    verified: srcs.filter((s) => s.status === "verified").length,
  };
}
const programs = [];
for (const entry of sources.sanctions_authorities ?? []) {
  for (const u of entry.urls ?? []) {
    if (u && typeof u === "object" && Array.isArray(u.targets) && u.targets.length) {
      programs.push({ authority: entry.jurisdiction ?? "", domain: entry.domain, url: u.url, targets: u.targets.map((t) => String(t).toUpperCase()) });
    }
  }
}
const pages = listJson(pagesDir)
  .map((n) => readJson(path.join(pagesDir, n)))
  .filter((p) => p && p.corridor && p.product)
  .map((p) => ({ corridor: p.corridor.id, from: p.corridor.from.code, to: p.corridor.to.code, hs6: p.product.hs6 }));
writeJson("registry.json", {
  generated: new Date().toISOString().slice(0, 10),
  countries,
  programs,
  rates: ratesMeta,
  demand: Object.keys(demand).sort(),
  fetched,
  pages,
  factsTotal,
});
console.log(`copy-data: ${hs6.length} HS-6, rates for ${Object.keys(ratesMeta).length} importers, demand for ${Object.keys(demand).length}, ${factsTotal} facts, ${programs.length} sanctions program pages, ${pages.length} prebuilt pages`);
