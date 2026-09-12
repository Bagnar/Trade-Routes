import type { Mode, PageContent, VerdictItem } from "@/lib/page-content";
import { visibleInMode } from "@/lib/text";

/** Five-part score card. A part without a basis shows no score (docs/concept.md, section 5). */
export function RatingCard({ rating }: { rating: PageContent["rating"] }) {
  const noBasis = rating.parts.every((p) => p.score === null);
  return (
    <>
      <h2 id={rating.id}>{rating.title}</h2>
      <p className="lead">{rating.lead}</p>
      <div className="rating">
        <div className="rating-head">
          <div className="rating-total">
            <span className="big">{noBasis ? "—" : rating.total}</span>
            <span className="of">из {rating.of}</span>
          </div>
          <div className="rating-verdict">
            <span className={`st ${rating.verdictStatus}`}>{rating.verdict}</span>
            <p>{rating.explanation}</p>
          </div>
        </div>
        <ul className="parts">
          {rating.parts.map((part) => (
            <li key={part.name}>
              <span className="pname">{part.name}</span>
              <span className="bar">
                <i style={{ width: part.score === null ? "0%" : `${(part.score / 5) * 100}%` }} />
              </span>
              <span className="pscore">{part.score === null ? "нет основания" : `${part.score} из 5`}</span>
              <span className="pnote">{part.basis}</span>
            </li>
          ))}
        </ul>
      </div>
    </>
  );
}

function VerdictList({ items, mode }: { items: VerdictItem[]; mode: Mode }) {
  return (
    <ul className="vlist">
      {items
        .filter((item) => visibleInMode(item.modes, mode))
        .map((item, i) => (
          <li key={i} className={item.kind}>
            {item.text}
          </li>
        ))}
    </ul>
  );
}

/** "Выгодно" (green) and "Мешает" (red = prohibition, yellow = obstacle) lists. */
export function ProsCons({ verdict, mode }: { verdict: PageContent["verdict"]; mode: Mode }) {
  return (
    <div className="verdict">
      <div>
        <h3>{verdict.prosTitle}</h3>
        <VerdictList items={verdict.pros} mode={mode} />
      </div>
      <div>
        <h3>{verdict.consTitle}</h3>
        <VerdictList items={verdict.cons} mode={mode} />
      </div>
    </div>
  );
}
