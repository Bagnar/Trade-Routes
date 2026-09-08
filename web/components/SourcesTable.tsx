import type { PageContent } from "@/lib/page-content";
import { SectionHeading } from "./Section";

/** "Источники и проверка": every line above rests on one of these rows. */
export function SourcesTable({ sources }: { sources: PageContent["sources"] }) {
  return (
    <>
      <SectionHeading id={sources.id} number={sources.number} title={sources.title} />
      <p className="lead">{sources.lead}</p>
      <div className="sources-wrap">
        <table className="sources">
          <thead>
            <tr>
              <th>Источник</th>
              <th>Что подтверждает</th>
              <th>Проверено</th>
              <th>Статус</th>
            </tr>
          </thead>
          <tbody>
            {sources.rows.map((row, i) => (
              <tr key={i}>
                <td>{row.source}</td>
                <td>{row.confirms}</td>
                <td>{row.checked}</td>
                <td>
                  <span className={`st ${row.status.kind}`}>{row.status.text}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
