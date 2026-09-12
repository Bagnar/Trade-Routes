import type { Metadata } from "next";
import Link from "next/link";
import { DemoBand } from "@/components/Bands";
import { BuySearch, type BuyOption } from "@/components/BuySearch";
import { SiteFooter, SiteHeader } from "@/components/SiteHeader";
import { countryList } from "@/lib/countries";
import { supplyHref } from "@/lib/routes";
import { listSupplyPages } from "@/lib/supply";

export const metadata: Metadata = { title: "Где купить — регионы производства по странам" };

export default async function WhereToBuy() {
  const pages = (await listSupplyPages()).filter((p) => p.lang === "ru");
  const options: BuyOption[] = pages.map((p) => ({
    country: p.country.code,
    hs: p.hs,
    name: p.product.name,
    hsLabel: p.product.hsLabel,
    href: supplyHref(p.country.code, p.hs),
  }));

  return (
    <>
      <SiteHeader languages={["ru"]} current="ru" linkHome />
      {pages.some((p) => p.isDemo) && (
        <DemoBand>
          <strong>Демо-данные.</strong> Страницы «где купить» показывают формат; регионы ещё не подтверждены
          конвейером по источникам.
        </DemoBand>
      )}
      <section className="hero">
        <h1>Где купить: регионы производства по странам</h1>
        <p className="sub">
          В каких провинциях и кластерах страны производят товар и через какие официальные реестры, выставки и
          агентства искать поставщика. Только регионы и государственные источники — без списков компаний.
        </p>
        <BuySearch countries={countryList()} options={options} />
      </section>
      <section className="section">
        <h2>Открытые страницы</h2>
        <div className="cards">
          {pages.map((p) => (
            <article className="card" key={`${p.country.code}-${p.hs}`}>
              <p className="route">
                {p.product.name[0].toUpperCase() + p.product.name.slice(1)} {p.country.loc ?? p.country.name}
              </p>
              <p className="prod">
                {p.product.hsLabel}; регионов: {p.regionCount} — {p.topRegions.join(", ")}
              </p>
              <p className="open">
                <Link href={supplyHref(p.country.code, p.hs)}>Открыть страницу</Link>
              </p>
            </article>
          ))}
        </div>
      </section>
      <SiteFooter />
    </>
  );
}
