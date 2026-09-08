/**
 * Corridor page content — the block structure stored in `pages.content` (JSONB) and rendered by the web app.
 *
 * This file is the single definition of the page template (docs/plan.md, stage 0: "шаблон страницы коридора как
 * структура данных"). The pipeline's `assemble` step must produce exactly this shape; the front end never
 * assembles facts itself.
 *
 * Every line of text on the page carries a `Stamp` (docs/concept.md, section 4). Numbers inside the calculator
 * come from the `rates` table via the pipeline — never from an LLM. Demo fixtures are flagged `isDemo: true`.
 */

export type Lang = "ru" | "en" | "zh" | "fa";
export type Mode = "b2b" | "parcel";

/**
 * Visual state of a source stamp. Maps from `fact_status` / `fact_freshness.display_status` in db/schema.sql:
 *   verified            -> "ok"
 *   stale, stale_warning-> "warn"
 *   not_found, unavailable -> "none"
 *   prohibited          -> "ban"
 *   estimate, confirm_with_broker -> "note"
 */
export type StampStatus = "ok" | "warn" | "none" | "ban" | "note";

export interface Stamp {
  status: StampStatus;
  /** Source domain(s), shown in bold: "cbsa-asfc.gc.ca" or "ofac.treasury.gov, sanctionsmap.eu". */
  source: string;
  /** Human-readable status line: "проверено 5 сен 2026", "источник не найден", "оценка, не источник". */
  label: string;
  /** ISO date of the last verification, when known. */
  verifiedAt?: string;
  /** Link to the source page, when the fact has one. */
  url?: string;
}

/** Text that may differ by shipment mode. A plain string applies to both modes. */
export type ModeText = string | Partial<Record<Mode, string>>;

export interface Fact {
  /** Short key shown in the "Коротко" block ("Пошлина при ввозе"). */
  key?: string;
  text: ModeText;
  stamp: Stamp;
  /** Red dot before the text (prohibition). */
  ban?: boolean;
  /** Show only in these modes; absent = both. */
  modes?: Mode[];
}

export interface FactGroup {
  title?: string;
  facts: Fact[];
}

export interface Section {
  /** Anchor id used by the table of contents: "s1", "s2", ... */
  id: string;
  /** Number badge shown before the title; the summary/verdict/compare blocks have none. */
  number?: number;
  title: string;
  lead?: string;
  facts: Fact[];
  /** Sub-blocks such as "Что даёт государство экспортёру". */
  groups?: FactGroup[];
}

export type ScoreStatus = "ok" | "mid" | "warn";

export interface RatingPart {
  name: string;
  /** 0..5, or null when there is no basis — a score without a basis is never shown. */
  score: number | null;
  basis: string;
}

export interface Rating {
  lead: string;
  total: number;
  of: number;
  verdict: string;
  verdictStatus: ScoreStatus;
  explanation: string;
  parts: RatingPart[];
}

export type VerdictKind = "pro" | "pro-check" | "con" | "con-ban";

export interface VerdictItem {
  kind: VerdictKind;
  text: string;
  modes?: Mode[];
}

export interface CompareRow {
  to: string;
  /** This page's own destination. */
  here?: boolean;
  duty: string;
  agreement: string;
  sanctions: string;
  support: string;
  score: { text: string; status: ScoreStatus };
}

/* ---------- calculator: a small data-driven expression language, no eval ---------- */

export interface CalcOption {
  value: number;
  label: string;
  /** Short form used inside line labels ("HST 13%"). */
  short?: string;
}

export interface CalcInput {
  id: string;
  label: string;
  kind: "number" | "checkbox" | "select";
  value: number | boolean;
  min?: number;
  step?: number;
  options?: CalcOption[];
  modes?: Mode[];
}

export type CalcExpr =
  | number
  | { input: string }
  | { line: string }
  | { mul: CalcExpr[] }
  | { add: CalcExpr[] }
  | { div: [CalcExpr, CalcExpr] }
  | { if: string; then: CalcExpr; else: CalcExpr }
  | { mode: Record<Mode, CalcExpr> };

export type CalcLabel =
  | string
  | { if: string; then: CalcLabel; else: CalcLabel }
  | { mode: Record<Mode, CalcLabel> }
  /** Substitutes `{short}` / `{label}` of the selected option of `select`. */
  | { template: string; select: string };

export interface CalcLine {
  id: string;
  label: CalcLabel;
  expr: CalcExpr;
}

export interface Calculator {
  id: string;
  number: number;
  title: string;
  lead: string;
  currency: string;
  inputs: CalcInput[];
  lines: CalcLine[];
  totalLabel: string;
  note: string;
}

/* ---------- documents, sources, rail ---------- */

export interface ChecklistGroup {
  title: string;
  items: string[];
  modes?: Mode[];
}

export interface SourceRow {
  source: string;
  confirms: string;
  checked: string;
  status: { text: string; kind: "ok" | "warn" | "none" };
}

export interface CountryRef {
  code: string;
  /** Nominative: "Канада". */
  name: string;
  /** "из Китая" — genitive. */
  from: string;
  /** "в Канаду" — accusative. */
  to: string;
}

export interface PageContent {
  corridor: {
    id: string;
    from: CountryRef;
    to: CountryRef;
    modes: Mode[];
    languages: Lang[];
    /** Optional note shown when a mode is unavailable ("Для этой товарной группы не применимо"). */
    parcelDisabledReason?: string;
  };
  product: {
    hs6: string;
    /** Query phrase in the accusative: "футболки хлопковые трикотажные". */
    name: string;
    /** "HS 6109.10". */
    hsLabel: string;
  };
  lang: Lang;
  isDemo: boolean;
  status: {
    sourcesTotal: number;
    sourcesMissing: number;
    lastChecked: string;
    text: string;
  };
  sanctions?: {
    tag: string;
    text: string;
  };
  summary: { id: string; title: string; facts: Fact[] };
  rating: { id: string; title: string } & Rating;
  verdict: { prosTitle: string; consTitle: string; pros: VerdictItem[]; cons: VerdictItem[] };
  compare: { id: string; title: string; lead: string; rows: CompareRow[] };
  regime: Section;
  export: Section;
  import: Section;
  cost: Calculator;
  logistics: Section;
  documents: { id: string; number: number; title: string; lead: string; groups: ChecklistGroup[] };
  sources: { id: string; number: number; title: string; lead: string; rows: SourceRow[] };
  rail: {
    disclaimer: string;
    reverseLabel?: string;
    followSample?: string;
  };
}

export interface PageMeta {
  corridorId: string;
  hs6: string;
  lang: Lang;
  isDemo: boolean;
  product: PageContent["product"];
  corridor: PageContent["corridor"];
  rating: Pick<Rating, "total" | "of" | "verdict" | "verdictStatus">;
}
