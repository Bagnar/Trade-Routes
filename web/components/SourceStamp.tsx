import type { Stamp } from "@/lib/page-content";

/** The source stamp shown next to every line: domain in bold, status line below, colour by status. */
export function SourceStamp({ stamp }: { stamp: Stamp }) {
  const body = (
    <>
      <b>{stamp.source}</b>
      {stamp.label}
    </>
  );
  if (stamp.url) {
    return (
      <a className={`stamp ${stamp.status}`} href={stamp.url} target="_blank" rel="noopener noreferrer">
        {body}
      </a>
    );
  }
  return <span className={`stamp ${stamp.status}`}>{body}</span>;
}
