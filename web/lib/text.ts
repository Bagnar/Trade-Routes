import type { Mode, ModeText } from "./page-content";

/** Picks the text for the current mode; returns null when the text has no variant for that mode. */
export function modeText(text: ModeText, mode: Mode): string | null {
  if (typeof text === "string") return text;
  return text[mode] ?? null;
}

export function visibleInMode(modes: Mode[] | undefined, mode: Mode): boolean {
  return !modes || modes.includes(mode);
}
