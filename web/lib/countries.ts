/**
 * Country names in the grammatical forms the query sentence needs ("из Китая", "в Канаду").
 * Only the Russian UI for now; other languages are added with the same shape.
 * The four MVP countries come first; the rest exist so the start page can show how the site answers
 * when a corridor is not open yet.
 */
import type { CountryRef } from "./page-content";

export const COUNTRIES: Record<string, CountryRef> = {
  CN: { code: "CN", name: "Китай", from: "Китая", to: "Китай" },
  CA: { code: "CA", name: "Канада", from: "Канады", to: "Канаду" },
  RU: { code: "RU", name: "Россия", from: "России", to: "Россию" },
  IR: { code: "IR", name: "Иран", from: "Ирана", to: "Иран" },
  TR: { code: "TR", name: "Турция", from: "Турции", to: "Турцию" },
  VN: { code: "VN", name: "Вьетнам", from: "Вьетнама", to: "Вьетнам" },
  DE: { code: "DE", name: "Германия", from: "Германии", to: "Германию" },
  US: { code: "US", name: "США", from: "США", to: "США" },
};

export function country(code: string): CountryRef {
  return COUNTRIES[code] ?? { code, name: code, from: code, to: code };
}
