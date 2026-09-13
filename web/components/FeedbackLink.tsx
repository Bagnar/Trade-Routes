"use client";

import { REPO_URL } from "@/lib/site";

/** "Сообщить о неточности": a prefilled GitHub issue (template page-feedback.yml) with the current page address,
 * built at click time so the static HTML needs no client state. */
export function FeedbackLink() {
  const base = `${REPO_URL}/issues/new?template=page-feedback.yml`;
  return (
    <a
      href={base}
      target="_blank"
      rel="noopener noreferrer"
      onClick={(e) => {
        e.preventDefault();
        const params = new URLSearchParams({ template: "page-feedback.yml", title: `Замечание: ${document.title}`, page: window.location.href });
        window.open(`${REPO_URL}/issues/new?${params.toString()}`, "_blank", "noopener,noreferrer");
      }}
    >
      Сообщить о неточности
    </a>
  );
}
