import type { PageContent } from "@/lib/page-content";

export function StatusBand({ status }: { status: PageContent["status"] }) {
  return (
    <div className="band status">
      <div className="in">{status.text}</div>
    </div>
  );
}

export function DemoBand({ children }: { children: React.ReactNode }) {
  return (
    <div className="band demo">
      <div className="in">{children}</div>
    </div>
  );
}

/** Red band shown only for sanctioned pairs. Text describes what is restricted — never how to get around it. */
export function SanctionsBand({ sanctions }: { sanctions: NonNullable<PageContent["sanctions"]> }) {
  return (
    <div className="band sanctions">
      <div className="in">
        <span className="tag">{sanctions.tag}</span>
        <p>{sanctions.text}</p>
      </div>
    </div>
  );
}
