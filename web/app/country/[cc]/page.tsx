import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { SiteFooter, SiteHeader } from "@/components/SiteHeader";
import { country } from "@/lib/countries";
import { listFactsFiles } from "@/lib/facts";
import { listPages } from "@/lib/pages";
import { agreementsInfo, loadRegistry, ratesInfo, type RegistrySource } from "@/lib/registry";
import { countryHref, pageHref } from "@/lib/routes";
import { topicLabel } from "@/lib/topics";

type Params = { cc: string };

export async function generateStaticParams(): Promise<Params[]> {
  const registry = await loadRegistry();
  return [...Object.keys(registry.countries), ...Object.keys(registry.blocs)].map((code) => ({ cc: code.toLowerCase() }));
}

export async function generateMetadata({ params }: { params: Promise<Params> }): Promise<Metadata> {
  const { cc } = await params;
  const registry = await loadRegistry();
  const code = cc.toUpperCase();
  const entry = registry.countries[code] ?? registry.blocs[code];
  return { title: entry ? `${entry.name.ru}: законы и органы` : "Страна не найдена" };
}

function ruDate(iso: string): string {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleDateString("ru-RU", { day: "numeric", month: "short", year: "numeric" });
}

const STATUS: Record<string, { text: string; kind: "ok" | "warn" | "none" }> = {
  verified: { text: "проверен вручную", kind: "ok" },
  to_verify: { text: "внесён, не проверен", kind: "warn" },
  unstable: { text: "доступен нестабильно", kind: "warn" },
};

function SourceRows({ sources, factsBySource, fetched }: { sources: RegistrySource[]; factsBySource: Map<string, number>; fetched: Map<string, string> }) {
  return (
    <>
      {sources.map((s) => (
        <tr key={s.id}>
          <td>
            <a href={`https://${s.domain}${s.path_prefix ?? ""}`} target="_blank" rel="noopener noreferrer">
              {s.domain}
              {s.path_prefix ?? ""}
            </a>
          </td>
          <td>
            {s.agency}
            {s.urls.length > 0 && (
              <ul style={{ margin: "4px 0 0", paddingLeft: 18 }}>
                {s.urls.map((u) => (
                  <li key={u.url}>
                    <a href={u.url} target="_blank" rel="noopener noreferrer">
                      {u.topic ? topicLabel(u.topic) : u.url}
                    </a>
                    {fetched.has(u.url) ? ` — перечитано ${ruDate(fetched.get(u.url)!)}` : " — ещё не перечитано"}
                  </li>
                ))}
              </ul>
            )}
          </td>
          <td>{s.topics.map(topicLabel).join(", ")}</td>
          <td>
            <span className={`st ${(STATUS[s.status] ?? STATUS.to_verify).kind}`}>{(STATUS[s.status] ?? STATUS.to_verify).text}</span>
          </td>
          <td>{factsBySource.get(s.id) ?? 0}</td>
        </tr>
      ))}
    </>
  );
}

/**
 * "Законы и органы": the country's official sources from the registry with what the pipeline has read from
 * them, third-country sanctions programs that name the country, export-control authorities, loaded rates and
 * open corridors. Nothing here is generated: it is the registry and the pipeline's own bookkeeping.
 */
