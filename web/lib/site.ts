/** Name chosen by the founder on 13 September 2026 (docs/concept.md, decision 14); the domain follows the name. */
export const SITE_NAME = "TradeRoutes";
export const SITE_TAGLINE = "правила торговли между странами";
export const SITE_TITLE = "TradeRoutes — правила торговли между странами одной страницей";

export const LANG_LABELS: Record<string, string> = { ru: "RU", en: "EN", zh: "中文", fa: "فارسی" };

/** Repository that holds the corridor request queue (GitHub issues, label `corridor-request`). */
export const REPO_URL = process.env.NEXT_PUBLIC_REPO_URL ?? "https://github.com/Bagnar/Trade-Routes";
