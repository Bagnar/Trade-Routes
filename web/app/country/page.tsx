import type { Metadata } from "next";
import Link from "next/link";
import { SiteFooter, SiteHeader } from "@/components/SiteHeader";
import { country } from "@/lib/countries";
import { listFactsFiles } from "@/lib/facts";
import { loadRegistry, ratesInfo } from "@/lib/registry";
import { countryHref } from "@/lib/routes";

export const metadata: Metadata = { title: "Законы и органы по странам" };

/** Index of the "laws and bodies" pages: every country and bloc with a source registry. */
export default async function Countries() {
  const [registry, facts] = await Promise.all([loadRegistry(), listFactsFiles()]);
  const factsBySource = new Map<string, number>();
  for (const f of facts) factsBySource.set(f.source_id, (factsBySource.get(f.source_id) ?? 0) + f.facts.length);
  const rows = await Promise.all(
    Object.values(registry.countries).map(async (c) => ({
      code: c.code,
      name: country(c.code).name,
      sources: c.sources.length,
      verified: c.sources.filter((s) => s.status === "verified").length,
      facts: c.sources.reduce((n, s) => n + (factsBySource.get(s.id) ?? 0), 0),
      rates: await ratesInfo(c.code),
    })),
  );
  rows.sort((a, b) => b.facts - a.facts || b.sources - a.sources || a.name.localeCompare(b.name, "ru"));

  return (
    <>
      <SiteHeader languages={["ru"]} current="ru" linkHome />
      <section className="hero">
        <h1>Законы и органы по странам</h1>
        <p className="sub">
          Реестр официальных источников — таможни, министерства, налоговые и санкционные органы, базы законов. Это
          белый список конвейера: страницы коридоров собираются только из этих сайтов. Для каждой страны видно, что
          уже перечитано и сколько фактов извлечено.
        </p>
      </section>
      <section className="section">
        <h2>Страны с реестром источников</h2>
        <div className="sources-wrap">
          <table className="sources">
            <thead>
              <tr>
                <th>Страна</th>
                <th>Источников в реестре</th>
                <th>Проверено вручную</th>
                <th>Фактов с цитатой</th>
                <th>Ставки MFN по HS-6</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.code}>
                  <td>
                    <Link href={countryHref(r.code)}>{r.name}</Link>
                  </td>
                  <td>{r.sources}</td>
                  <td>{r.verified}</td>
                  <td>{r.facts}</td>
                  <td>{r.rates ? <span className="st ok">загружены, {r.rates.year} год</span> : <span className="st none">не загружены</span>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="hint">
          Наднациональные источники:{" "}
          {Object.values(registry.blocs).map((b, i) => (
            <span key={b.code}>
              {i > 0 && ", "}
              <Link href={countryHref(b.code)}>{b.name.ru}</Link> ({b.members?.length ?? 0} стран)
            </span>
          ))}
          . Для остальных стран реестра пока нет: страница коридора для них создаётся по запросу, а источники добавляет
          основатель проекта.
        </p>
      </section>
      <SiteFooter />
    </>
  );
}
