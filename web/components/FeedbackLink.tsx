"use client";

import { useEffect, useState } from "react";
import { REPO_URL } from "@/lib/site";

/** "Сообщить о неточности": a prefilled GitHub issue with the current page address (template page-feedback.yml). */
export function FeedbackLink() {
  const [href, setHref] = useState(`${REPO_URL}/issues/new?template=page-feedback.yml`);
  useEffect(() => {
    const params = new URLSearchParams({ template: "page-feedback.yml", title: `Замечание: ${document.title}`, page: window.location.href });
    setHref(`${REPO_URL}/issues/new?${params.toString()}`);
  }, []);
  return (
    <a href={href} target="_blank" rel="noopener noreferrer">
      Сообщить о неточности
    </a>
  );
}
