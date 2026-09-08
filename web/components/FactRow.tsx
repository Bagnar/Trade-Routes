import type { Fact, Mode } from "@/lib/page-content";
import { modeText, visibleInMode } from "@/lib/text";
import { SourceStamp } from "./SourceStamp";

export function FactRow({ fact, mode }: { fact: Fact; mode: Mode }) {
  if (!visibleInMode(fact.modes, mode)) return null;
  const text = modeText(fact.text, mode);
  if (text === null) return null;
  return (
    <div className={fact.ban ? "fact ban" : "fact"}>
      {fact.key !== undefined && <span className="k">{fact.key}</span>}
      <p>{text}</p>
      <SourceStamp stamp={fact.stamp} />
    </div>
  );
}

export function FactList({ facts, mode }: { facts: Fact[]; mode: Mode }) {
  return (
    <div className="facts">
      {facts.map((fact, i) => (
        <FactRow key={i} fact={fact} mode={mode} />
      ))}
    </div>
  );
}
