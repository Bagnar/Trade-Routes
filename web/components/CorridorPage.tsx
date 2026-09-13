"use client";

import { useState, useSyncExternalStore } from "react";
import type { Mode, PageContent } from "@/lib/page-content";
import { DemoBand, SanctionsBand, StatusBand } from "./Bands";
import { CompareTable } from "./CompareTable";
import { CostCalculator } from "./CostCalculator";
import { DocumentChecklist } from "./DocumentChecklist";
import { QuerySentence, type SiblingPage } from "./QuerySentence";
import { Rail, type SupplyLink, type TocItem } from "./Rail";
import { ProsCons, RatingCard } from "./RatingCard";
import { Section } from "./Section";
import { SiteFooter, SiteHeader } from "./SiteHeader";
import { SourcesTable } from "./SourcesTable";
import { Summary } from "./Summary";

function subscribeToUrl(onChange: () => void): () => void {
  window.addEventListener("popstate", onChange);
  return () => window.removeEventListener("popstate", onChange);
}

function readUrlMode(): string | null {
  return new URL(window.location.href).searchParams.get("mode");
}

/**
 * Corridor page in the block order of docs/concept.md, section 4. Holds the one piece of client state that
 * several blocks share: the shipment mode (commercial batch vs parcels).
 */
export function CorridorPage({
  page,
  siblings,
  supplyLink,
  notice,
}: {
  page: PageContent;
  siblings: SiblingPage[];
  supplyLink?: SupplyLink;
  /** Optional band under the status line (the browser-assembled page uses it for "make this page permanent"). */
  notice?: React.ReactNode;
}) {
  // Static export: the mode comes from the URL (?mode=parcel) on the client; the server snapshot is "b2b" so the
  // pre-rendered HTML hydrates without a mismatch and the client value applies right after.
  const urlMode = useSyncExternalStore(subscribeToUrl, readUrlMode, () => null);
  const [override, setOverride] = useState<Mode | null>(null);
  const mode: Mode = override ?? (urlMode === "parcel" && page.corridor.modes.includes("parcel") ? "parcel" : "b2b");

  function setMode(next: Mode) {
    setOverride(next);
    const url = new URL(window.location.href);
    if (next === "b2b") url.searchParams.delete("mode");
    else url.searchParams.set("mode", next);
    window.history.replaceState(null, "", url.toString());
  }

  const toc: TocItem[] = [
    { id: page.summary.id, title: page.summary.title },
    { id: page.rating.id, title: page.rating.title },
    { id: page.compare.id, title: "Куда ещё везти" },
    { id: page.regime.id, number: page.regime.number, title: "Режим торговли" },
    { id: page.export.id, number: page.export.number, title: page.export.title },
    ...(page.exportControl ? [{ id: page.exportControl.id, number: page.exportControl.number, title: "Экспортный контроль" }] : []),
    { id: page.import.id, number: page.import.number, title: page.import.title },
    { id: page.cost.id, number: page.cost.number, title: "Сколько платить" },
    { id: page.logistics.id, number: page.logistics.number, title: page.logistics.title },
    { id: page.documents.id, number: page.documents.number, title: page.documents.title },
    { id: page.sources.id, number: page.sources.number, title: "Источники" },
  ];

  return (
    <>
      <SiteHeader languages={page.corridor.languages} current={page.lang} linkHome>
        <QuerySentence page={page} siblings={siblings} mode={mode} onMode={setMode} />
      </SiteHeader>

      <StatusBand status={page.status} />
      {notice && <DemoBand>{notice}</DemoBand>}
      {page.isDemo && page.status.sourcesTotal > 0 && (
        <DemoBand>
          <strong>Смешанная страница.</strong> Строки с зелёной печатью и ссылкой взяты из официальных источников с
          дословной цитатой и проверяются ежедневно. Строки с пометкой «демо» или «не собрано» конвейер ещё не
          заполнил.
        </DemoBand>
      )}
      {page.isDemo && page.status.sourcesTotal === 0 && (
        <DemoBand>
          <strong>Демо-данные.</strong> Цифры и формулировки иллюстративные и не проверены — в продукте каждую строку
          заполнит конвейер из источников.
        </DemoBand>
      )}
      {page.sanctions && <SanctionsBand sanctions={page.sanctions} />}

      <div className="doc">
        <main>
          <Summary summary={page.summary} mode={mode} />
          <RatingCard rating={page.rating} />
          <ProsCons verdict={page.verdict} mode={mode} />
          <CompareTable compare={page.compare} />
          <Section section={page.regime} mode={mode} />
          <Section section={page.export} mode={mode} />
          {page.exportControl && <Section section={page.exportControl} mode={mode} />}
          <Section section={page.import} mode={mode} />
          <CostCalculator calc={page.cost} mode={mode} />
          <Section section={page.logistics} mode={mode} />
          <DocumentChecklist documents={page.documents} mode={mode} />
          <SourcesTable sources={page.sources} />
        </main>
        <Rail toc={toc} rail={page.rail} supplyLink={supplyLink} />
      </div>

      <SiteFooter sanctionsPolicy={Boolean(page.sanctions)} />
    </>
  );
}
