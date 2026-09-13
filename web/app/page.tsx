import Link from "next/link";
import { DemoBand } from "@/components/Bands";
import { BuySearch, type BuyOption } from "@/components/BuySearch";
import { RequestCorridorCard, SearchForm, type OpenCorridor } from "@/components/SearchForm";
import { SiteFooter, SiteHeader } from "@/components/SiteHeader";
import { listCorridors } from "@/lib/corridors";
import { countryList } from "@/lib/countries";
import type { Fact, PageContent } from "@/lib/page-content";
import { getPage, listPages } from "@/lib/pages";
import { pageHref, supplyHref } from "@/lib/routes";
import { ruDate, siteStats } from "@/lib/stats";
import { listSupplyPages } from "@/lib/supply";
import { modeText } from "@/lib/text";

function factText(fact: Fact | undefined): string {
  return fact ? (modeText(fact.text, "b2b") ?? "") : "";
}

/** Real lines from assembled pages for the "what you get" blocks — never typed in by hand. */
async function examples(): Promise<{ duty?: Fact; demand?: Fact; sanctions?: PageContent["sanctions"]; rating?: PageContent["rating"]; ref?: PageContent }> {
  const [cnca, ruir] = await Promise.all([getPage("cn-ca", "610910"), getPage("ru-ir", "100199")]);
  return {
    duty: cnca?.summary.facts.find((f) => f.key === "Пошлина при ввозе" && f.rate_ref),
    demand: cnca?.summary.facts.find((f) => f.key === "Спрос"),
    sanctions: ruir?.sanctions,
    rating: cnca?.rating,
    ref: cnca ?? undefined,
  };
}

