/** URL helpers shared by server and client components (no Node-only imports here). */
export function pageHref(corridorId: string, hs6: string): string {
  return `/corridor/${corridorId}/${hs6}`;
}

export function supplyHref(country: string, hs: string): string {
  return `/where-to-buy/${country.toLowerCase()}/${hs}`;
}

export function countryHref(code: string): string {
  return `/country/${code.toLowerCase()}`;
}

/**
 * "Запросить коридор": a prefilled GitHub issue (template .github/ISSUE_TEMPLATE/corridor-request.yml).
 * No server of our own: the issue is the queue, `python -m pipeline requests` reads it (docs/expansion-plan.md, 1.9).
 */
export function requestCorridorUrl(repoUrl: string, q: { product: string; from: string; to: string; mode?: "b2b" | "parcel" }): string {
  const params = new URLSearchParams({
    template: "corridor-request.yml",
    title: `Коридор: ${q.product || "товар"} из ${q.from} в ${q.to}`,
    product: q.product,
    from: q.from,
    to: q.to,
    mode: q.mode === "parcel" ? "посылки покупателям" : "коммерческая партия",
  });
  return `${repoUrl}/issues/new?${params.toString()}`;
}
