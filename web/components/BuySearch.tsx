"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import type { CountryRef } from "@/lib/page-content";

export interface BuyOption {
  country: string;
  hs: string;
  name: string;
  hsLabel: string;
  href: string;
}

/** "Покупаю [товар] в [стране]" — entry to the "where to buy" layer. */
export function BuySearch({ countries, options }: { countries: CountryRef[]; options: BuyOption[] }) {
  const router = useRouter();
  const [product, setProduct] = useState(options[0]?.name ?? "");
  const [country, setCountry] = useState(options[0]?.country ?? countries[0]?.code ?? "");
  const [miss, setMiss] = useState<React.ReactNode>(null);

  function go() {
    const q = product.trim().toLowerCase();
    const digits = q.replace(/\D/g, "");
    const inCountry = options.filter((o) => o.country === country);
    const found =
      inCountry.find((o) => digits.length >= 4 && digits.startsWith(o.hs)) ??
      inCountry.find((o) => o.name.toLowerCase() === q) ??
      inCountry.find((o) => q.length >= 3 && (o.name.toLowerCase().includes(q) || q.includes(o.name.toLowerCase())));
    const loc = countries.find((c) => c.code === country)?.loc ?? country;
    if (found) {
      setMiss(null);
      router.push(found.href);
      return;
    }
    setMiss(
      inCountry.length ? (
        <>
          Для «{product || "этого товара"}» в {loc} страница ещё не собрана. Открыты:{" "}
          {inCountry.map((o, i) => (
            <span key={o.href}>
              {i > 0 && ", "}
              <Link href={o.href}>
                {o.name} ({o.hsLabel})
              </Link>
            </span>
          ))}
          .
        </>
      ) : (
        `Для страны «${loc}» слой «где купить» ещё не собран. Страница собирается из официальной статистики и реестров по запросу.`
      ),
    );
  }

  return (
    <div className="search">
      <div className="query" role="group" aria-label="Параметры запроса">
        Покупаю{" "}
        <input
          className="product"
          list="buy-products"
          placeholder="товар или код HS"
          aria-label="Товар"
          value={product}
          onChange={(e) => setProduct(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && go()}
        />
        <datalist id="buy-products">
          {options.map((o) => (
            <option key={o.href} value={o.name}>
              {o.hsLabel}
            </option>
          ))}
        </datalist>{" "}
        в{" "}
        <select className="country" aria-label="Страна" value={country} onChange={(e) => setCountry(e.target.value)}>
          {countries.map((c) => (
            <option key={c.code} value={c.code}>
              {c.loc ?? c.name}
            </option>
          ))}
        </select>
      </div>
      <div className="go">
        <button type="button" onClick={go}>
          Показать регионы
        </button>
        <span className="alt">регионы и кластеры производства, официальные реестры и выставки</span>
      </div>
      <div className="miss" hidden={miss === null}>
        {miss}
      </div>
    </div>
  );
}
