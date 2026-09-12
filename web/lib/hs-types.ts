/** HS-6 nomenclature entry (data/hs6.json) and the label helper — safe for client components (no Node imports). */
export interface HsEntry {
  code: string;
  en: string;
  ru: string;
}

export function hsLabel(code: string): string {
  return code.length >= 6 ? `HS ${code.slice(0, 4)}.${code.slice(4, 6)}` : `HS ${code}`;
}
