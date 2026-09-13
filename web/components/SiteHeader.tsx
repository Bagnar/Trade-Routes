import Link from "next/link";
import type { Lang } from "@/lib/page-content";
import { LANG_LABELS, SITE_NAME } from "@/lib/site";
import { FeedbackLink } from "./FeedbackLink";

/** Language switch. Only the current language is enabled until the assembler produces other languages. */
export function LangSwitch({ languages, current }: { languages: Lang[]; current: Lang }) {
  return (
    <div className="langs" role="group" aria-label="Язык страницы">
      {languages.map((lang) =>
        lang === current ? (
          <button key={lang} type="button" aria-current="true">
            {LANG_LABELS[lang] ?? lang}
          </button>
        ) : (
          <button key={lang} type="button" disabled title="Пока только русский">
            {LANG_LABELS[lang] ?? lang}
          </button>
        ),
      )}
    </div>
  );
}

/** Top row: brand on the left, languages on the right. `children` is the query sentence on corridor pages. */
export function SiteHeader({
  languages,
  current,
  linkHome,
  children,
}: {
  languages: Lang[];
  current: Lang;
  linkHome?: boolean;
  children?: React.ReactNode;
}) {
  return (
    <header className="top">
      <div className="top-inner">
        <div className="top-row">
          <div className="brand">
            {linkHome ? (
              <>
                <Link href="/">{SITE_NAME}</Link> — все коридоры
              </>
            ) : (
              SITE_NAME
            )}
          </div>
          <LangSwitch languages={languages} current={current} />
        </div>
        {children}
      </div>
    </header>
  );
}

export function SiteFooter({ sanctionsPolicy }: { sanctionsPolicy?: boolean }) {
  return (
    <footer>
      <div className="in">
        <span>Условия использования</span>
        <Link href="/facts">Как собираются страницы</Link>
        {sanctionsPolicy && <span>Санкционная политика сайта</span>}
        <Link href="/country">Источники по странам</Link>
        <FeedbackLink />
      </div>
    </footer>
  );
}
