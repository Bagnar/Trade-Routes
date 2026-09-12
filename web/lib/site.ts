/** Brand and domain are not chosen yet (docs/concept.md, section 15); the placeholder matches the mockups. */
export const SITE_NAME = "[название сайта]";
export const SITE_TITLE = "Правила торговли между странами — одной страницей";

export const LANG_LABELS: Record<string, string> = { ru: "RU", en: "EN", zh: "中文", fa: "فارسی" };

/** Repository that holds the corridor request queue (GitHub issues, label `corridor-request`). */
export const REPO_URL = process.env.NEXT_PUBLIC_REPO_URL ?? "https://github.com/Bagnar/Trade-Routes";