export default async function Home() {
  const [corridors, pages, supplyPages, stats, ex] = await Promise.all([listCorridors(), listPages(), listSupplyPages(), siteStats(), examples()]);
  const buyOptions: BuyOption[] = supplyPages
    .filter((p) => p.lang === "ru")
    .map((p) => ({ country: p.country.code, hs: p.hs, name: p.product.name, hsLabel: p.product.hsLabel, href: supplyHref(p.country.code, p.hs) }));
  const ruPages = pages.filter((p) => p.lang === "ru");
  const open: OpenCorridor[] = corridors
    .map((c) => ({
      id: c.id,
      from: c.from,
      to: c.to,
      pages: ruPages.filter((p) => p.corridorId === c.id).map((p) => ({ hs6: p.hs6, name: p.product.name, hsLabel: p.product.hsLabel, href: pageHref(c.id, p.hs6) })),
    }))
    .filter((c) => c.pages.length > 0);
  const cards = await Promise.all(open.map(async (c) => ({ corridor: c, page: await getPage(c.id, c.pages[0].hs6) })));
  const anyDemo = ruPages.some((p) => p.isDemo);
  const scored = ex.rating ? ex.rating.parts.filter((p) => p.score !== null).length : 0;

  return (
    <>
      <SiteHeader languages={["ru", "en", "zh", "fa"]} current="ru" />

      {anyDemo && (
        <DemoBand>
          <strong>Сайт наполняется.</strong> Строки с зелёной печатью взяты из официальных источников с цитатой; строки с плашкой «демо»
          показывают формат и будут заменены по мере проверки источников.
        </DemoBand>
      )}

      <section className="hero">
        <h1>Правила торговли между любыми странами одной страницей</h1>
        <p className="sub">
          Пошлины и налоги с обеих сторон границы, санкции, документы, господдержка и оценка «выгодно ли» из официальных источников,
          с датой проверки у каждой строки.
        </p>
        <SearchForm countries={countryList()} corridors={open} />
      </section>

      <div className="stats" aria-label="Что уже есть на сайте">
        <div>
          <b>{stats.countries}</b>
          <span>стран в поиске</span>
        </div>
        <div>
          <b>{stats.hs6.toLocaleString("ru-RU")}</b>
          <span>товарных групп HS‑6, названия на русском</span>
        </div>
        <div>
          <b>{stats.facts}</b>
          <span>фактов с дословной цитатой из {stats.sourcesRead} официальных страниц</span>
        </div>
        <div>
          <b>{stats.ratesCountries}</b>
          <span>стран со ставками пошлин по каждой группе</span>
        </div>
        <div>
          <b>{stats.agreements}</b>
          <span>торговых соглашений в базе ВТО</span>
        </div>
        <div>
          <b>{stats.lastChecked ? ruDate(stats.lastChecked) : "—"}</b>
          <span>последняя проверка источников</span>
        </div>
      </div>

      <section className="section">
        <h2>Что вы получите на странице коридора</h2>
        <p className="lead">Примеры ниже взяты со страницы «Футболки из Китая в Канаду» и «Пшеница из России в Иран» в том виде, в каком они там стоят.</p>
        <div className="get">
          <article>
            <h3>Пошлина из таблицы, не из головы</h3>
            <p>Ставка ввоза берётся из официальной базы ставок по коду HS‑6 и показывается с годом данных и ссылкой на таблицу.</p>
            {ex.duty ? <p className="ex">{factText(ex.duty)}</p> : <p className="ex note">Ставки загружаются загрузчиком справочников.</p>}
          </article>
          <article>
            <h3>Оценка из пяти частей</h3>
            <p>Пошлины, препятствия, господдержка считаются по правилам из источников; спрос и логистика всегда помечены как ориентир.</p>
            {ex.rating ? (
              <p className="ex note">
                {ex.rating.total} из {ex.rating.of}: {ex.rating.verdict}. Оценено частей: {scored} из 5, у остальных честно «нет основания».
              </p>
            ) : null}
          </article>
          <article>
            <h3>Санкции как есть</h3>
            <p>Для пар под ограничениями показано, что именно ограничено и по какому документу. Советов «как обойти» на сайте нет.</p>
            {ex.sanctions ? <p className="ex ban">{ex.sanctions.text.slice(0, 220)}…</p> : null}
          </article>
          <article>
            <h3>Спрос по торговой статистике</h3>
            <p>Сколько страна ввозит этой группы и растёт ли ввоз, по данным UN Comtrade за последний доступный год.</p>
            {ex.demand ? <p className="ex note">{factText(ex.demand)}</p> : <p className="ex note">Статистика подключается загрузчиком справочников.</p>}
          </article>
        </div>
        {ex.ref && (
          <p className="who">
            Посмотреть целиком: <Link href={pageHref(ex.ref.corridor.id, ex.ref.product.hs6)}>{ex.ref.product.name} {ex.ref.corridor.from.from} {ex.ref.corridor.to.to}</Link>.
          </p>
        )}
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
                  {corridor.pages.length} {corridor.pages.length === 1 ? "товарная группа" : corridor.pages.length < 5 ? "товарные группы" : "товарных групп"};{" "}
                  {page.corridor.modes.includes("parcel") ? "партия или посылки" : "партия"}
                </p>
                <span className={`st ${page.rating.verdictStatus}`} style={{ alignSelf: "flex-start" }}>
                  {page.product.name}: {page.rating.total} из {page.rating.of}
                </span>
                <p className="open">
                  <Link href={pageHref(corridor.id, page.product.hs6)}>Открыть страницу коридора</Link>
                </p>
              </article>
            ) : null,
          )}
          <RequestCorridorCard countries={countryList()} />
        </div>
      </section>

      <section className="section">
        <h2>Где купить: регионы производства</h2>
        <p className="lead">
          Второй вход: в каких провинциях и кластерах страны производят товар и через какие официальные реестры и выставки искать поставщика.
          Только регионы и государственные источники, без списков компаний.
        </p>
        <BuySearch countries={countryList()} options={buyOptions} />
        <p className="who">
          Все страницы «где купить» <Link href="/where-to-buy">отдельным списком</Link>.
        </p>
      </section>

      <section className="section">
        <h2>Как собираются страницы</h2>
        <div className="how">
          <div>
            <h3>Только официальные источники</h3>
            <p>Таможни, министерства, налоговые и санкционные органы, базы ООН и ВТО. Реестр источников открыт: <Link href="/country">по странам</Link>.</p>
          </div>
          <div>
            <h3>Нет цитаты, нет утверждения</h3>
            <p>Каждый факт хранится с фрагментом текста источника и ссылкой. Все извлечённые факты: <Link href="/facts">на одной странице</Link>.</p>
          </div>
          <div>
            <h3>Проверка каждый день</h3>
            <p>Источники перечитываются ночью. Если цитата исчезла, строка помечается «требует проверки», а не остаётся зелёной.</p>
          </div>
        </div>
        <h2>Чего здесь нет</h2>
        <ul className="honest">
          <li>Юридической, таможенной или налоговой консультации: код и ставки подтверждаются у брокера.</li>
          <li>Классификации точнее шести знаков HS: национальную подстроку сайт не выбирает.</li>
          <li>Советов, как обойти санкции или проверки: ограничения показываются как есть.</li>
          <li>Проверенного спроса и логистики: эти части оценки всегда ориентир.</li>
        </ul>
        <p className="who">
          Условия использования и отказ от ответственности: <Link href="/terms">читать</Link>. Замечание к любой странице: ссылка «Сообщить о неточности» внизу.
        </p>
      </section>

      <SiteFooter sanctionsPolicy />
    </>
  );
}
