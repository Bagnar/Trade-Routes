import Link from "next/link";
import { DemoBand } from "@/components/Bands";
import { RequestCorridorCard, SearchForm, type OpenCorridor } from "@/components/SearchForm";
import { SiteFooter, SiteHeader } from "@/components/SiteHeader";
import { listCorridors } from "@/lib/corridors";
import { COUNTRIES } from "@/lib/countries";
import { getPage, listPages } from "@/lib/pages";
import { pageHref } from "@/lib/routes";
import type { VerdictItem } from "@/lib/page-content";

/** Picks the three lines the corridor card shows: one benefit, one prohibition/sanction, one obstacle. */
function cardLines(pros: VerdictItem[], cons: VerdictItem[]): VerdictItem[] {
  const pro = pros.find((p) => p.kind === "pro");
  const ban = cons.find((c) => c.kind === "con-ban");
  const con = cons.find((c) => c.kind === "con");
  return [pro, ban, con].filter((x): x is VerdictItem => Boolean(x));
}

export default async function Home() {
  const [corridors, pages] = await Promise.all([listCorridors(), listPages()]);
  const ruPages = pages.filter((p) => p.lang === "ru");

  const open: OpenCorridor[] = corridors
    .map((c) => ({
      id: c.id,
      from: c.from,
      to: c.to,
      pages: ruPages
        .filter((p) => p.corridorId === c.id)
        .map((p) => ({ hs6: p.hs6, name: p.product.name, hsLabel: p.product.hsLabel, href: pageHref(c.id, p.hs6) })),
    }))
    .filter((c) => c.pages.length > 0);

  const cards = await Promise.all(
    open.map(async (c) => {
      const first = c.pages[0];
      const page = await getPage(c.id, first.hs6);
      return { corridor: c, page };
    }),
  );

  const anyDemo = ruPages.some((p) => p.isDemo);

  return (
    <>
      <SiteHeader languages={["ru", "en", "zh", "fa"]} current="ru" />

      {anyDemo && (
        <DemoBand>
          <strong>Демо-данные.</strong> Открыты два коридора на демонстрационных данных; остальные сочетания стран
          показывают, как сайт отвечает, когда страницы ещё нет.
        </DemoBand>
      )}

      <section className="hero">
        <h1>Правила торговли между любыми странами — одной страницей</h1>
        <p className="sub">
          Пошлины и налоги с обеих сторон границы, документы, санкции, господдержка и субсидии за маршрут — из
          официальных источников, с датой проверки у каждой строки. И оценка: выгодно ли, и куда выгоднее.
        </p>
        <SearchForm countries={Object.values(COUNTRIES)} corridors={open} />
      </section>

      <section className="section">
        <h2>Открытые коридоры</h2>
        <div className="cards">
          {cards.map(({ corridor, page }) =>
            page ? (
              <article className="card" key={corridor.id}>
                <p className="route">
                  {page.corridor.from.name} → {page.corridor.to.name}
                </p>
                <p className="prod">
                  {page.product.name}, {page.product.hsLabel};{" "}
                  {page.corridor.modes.includes("parcel") ? "партия или посылки" : "партия"}
                </p>
                <span className={`st ${page.rating.verdictStatus}`} style={{ alignSelf: "flex-start" }}>
                  {page.rating.total} из {page.rating.of} — {page.rating.verdict}
                </span>
                <ul className="lines">
                  {cardLines(page.verdict.pros, page.verdict.cons).map((line, i) => (
                    <li key={i} className={line.kind}>
                      {line.text}
                    </li>
                  ))}
                </ul>
                <p className="open">
                  <Link href={pageHref(corridor.id, page.product.hs6)}>Открыть страницу коридора</Link>
                  {corridor.pages.length > 1 && (
                    <>
                      {" "}
                      · ещё {corridor.pages.length - 1}
                    </>
                  )}
                </p>
              </article>
            ) : null,
          )}
          <RequestCorridorCard />
        </div>
      </section>

      <section className="section">
        <h2>Как собираются страницы</h2>
        <div className="how">
          <div>
            <h3>Только официальные источники</h3>
            <p>
              Таможни, министерства торговли, экспортные агентства, налоговые и санкционные органы. Никаких блогов и
              сайтов перевозчиков.
            </p>
          </div>
          <div>
            <h3>Нет цитаты — нет утверждения</h3>
            <p>
              Каждый факт хранится вместе с фрагментом текста источника и ссылкой. Если источника нет, страница
              говорит об этом, а не заполняет пробел догадкой.
            </p>
          </div>
          <div>
            <h3>Дата и статус у каждой строки</h3>
            <p>
              Источники перечитываются регулярно. Старше 90 дней — «требует проверки». Подписка сообщает, когда
              что-то изменилось.
            </p>
          </div>
        </div>
        <p className="who">
          Для производителей, продавцов маркетплейсов, импортёров и логистов. Не юридическая консультация: код товара
          и ставки подтверждайте у брокера.
        </p>
      </section>

      <SiteFooter sanctionsPolicy />
    </>
  );
}
