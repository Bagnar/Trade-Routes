/**
 * "Where to buy" page content — the block structure stored in `supply_pages.content` (JSONB).
 * See docs/where-to-buy.md. Reuses Fact/Stamp/Section/SourceRow from the corridor page template so that
 * every line carries a source stamp. Regions and official registries only — never individual companies.
 */
import type { CountryRef, Fact, Lang, Section, SourceRow, Stamp } from "./page-content";

export interface RegionRow {
  /** Region / province name in the page language. */
  region: string;
  /** ISO 3166-2 code when known ("CN-SD"). */
  code?: string;
  /** What is made there and why it matters for this product group. */
  note: string;
  /** Indicator text from statistics ("доля в выпуске 23%, 2025") or an honest "не загружено". */
  indicator: string;
  stamp: Stamp;
}

export interface LinkRow {
  label: string;
  href: string;
  /** "open" — page exists; "closed" — corridor not assembled yet (rendered as plain text). */
  state: "open" | "closed";
}

export interface SupplyContent {
  country: CountryRef;
  product: {
    /** HS-4 or HS-6 prefix used in the URL: "8432", "6109". */
    hs: string;
    /** Query phrase in the accusative: "сельхозтехнику". */
    name: string;
    /** "HS 8432–8436". */
    hsLabel: string;
  };
  lang: Lang;
  isDemo: boolean;
  status: { sourcesTotal: number; sourcesMissing: number; lastChecked: string; text: string };
  summary: { id: string; title: string; facts: Fact[] };
  regions: { id: string; number: number; title: string; lead: string; rows: RegionRow[] };
  find: Section;
  check: Section;
  corridors: { id: string; number: number; title: string; lead: string; links: LinkRow[] };
  sources: { id: string; number: number; title: string; lead: string; rows: SourceRow[] };
  rail: { disclaimer: string };
}

export interface SupplyMeta {
  country: CountryRef;
  hs: string;
  lang: Lang;
  isDemo: boolean;
  product: SupplyContent["product"];
  regionCount: number;
  topRegions: string[];
}
