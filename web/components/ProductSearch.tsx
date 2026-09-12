"use client";

import { useEffect, useMemo, useState } from "react";
import type { HsEntry } from "@/lib/hs-types";
import { hsLabel } from "@/lib/hs-types";

const BASE = process.env.NEXT_PUBLIC_BASE_PATH ?? "";
let hsPromise: Promise<HsEntry[]> | null = null;
let synPromise: Promise<Record<string, string[]>> | null = null;

function loadHs(): Promise<HsEntry[]> {
  hsPromise ??= fetch(`${BASE}/data/hs6.json`).then((r) => (r.ok ? r.json() : [])).catch(() => []);
  return hsPromise;
}
function loadSynonyms(): Promise<Record<string, string[]>> {
  synPromise ??= fetch(`${BASE}/data/hs_synonyms_ru.json`)
    .then((r) => (r.ok ? r.json() : {}))
    .then((raw: Record<string, unknown>) => Object.fromEntries(Object.entries(raw).filter(([k, v]) => !k.startsWith("_") && Array.isArray(v))) as Record<string, string[]>)
    .catch(() => ({}));
  return synPromise;
}

export interface ProductPick {
  code: string;
  label: string;
}

/**
 * Product picker over the whole HS-6 nomenclature: type a word (Russian hint, English text) or a code,
 * pick one of the suggestions. Never narrower than HS-6 (principle 6).
 */
export function ProductSearch({
  value,
  onPick,
  placeholder = "товар или код HS",
  id = "product-search",
}: {
  value: string;
  onPick: (pick: ProductPick | null, text: string) => void;
  placeholder?: string;
  id?: string;
}) {
  const [open, setOpen] = useState(false);
  const [hs, setHs] = useState<HsEntry[]>([]);
  const [synonyms, setSynonyms] = useState<Record<string, string[]>>({});
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    if (!open || loaded) return;
    let alive = true;
    Promise.all([loadHs(), loadSynonyms()]).then(([h, s]) => {
      if (!alive) return;
      setHs(h);
      setSynonyms(s);
      setLoaded(true);
    });
    return () => {
      alive = false;
    };
  }, [open, loaded]);

  const matches = useMemo<HsEntry[]>(() => {
    const q = value.trim().toLowerCase();
    if (q.length < 2) return [];
    const digits = q.replace(/\D/g, "");
    const out: HsEntry[] = [];
    const seen = new Set<string>();
    const push = (e: HsEntry) => {
      if (!seen.has(e.code) && out.length < 12) {
        seen.add(e.code);
        out.push(e);
      }
    };
    if (digits.length >= 4 && digits.length === q.replace(/[.\s]/g, "").length) {
      hs.filter((e) => e.code.startsWith(digits.slice(0, 6))).forEach(push);
      return out;
    }
    // Russian hints: keyword -> HS prefixes
    const prefixes = new Set<string>();
    for (const [word, codes] of Object.entries(synonyms)) {
      if (q.includes(word) || word.startsWith(q)) codes.forEach((c) => prefixes.add(c));
    }
    if (prefixes.size) hs.filter((e) => [...prefixes].some((p) => e.code.startsWith(p))).forEach(push);
    // Nomenclature texts (Russian when loaded, English always)
    const words = q.split(/\s+/).filter((w) => w.length >= 3);
    if (words.length) {
      hs.filter((e) => {
        const t = `${e.ru} ${e.en}`.toLowerCase();
        return words.every((w) => t.includes(w));
      }).forEach(push);
    }
    return out;
  }, [value, hs, synonyms]);

  return (
    <span style={{ position: "relative", display: "inline-block", maxWidth: "100%" }}>
      <input
        id={id}
        className="product"
        placeholder={placeholder}
        aria-label="Товар"
        autoComplete="off"
        value={value}
        onChange={(e) => {
          onPick(null, e.target.value);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        onBlur={() => setTimeout(() => setOpen(false), 150)}
      />
      {open && matches.length > 0 && (
        <ul className="suggest" role="listbox">
          {matches.map((e) => (
            <li key={e.code} role="option" aria-selected={false}>
              <button
                type="button"
                onMouseDown={(ev) => ev.preventDefault()}
                onClick={() => {
                  const label = e.ru || e.en;
                  onPick({ code: e.code, label }, `${label}, ${hsLabel(e.code)}`);
                  setOpen(false);
                }}
              >
                <b>{hsLabel(e.code)}</b> {e.ru || e.en}
                {e.ru && e.en && <span className="en"> · {e.en}</span>}
              </button>
            </li>
          ))}
        </ul>
      )}
      {loaded && hs.length === 0 && value.trim().length >= 2 && matches.length === 0 && (
        <span className="hint" style={{ display: "block" }}>
          Номенклатура ещё не загружена: подсказки только по русским ключевым словам. Код можно ввести цифрами.
        </span>
      )}
    </span>
  );
}
