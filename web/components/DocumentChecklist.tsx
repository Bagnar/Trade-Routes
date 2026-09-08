"use client";

import { useState } from "react";
import type { Mode, PageContent } from "@/lib/page-content";
import { visibleInMode } from "@/lib/text";
import { SectionHeading } from "./Section";

/** Export and import checklists. Ticks live only in this browser tab, as the lead says. */
export function DocumentChecklist({ documents, mode }: { documents: PageContent["documents"]; mode: Mode }) {
  const [done, setDone] = useState<Record<string, boolean>>({});

  return (
    <>
      <SectionHeading id={documents.id} number={documents.number} title={documents.title} />
      <p className="lead">{documents.lead}</p>
      {documents.groups.map((group, g) => {
        if (!visibleInMode(group.modes, mode)) return null;
        return (
          <div key={g}>
            <h3>{group.title}</h3>
            <ul className="check">
              {group.items.map((item, i) => {
                const id = `doc-${g}-${i}`;
                return (
                  <li key={id} className={done[id] ? "done" : undefined}>
                    <input
                      type="checkbox"
                      id={id}
                      checked={Boolean(done[id])}
                      onChange={(e) => setDone((prev) => ({ ...prev, [id]: e.target.checked }))}
                    />
                    <label htmlFor={id}>{item}</label>
                  </li>
                );
              })}
            </ul>
          </div>
        );
      })}
    </>
  );
}
