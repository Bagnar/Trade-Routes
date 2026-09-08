"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import type { CountryRef, Mode } from "@/lib/page-content";

export interface OpenPage {
  hs6: string;
  name: string;
  hsLabel: string;
  href: string;
}

export interface OpenCorridor {
  id: string;
  from: string;
  to: string;
  pages: OpenPage[];
}

/**
 * Start page query: "Везу [товар] из [страны] в [страну] как [режим]". Routes to an assembled page when one
 * exists; otherwise says honestly that the corridor or the product page is not open yet.
 */
export function SearchForm({ countries, corridors }: { countries: CountryRef[]; corridors: OpenCorridor[] }) {
  const router = useRouter();
  const [product, setProduct] = useState(corridors[0]?.pages[0]?.name ?? "");
  const [from, setFrom] = useState(corridors[0]?.from ?? countries[0]?.code ?? "");
  const [to, setTo] = useState(corridors[0]?.to ?? countries[1]?.code ?? "");
  const [mode, setMode] = useState<Mode>("b2b");
  const [miss, setMiss] = useState<React.ReactNode>(null);

  const allProducts = corridors.flatMap((c) => c.pages);

  function findPage(corridor: OpenCorridor): OpenPage | undefined {
    const q = product.trim().toLowerCase();
    const digits = q.replace(/\D/g, "");
    return (
      corridor.pages.find((p) => digits.length >= 4 && p.hs6.startsWith(digits.slice(0, 6))) ??
      corridor.pages.find((p) => p.name.toLowerCase() === q) ??
      corridor.pages.find((p) => q.length >= 3 && (p.name.toLowerCase().includes(q) || q.includes(p.name.toLowerCase())))
    );
  }

  function go(anchor: string) {
    const fromName = countries.find((c) => c.code === from)?.from ?? from;
    const toName = countries.find((c) => c.code === to)?.to ?? to;
    const corridor = corridors.find((c) => c.from === from && c.to === to);
    if (!corridor) {
      setMiss(
        `Коридор «${fromName} → ${toName}» ещё не открыт. Страница соберётся из официальных источников по запросу; оставьте email в карточке ниже, и мы сообщим, когда она будет готова.`,
      );
      return;
    }
    const page = findPage(corridor);
    if (!page) {
      setMiss(
        <>
          Для «{product || "этого товара"}» в коридоре «{fromName} → {toName}» страница ещё не собрана. Открыты:{" "}
          {corridor.pages.map((p, i) => (
            <span key={p.hs6}>
              {i > 0 && ", "}
              <Link href={p.href}>
                {p.name} ({p.hsLabel})
              </Link>
            </span>
          ))}
          .
        </>,
      );
      return;
    }
    setMiss(null);
    router.push(`${page.href}${mode === "parcel" ? "?mode=parcel" : ""}${anchor}`);
  }

  return (
    <div className="search">
      <div className="query" role="group" aria-label="Параметры коридора">
        Везу{" "}
        <input
          className="product"
          list="products"
          placeholder="товар или код HS"
          aria-label="Товар"
          value={product}
          onChange={(e) => setProduct(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && go("")}
        />
        <datalist id="products">
          {allProducts.map((p) => (
            <option key={`${p.href}`} value={p.name}>
              {p.hsLabel}
            </option>
          ))}
        </datalist>{" "}
        из{" "}
        <select className="country" aria-label="Откуда" value={from} onChange={(e) => setFrom(e.target.value)}>
          {countries.map((c) => (
            <option key={c.code} value={c.code}>
              {c.from}
            </option>
          ))}
        </select>{" "}
        в{" "}
        <select className="country" aria-label="Куда" value={to} onChange={(e) => setTo(e.target.value)}>
          {countries.map((c) => (
            <option key={c.code} value={c.code}>
              {c.to}
            </option>
          ))}
        </select>{" "}
        как{" "}
        <span className="mode" role="group" aria-label="Режим поставки">
          <button type="button" data-mode="b2b" aria-pressed={mode === "b2b"} onClick={() => setMode("b2b")}>
            коммерческую партию
          </button>
          <button type="button" data-mode="parcel" aria-pressed={mode === "parcel"} onClick={() => setMode("parcel")}>
            посылки покупателям
          </button>
        </span>
      </div>
      <div className="go">
        <button type="button" onClick={() => go("")}>
          Показать коридор
        </button>
        <span className="alt">
          или сразу:{" "}
          <a
            href="#"
            onClick={(e) => {
              e.preventDefault();
              go("#sw");
            }}
          >
            куда выгоднее везти этот товар
          </a>
        </span>
      </div>
      <div className="miss" hidden={miss === null}>
        {miss}
      </div>
    </div>
  );
}

/** "Следующий коридор — ваш": request form. Stage 0: nothing is stored yet, and the card says so. */
export function RequestCorridorCard() {
  const [sent, setSent] = useState(false);
  return (
    <article className="card soon">
      <p className="route">Следующий коридор — ваш</p>
      <p className="prod">
        новые коридоры открываются по запросам: страница собирается из источников, когда её спросили
      </p>
      <input placeholder="товар, откуда, куда" aria-label="Запрос коридора" />
      <input placeholder="email — сообщим, когда откроем" aria-label="Email" type="email" />
      <p className="open">
        {sent ? (
          "Запрос принят (демо: заявки пока не сохраняются)"
        ) : (
          <a
            href="#"
            onClick={(e) => {
              e.preventDefault();
              setSent(true);
            }}
          >
            Запросить коридор
          </a>
        )}
      </p>
    </article>
  );
}
