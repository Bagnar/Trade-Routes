/** URL helpers shared by server and client components (no Node-only imports here). */
export function pageHref(corridorId: string, hs6: string): string {
  return `/corridor/${corridorId}/${hs6}`;
}
