"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import type { CountryRef, Mode } from "@/lib/page-content";
import { assembledHref, requestCorridorUrl } from "@/lib/routes";
import { REPO_URL } from "@/lib/site";
import { ProductSearch, type ProductPick } from "./ProductSearch";

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
  const [pick, setPick] = useState<ProductPick | null>(null);
  const [from, setFrom] = useState(corridors[0]?.from ?? countries[0]?.code ?? "");
  const [to, setTo] = useState(corridors[0]?.to ?? countries[1]?.code ?? "");
  const [mode, setMode] = useState<Mode>("b2b");
  const [miss, setMiss] = useState<React.ReactNode>(null);

  function findPage(corridor: OpenCorridor): OpenPage | undefined {
    const q = product.trim().toLowerCase();
    const digits = pick ? pick.code : q.replace(/\D/g, "");
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
    const page = corridor ? findPage(corridor) : undefined;
    if (!page) {
      // No prebuilt page: assemble one in the browser from the structured data when the HS-6 code is known.
      const code = pick ? pick.code : product.replace(/\D/g, "").slice(0, 6);
      if (from !== to && /^\d{6}$/.test(code)) {
        setMiss(null);
        router.push(`${assembledHref(from, to, code, mode)}${anchor}`);
        return;
      }
      const url = requestCorridorUrl(REPO_URL, { product: pick ? `${pick.label}, ${pick.code}` : product, from, to, mode });
      setMiss(
        from === to ? (
          <>Выберите две разные страны: откуда везёте и куда.</>
        ) : (
          <>
            Чтобы собрать страницу «{fromName} → {toName}», выберите товар из подсказок (нужен код HS-6) или введите шестизначный код.
            Если группа не находится —{" "}
            <a href={url} target="_blank" rel="noopener noreferrer">
              запросите коридор
            </a>{" "}
            (откроется форма на GitHub).
          </>
        ),
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
        <ProductSearch
          id="q-product"
          value={product}
          onPick={(p, text) => {
            setPick(p);
            setProduct(text);
          }}
        />{" "}
        <select className="country" aria-label="Откуда" value={from} onChange={(e) => setFrom(e.target.value)}>
          {countries.map((c) => (
            <option key={c.code} value={c.code}>
              {c.from}
            </option>
          ))}
        </select>{" "}
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

/**
 * "Следующий коридор — ваш": the request goes to a prefilled GitHub issue; the pipeline reads the queue and
 * creates a blank page that the daily assembler fills from official sources (docs/expansion-plan.md, 1.9).
 */
export function RequestCorridorCard({ countries }: { countries: CountryRef[] }) {
  const [product, setProduct] = useState("");
  const [pick, setPick] = useState<ProductPick | null>(null);
  const [from, setFrom] = useState(countries[0]?.code ?? "");
  const [to, setTo] = useState(countries[1]?.code ?? "");
  const url = requestCorridorUrl(REPO_URL, { product: pick ? `${pick.label}, ${pick.code}` : product, from, to });
  return (
    <article className="card soon">
      <p className="route">Следующий коридор — ваш</p>
      <p className="prod">
        новые коридоры открываются по запросам: страница-заготовка создаётся из очереди запросов, а ежедневная
        проверка наполняет её фактами из официальных источников
      </p>
      <ProductSearch
        id="req-product"
        placeholder="товар или код HS"
        value={product}
        onPick={(p, text) => {
          setPick(p);
          setProduct(text);
        }}
      />
      <p style={{ margin: "6px 0 0" }}>
        <select className="country" aria-label="Откуда" value={from} onChange={(e) => setFrom(e.target.value)}>
          {countries.map((c) => (
            <option key={c.code} value={c.code}>
              {c.from}
            </option>
          ))}
        </select>{" "}
        <select className="country" aria-label="Куда" value={to} onChange={(e) => setTo(e.target.value)}>
          {countries.map((c) => (
            <option key={c.code} value={c.code}>
              {c.to}
            </option>
          ))}
        </select>
      </p>
      <p className="open">
        <a href={url} target="_blank" rel="noopener noreferrer">
          Запросить коридор
        </a>{" "}
        <span className="hint">— откроется форма на GitHub (нужен аккаунт GitHub)</span>
      </p>
    </article>
  );
}
