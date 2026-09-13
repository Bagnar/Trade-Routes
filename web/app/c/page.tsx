import type { Metadata } from "next";
import { AssembledCorridor } from "@/components/AssembledCorridor";

export const metadata: Metadata = { title: "Коридор — сборка из данных" };

/**
 * /c/?from=CN&to=CA&hs6=610910 — a corridor page for any pair of countries and any HS-6 group, assembled in the
 * browser from the structured data the pipeline loaded (docs/concept.md, decision 15). Static export: the HTML
 * shell is pre-rendered once; the client reads the query string and builds the page from public/data.
 */
export default function Page() {
  return <AssembledCorridor />;
}
