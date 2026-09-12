import Link from "next/link";
import type { SupplyContent } from "@/lib/supply-content";
import { DemoBand, StatusBand } from "./Bands";
import { Rail, type TocItem } from "./Rail";
import { Section, SectionHeading } from "./Section";
import { SiteFooter, SiteHeader } from "./SiteHeader";
import { SourceStamp } from "./SourceStamp";
import { SourcesTable } from "./SourcesTable";
import { Summary } from "./Summary";

/** "Where to buy" page (docs/where-to-buy.md): regions, official ways to find suppliers, checks, corridors. */
export function SupplyPage({ page }: { page: SupplyContent }) {
  const toc: TocItem[] = [
    { id: page.summary.id, title: page.summary.title },
    { id: page.regions.id, number: page.regions.number, title: page.regions.title },
    { id: page.find.id, number: page.find.number, title: page.find.title },
    { id: page.check.id, number: page.check.number, title: page.check.title },
    { id: page.corridors.id, number: page.corridors.number, title: "Куда везти" },
    { id: page.sources.id, number: page.sources.number, title: "Источники" },
  ];

  return (
    <>
      <SiteHeader languages={[page.lang]} current={page.lang} linkHome>
        <div className="query" role="group" aria-label="Параметры запроса">
          Покупаю{" "}
          <select className="product" aria-label="Товар" defaultValue={page.product.hs}>
            <option value={page.product.hs}>
              {page.product.name}, {page.product.hsLabel}
            </option>
            <option disabled>другие группы…</option>
          </select>{" "}
          в{" "}
          <select className="country" aria-label="Страна" defaultValue={page.country.code}>
            <option value={page.country.code}>{page.country.loc ?? page.country.name}</option>
            <option disabled>другие…</option>
          </select>
        </div>
      </SiteHeader>

      <StatusBand status={page.status} />
      {page.isDemo && (
        <DemoBand>
          <strong>Демо-данные.</strong> Регионы приведены как пример формата и ещё не подтверждены конвейером по
          источникам; показатели из статистики не загружены.
        </DemoBand>
      )}

      <div className="doc">
        <main>
          <Summary summary={page.summary} mode="b2b" />

          <SectionHeading id={page.regions.id} number={page.regions.number} title={page.regions.title} />
          <p className="lead">{page.regions.lead}</p>
          <div className="compare-wrap">
            <table className="compare regions">
              <thead>
                <tr>
                  <th>Регион</th>
                  <th>Что производят</th>
                  <th>Показатель</th>
                  <th>Источник</th>
                </tr>
              </thead>
              <tbody>
                {page.regions.rows.map((row) => (
                  <tr key={row.region}>
                    <td>
                      {row.region}
                      {row.code && <span className="code">{row.code}</span>}
                    </td>
                    <td>{row.note}</td>
                    <td>{row.indicator}</td>
                    <td>
                      <SourceStamp stamp={row.stamp} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <Section section={page.find} mode="b2b" />
          <Section section={page.check} mode="b2b" />

          <SectionHeading id={page.corridors.id} number={page.corridors.number} title={page.corridors.title} />
          <p className="lead">{page.corridors.lead}</p>
          <ul className="check links">
            {page.corridors.links.map((link) => (
              <li key={link.label}>
                {link.state === "open" ? (
                  <Link href={link.href}>{link.label}</Link>
                ) : (
                  <span className="dim">{link.label}</span>
                )}
              </li>
            ))}
          </ul>

          <SourcesTable sources={page.sources} />
        </main>
        <Rail toc={toc} rail={{ disclaimer: page.rail.disclaimer }} hideFollow />
      </div>

      <SiteFooter />
    </>
  );
}
