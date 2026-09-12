/**
 * Reads the pipeline's extracted facts (data/facts/*.json at the repository root, written by
 * `python -m pipeline extract`). Every fact carries a verbatim quote, the source URL and the snapshot date.
 */
import { promises as fs } from "node:fs";
import path from "node:path";

export interface ExtractedFact {
  block: string;
  country: string;
  hs_scope: string[];
  statement: { ru: string; en: string };
  quote: string;
  quote_lang: string;
  has_number: boolean;
}

export interface FactsFile {
  url: string;
  source_id: string;
  fetched_at: string;
  content_hash: string;
  topic: string | null;
  facts: ExtractedFact[];
  dropped: number;
}

const FACTS_DIR = path.join(process.cwd(), "..", "data", "facts");

export async function listFactsFiles(): Promise<FactsFile[]> {
  let names: string[] = [];
  try {
    names = (await fs.readdir(FACTS_DIR)).filter((n) => n.endsWith(".json")).sort();
  } catch {
    return [];
  }
  const files: FactsFile[] = [];
  for (const name of names) {
    try {
      files.push(JSON.parse(await fs.readFile(path.join(FACTS_DIR, name), "utf8")) as FactsFile);
    } catch {
      // a half-written or invalid file is skipped, never rendered
    }
  }
  return files;
}

export const BLOCK_LABELS: Record<string, string> = {
  regime: "Режим торговли",
  export: "Вывоз",
  export_support: "Господдержка экспорта",
  import: "Ввоз",
  cost: "Сколько платить",
  logistics: "Как везти",
  documents: "Документы",
  sanctions: "Санкции",
  supply: "Где купить",
};
