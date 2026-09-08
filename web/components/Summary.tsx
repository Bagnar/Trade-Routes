import type { Mode, PageContent } from "@/lib/page-content";
import { FactRow } from "./FactRow";

/** "Коротко": 5–6 key lines, each with a short key on the left and a stamp on the right. */
export function Summary({ summary, mode }: { summary: PageContent["summary"]; mode: Mode }) {
  return (
    <>
      <h2 id={summary.id}>{summary.title}</h2>
      <div className="summary">
        {summary.facts.map((fact, i) => (
          <FactRow key={i} fact={fact} mode={mode} />
        ))}
      </div>
    </>
  );
}
