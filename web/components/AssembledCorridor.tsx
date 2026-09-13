"use client";

import Link from "next/link";
import { useEffect, useState, useSyncExternalStore } from "react";
import { assemblePage } from "@/lib/assemble-client";
import { loadCorridorData } from "@/lib/corridor-data";
import type { PageContent } from "@/lib/page-content";
import { pageHref, requestCorridorUrl } from "@/lib/routes";
import { REPO_URL } from "@/lib/site";
import { CorridorPage } from "./CorridorPage";
import { SiteFooter, SiteHeader } from "./SiteHeader";

interface Query {
  from: string;
  to: string;
  hs6: string;
}

function subscribeToUrl(onChange: () => void): () => void {
  window.addEventListener("popstate", onChange);
  return () => window.removeEventListener("popstate", onChange);
}

function readQuery(): string {
  const p = new URL(window.location.href).searchParams;
  return `${p.get("from") ?? ""}|${p.get("to") ?? ""}|${p.get("hs6") ?? ""}`;
}

function parseQuery(raw: string | null): Query | null {
  if (raw === null) return null;
  const [from, to, hs6] = raw.split("|").map((s) => s.trim().toUpperCase());
  if (!/^[A-Z]{2}$/.test(from) || !/^[A-Z]{2}$/.test(to) || !/^\d{6}$/.test(hs6)) return null;
  return { from, to, hs6 };
}

type Loaded = { kind: "prebuilt"; href: string } | { kind: "ready"; page: PageContent };
type State = { kind: "loading" } | { kind: "bad" } | Loaded;

/** Reads the query on the client, loads the data, assembles the page; redirects to a prebuilt page when one exists. */
export function AssembledCorridor() {
  const raw = useSyncExternalStore(subscribeToUrl, readQuery, () => null);
  const query = parseQuery(raw);
  const key = query ? `${query.from}|${query.to}|${query.hs6}` : null;
  // Loaded results are keyed by the query they answer; the effect only does the asynchronous work.
  const [loaded, setLoaded] = useState<{ key: string; value: Loaded } | null>(null);

  useEffect(() => {
    if (!key) return;
    const [from, to, hs6] = key.split("|");
    let alive = true;
    loadCorridorData(from, to, hs6).then((data) => {
      if (!alive) return;
      const prebuilt = data.registry.pages.find((p) => p.from === from && p.to === to && p.hs6 === hs6);
      if (prebuilt) {
        const href = pageHref(prebuilt.corridor, prebuilt.hs6);
        setLoaded({ key, value: { kind: "prebuilt", href } });
        window.location.replace(`${process.env.NEXT_PUBLIC_BASE_PATH ?? ""}${href}/`);
        return;
      }
      setLoaded({ key, value: { kind: "ready", page: assemblePage(data, from, to, hs6) } });
    });
    return () => {
      alive = false;
    };
  }, [key]);

  const current: State = raw === null ? { kind: "loading" } : !key ? { kind: "bad" } : loaded?.key === key ? loaded.value : { kind: "loading" };

  if (current.kind === "ready") {
    const page = current.page;
    return <CorridorPage page={page} siblings={[{ hs6: page.product.hs6, name: page.product.name, hsLabel: page.product.hsLabel }]} />;
  }

  return (
    <>
      <SiteHeader languages={["ru"]} current="ru" linkHome />
      <div className="doc">
        <main>
          {current.kind === "loading" && <p className="lead">Собираем страницу из загруженных данных…</p>}
          {current.kind === "prebuilt" && (
            <p className="lead">
              Для этой пары и группы уже есть собранная страница: <Link href={current.href}>открыть</Link>.
            </p>
          )}
          {current.kind === "bad" && (
            <>
              <h2>Не хватает параметров</h2>
              <p className="lead">
                Адрес страницы должен содержать две страны (ISO-код из двух букв) и код товара HS-6 из шести цифр, например{" "}
                <Link href="/c/?from=CN&to=CA&hs6=610910">/c/?from=CN&amp;to=CA&amp;hs6=610910</Link>. Выберите товар и страны на{" "}
                <Link href="/">главной странице</Link>, или{" "}
                <a href={requestCorridorUrl(REPO_URL, { product: "", from: "", to: "" })} target="_blank" rel="noopener noreferrer">
                  запросите коридор
                </a>
                .
              </p>
            </>
          )}
        </main>
      </div>
      <SiteFooter />
    </>
  );
}
