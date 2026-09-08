import type { Mode, Section as SectionContent } from "@/lib/page-content";
import { FactList } from "./FactRow";

export function SectionHeading({ id, number, title }: { id: string; number?: number; title: string }) {
  return (
    <h2 id={id}>
      {number !== undefined && <span className="n">{number}</span>}
      {title}
    </h2>
  );
}

/** A numbered block of facts with optional lead and sub-groups (e.g. "Что даёт государство экспортёру"). */
export function Section({ section, mode }: { section: SectionContent; mode: Mode }) {
  return (
    <>
      <SectionHeading id={section.id} number={section.number} title={section.title} />
      {section.lead && <p className="lead">{section.lead}</p>}
      <FactList facts={section.facts} mode={mode} />
      {section.groups?.map((group, i) => (
        <div key={i}>
          {group.title && <h3>{group.title}</h3>}
          <FactList facts={group.facts} mode={mode} />
        </div>
      ))}
    </>
  );
}