export default async function CountryPage({ params }: { params: Promise<Params> }) {
  const { cc } = await params;
  const code = cc.toUpperCase();
  const [registry, facts, pages, rates, agreements] = await Promise.all([loadRegistry(), listFactsFiles(), listPages(), ratesInfo(code), agreementsInfo()]);
  const entry = registry.countries[code] ?? registry.blocs[code];
  if (!entry) notFound();
  const isBloc = Boolean(registry.blocs[code]);
  const ref = isBloc ? { code, name: entry.name.ru, from: `из ${entry.name.ru}`, to: `в ${entry.name.ru}`, loc: `в ${entry.name.ru}` } : country(code);

  const factsBySource = new Map<string, number>();
  const fetched = new Map<string, string>();
  for (const f of facts) {
    factsBySource.set(f.source_id, (factsBySource.get(f.source_id) ?? 0) + f.facts.length);
    fetched.set(f.url, f.fetched_at);
  }
  const blocs = Object.values(registry.blocs).filter((b) => b.members?.includes(code));
  const ownFacts = [...entry.sources, ...blocs.flatMap((b) => b.sources)].reduce((n, s) => n + (factsBySource.get(s.id) ?? 0), 0);
  const sanctionsAgainst = registry.sanctions.flatMap((a) => a.urls.filter((u) => u.targets?.includes(code)).map((u) => ({ authority: a, url: u })));
  const sanctionsOwn = registry.sanctions.filter((a) => a.jurisdiction === code);
  const exportControl = registry.exportControl.filter((a) => a.jurisdiction === code || a.jurisdiction === "INT");
  const corridors = pages.filter((p) => p.lang === "ru" && (p.corridor.from.code === code || p.corridor.to.code === code));
  const ownAgreements = agreements?.agreements.filter((a) => a.members.includes(code)) ?? null;

  return (
    <>
      <SiteHeader languages={["ru"]} current="ru" linkHome />
      <div className="band status">
        <div className="in">
          В реестре {entry.sources.length} источников ({entry.sources.filter((s) => s.status === "verified").length} проверены вручную), фактов с дословной
          цитатой: {ownFacts}. Ставки MFN по HS-6: {rates ? `загружены (${rates.count} групп, ${rates.year} год, снимок ${ruDate(rates.fetchedAt)})` : "не загружены"}.
          Это не юридическая консультация.
        </div>
      </div>
      <section className="hero">
        <h1>{entry.name.ru}: законы и органы</h1>
        <p className="sub">
          Официальные органы и базы законов, из которых собираются страницы коридоров {ref.from} и {ref.to}. Каждая
          ссылка ведёт на первоисточник; статус показывает, подтверждена ли роль сайта вручную и что уже перечитано
          конвейером.
        </p>
      </section>

      <section className="section">
        <h2>Органы и источники</h2>
        <p className="lead">Белый список для {isBloc ? "наднациональных" : "национальных"} правил: таможня, министерства, налоговые органы, базы законов, поддержка экспорта.</p>
        <div className="sources-wrap">
          <table className="sources">
            <thead>
              <tr>
                <th>Сайт</th>
                <th>Орган и страницы</th>
                <th>Темы</th>
                <th>Статус в реестре</th>
                <th>Фактов</th>
              </tr>
            </thead>
            <tbody>
              <SourceRows sources={entry.sources} factsBySource={factsBySource} fetched={fetched} />
            </tbody>
          </table>
        </div>
        {isBloc && entry.members && (
          <p className="hint">
            Применяется к странам: {entry.members.map((m) => country(m).name).join(", ")}.
          </p>
        )}
      </section>

      {blocs.length > 0 && (
        <section className="section">
          <h2>Наднациональные источники</h2>
          <p className="lead">Правила, общие для всех членов объединения, — там же, где национальные.</p>
          {blocs.map((b) => (
            <div key={b.code} className="sources-wrap">
              <p className="hint">
                <Link href={countryHref(b.code)}>{b.name.ru}</Link>
              </p>
              <table className="sources">
                <tbody>
                  <SourceRows sources={b.sources} factsBySource={factsBySource} fetched={fetched} />
                </tbody>
              </table>
            </div>
          ))}
        </section>
      )}

      <section className="section">
        <h2>Ставки и соглашения</h2>
        <div className="facts">
          <div className="fact">
            <p>
              {rates
                ? `Пошлины по режиму наибольшего благоприятствования при ввозе ${ref.to}: ${rates.count} групп HS-6 за ${rates.year} год из базы ${rates.source}. На страницах коридоров эти ставки показываются с печатью «таблица ставок».`
                : `Ставки MFN при ввозе ${ref.to} ещё не загружены в таблицу ставок: на страницах коридоров пошлина помечена «ставка не загружена».`}
            </p>
            <span className={`stamp ${rates ? "ok" : "none"}`}>
              <b>{rates ? "wits.worldbank.org" : "таблица rates"}</b>
              {rates ? `снимок ${ruDate(rates.fetchedAt)}` : "не загружено"}
            </span>
          </div>
          <div className="fact">
            <p>
              {ownAgreements === null
                ? "База региональных торговых соглашений ВТО (RTA-IS) ещё не загружена: на страницах коридоров соглашение помечено «не проверено»."
                : ownAgreements.length === 0
                  ? `В базе РТС ВТО нет действующих соглашений с участием этой страны.`
                  : `Действующие соглашения с участием страны по базе РТС ВТО (${ownAgreements.length}): ${ownAgreements
                      .slice(0, 12)
                      .map((a) => `${a.name}${a.in_force ? ` (с ${a.in_force})` : ""}`)
                      .join("; ")}${ownAgreements.length > 12 ? " и другие" : ""}.`}
            </p>
            <span className={`stamp ${agreements ? "ok" : "none"}`}>
              <b>rtais.wto.org</b>
              {agreements ? `снимок ${ruDate(agreements.fetchedAt)}` : "не загружено"}
            </span>
          </div>
        </div>
      </section>

      <section className="section">
        <h2>Санкционные режимы</h2>
        <p className="lead">
          Показываются как есть: какие органы третьих стран ведут программы в отношении страны и перечитаны ли их
          страницы. Ничего о том, как обойти ограничения, на сайте нет.
        </p>
        {sanctionsAgainst.length === 0 ? (
          <p className="hint">В реестре нет страниц санкционных программ, которые называют эту страну. Это не означает отсутствия санкций — полный список режимов не проверен.</p>
        ) : (
          <div className="facts">
            {sanctionsAgainst.map(({ authority, url }) => (
              <div className="fact" key={url.url}>
                <p>
                  {authority.agency} —{" "}
                  <a href={url.url} target="_blank" rel="noopener noreferrer">
                    страница программы
                  </a>
                </p>
                <span className={`stamp ${fetched.has(url.url) ? "ok" : "none"}`}>
                  <b>{authority.domain}</b>
                  {fetched.has(url.url) ? `перечитано ${ruDate(fetched.get(url.url)!)}` : "ещё не перечитано"}
                </span>
              </div>
            ))}
          </div>
        )}
        {sanctionsOwn.length > 0 && (
          <p className="hint">Собственные санкционные органы страны: {sanctionsOwn.map((a) => `${a.agency} (${a.domain})`).join("; ")}.</p>
        )}
      </section>

      {exportControl.length > 0 && (
        <section className="section">
          <h2>Экспортный контроль и двойное назначение</h2>
          <p className="lead">Органы, публикующие контрольные списки. Принадлежность конкретного товара к спискам — по национальному коду у брокера.</p>
          <div className="sources-wrap">
            <table className="sources">
              <tbody>
                <SourceRows sources={exportControl} factsBySource={factsBySource} fetched={fetched} />
              </tbody>
            </table>
          </div>
        </section>
      )}

      <section className="section">
        <h2>Открытые коридоры</h2>
        {corridors.length === 0 ? (
          <p className="hint">Страниц коридоров с участием этой страны пока нет — их можно запросить с главной страницы.</p>
        ) : (
          <ul className="links">
            {corridors.map((p) => (
              <li key={`${p.corridorId}-${p.hs6}`}>
                <Link href={pageHref(p.corridorId, p.hs6)}>
                  {p.product.name[0].toUpperCase() + p.product.name.slice(1)} {p.corridor.from.from} {p.corridor.to.to}
                </Link>
                {p.isDemo ? " (демо)" : ""}
              </li>
            ))}
          </ul>
        )}
        <p className="hint">
          Всё, что конвейер извлёк из источников этой и других стран, с цитатами — <Link href="/facts">на странице фактов</Link>. Все страны —{" "}
          <Link href="/country">списком</Link>.
        </p>
      </section>
      <SiteFooter />
    </>
  );
}
