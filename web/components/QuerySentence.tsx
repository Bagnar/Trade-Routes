"use client";

import { useRouter } from "next/navigation";
import type { Mode, PageContent } from "@/lib/page-content";
import { pageHref } from "@/lib/routes";

export interface SiblingPage {
  hs6: string;
  name: string;
  hsLabel: string;
}

/**
 * The query sentence on a corridor page: "Везу [товар] из [страны] в [страну] как [партию | посылки]".
 * Product select switches between pages already assembled for this corridor; countries change on the start page.
 */
export function QuerySentence({
  page,
  siblings,
  mode,
  onMode,
}: {
  page: PageContent;
  siblings: SiblingPage[];
  mode: Mode;
  onMode: (mode: Mode) => void;
}) {
  const router = useRouter();
  const { corridor, product } = page;
  const parcelAllowed = corridor.modes.includes("parcel");

  return (
    <div className="query" role="group" aria-label="Параметры коридора">
      Везу{" "}
      <select
        className="product"
        aria-label="Товар"
        value={product.hs6}
        onChange={(e) => router.push(pageHref(corridor.id, e.target.value))}
      >
        {siblings.map((s) => (
          <option key={s.hs6} value={s.hs6}>
            {s.name}, {s.hsLabel}
          </option>
        ))}
        <option disabled>другие группы…</option>
      </select>{" "}
      <select className="country" aria-label="Откуда" value={corridor.from.code} onChange={() => router.push("/")}>
        <option value={corridor.from.code}>{corridor.from.from}</option>
        <option value="">другие…</option>
      </select>{" "}
      <select className="country" aria-label="Куда" value={corridor.to.code} onChange={() => router.push("/")}>
        <option value={corridor.to.code}>{corridor.to.to}</option>
        <option value="">другие…</option>
      </select>{" "}
      как{" "}
      <span className="mode" role="group" aria-label="Режим поставки">
        <button type="button" data-mode="b2b" aria-pressed={mode === "b2b"} onClick={() => onMode("b2b")}>
          коммерческую партию
        </button>
        <button
          type="button"
          data-mode="parcel"
          aria-pressed={mode === "parcel"}
          disabled={!parcelAllowed}
          title={parcelAllowed ? undefined : corridor.parcelDisabledReason ?? "Для этой товарной группы не применимо"}
          onClick={() => onMode("parcel")}
        >
          посылки покупателям
        </button>
      </span>
    </div>
  );
}
