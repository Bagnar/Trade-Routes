/**
 * Page store. Stage 0: JSON demo fixtures in web/data/pages (all `isDemo: true`).
 * Stage 3: the same functions read the `pages` table (JSONB `content`) — callers do not change.
 */
import { promises as fs } from "node:fs";
import path from "node:path";
import type { Lang, PageContent, PageMeta } from "./page-content";

export { pageHref } from "./routes";

const PAGES_DIR = path.join(process.cwd(), "data", "pages");

function fileName(corridorId: string, hs6: string, lang: Lang): string {
  return `${corridorId}-${hs6}-${lang}.json`;
}

export async function getPage(corridorId: string, hs6: string, lang: Lang = "ru"): Promise<PageContent | null> {
  try {
    const raw = await fs.readFile(path.join(PAGES_DIR, fileName(corridorId, hs6, lang)), "utf8");
    return JSON.parse(raw) as PageContent;
  } catch {
    return null;
  }
}

export async function listPages(): Promise<PageMeta[]> {
  let names: string[] = [];
  try {
    names = (await fs.readdir(PAGES_DIR)).filter((n) => n.endsWith(".json")).sort();
  } catch {
    return [];
  }
  const metas: PageMeta[] = [];
  for (const name of names) {
    const page = JSON.parse(await fs.readFile(path.join(PAGES_DIR, name), "utf8")) as PageContent;
    metas.push({
      corridorId: page.corridor.id,
      hs6: page.product.hs6,
      lang: page.lang,
      isDemo: page.isDemo,
      product: page.product,
      corridor: page.corridor,
      rating: {
        total: page.rating.total,
        of: page.rating.of,
        verdict: page.rating.verdict,
        verdictStatus: page.rating.verdictStatus,
      },
    });
  }
  return metas;
}
