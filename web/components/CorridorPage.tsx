"use client";

import { useState } from "react";
import type { Mode, PageContent } from "@/lib/page-content";
import { DemoBand, SanctionsBand, StatusBand } from "./Bands";
import { CompareTable } from "./CompareTable";
import { CostCalculator } from "./CostCalculator";
import { DocumentChecklist } from "./DocumentChecklist";
import { QuerySentence, type SiblingPage } from "./QuerySentence";
import { Rail, type TocItem } from "./Rail";
import { ProsCons, RatingCard } from "./RatingCard";
import { Section } from "./Section";
import { SiteFooter, SiteHeader } from "./SiteHeader";
import { SourcesTable } from "./SourcesTable";
import { Summary } from "./Summary";

/**
 * Corridor page in the block order of docs/concept.md, section 4. Holds the one piece of client state that
 * several blocks share: the shipment mode (commercial batch vs parcels).
 */
export function CorridorPage({
  page,
  siblings,
  initialMode,
}: {
  page: PageContent;
  siblings: SiblingPage[];
  initialMode: Mode;
}) {
  const [mode, setModeState] = useState<Mode>(page.corridor.modes.includes(initialMode) ? initialMode : "b2b");

  function setMode(next: Mode) {
    setModeState(next);
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
      {page.isDemo && (
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
          <Section section={page.import} mode={mode} />
          <CostCalculator calc={page.cost} mode={mode} />
          <Section section={page.logistics} mode={mode} />
          <DocumentChecklist documents={page.documents} mode={mode} />
          <SourcesTable sources={page.sources} />
        </main>
        <Rail toc={toc} rail={page.rail} />
      </div>

      <SiteFooter sanctionsPolicy={Boolean(page.sanctions)} />
    </>
  );
}
