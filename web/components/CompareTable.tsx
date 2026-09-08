import type { PageContent } from "@/lib/page-content";

/** "Куда ещё везти этот товар": destinations from the index layer, sorted by score. */
export function CompareTable({ compare }: { compare: PageContent["compare"] }) {
  return (
    <>
      <h2 id={compare.id}>{compare.title}</h2>
      <p className="lead">{compare.lead}</p>
      <div className="compare-wrap">
        <table className="compare">
          <thead>
            <tr>
              <th>Куда</th>
              <th>Пошлина</th>
              <th>Соглашение</th>
              <th>Санкции</th>
              <th>Поддержка</th>
              <th>Оценка</th>
            </tr>
          </thead>
          <tbody>
            {compare.rows.map((row) => (
              <tr key={row.to} className={row.here ? "here" : undefined}>
                <td>{row.to}</td>
                <td>{row.duty}</td>
                <td>{row.agreement}</td>
                <td>{row.sanctions}</td>
                <td>{row.support}</td>
                <td>
                  <span className={`st ${row.score.status}`}>{row.score.text}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
