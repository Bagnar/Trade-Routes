// Copies reference JSON from the repository's data/ into public/data so the browser can fetch it
// (product search loads the HS-6 nomenclature lazily). Runs before `next dev` and `next build`.
import { copyFileSync, existsSync, mkdirSync } from "node:fs";
import path from "node:path";

const root = path.resolve(process.cwd(), "..", "data");
const out = path.resolve(process.cwd(), "public", "data");
mkdirSync(out, { recursive: true });
for (const name of ["hs6.json", "hs_synonyms_ru.json", "countries.json"]) {
  const src = path.join(root, name);
  if (existsSync(src)) copyFileSync(src, path.join(out, name));
  else console.warn(`copy-data: ${name} not found yet (reference-data workflow fills it)`);
}
