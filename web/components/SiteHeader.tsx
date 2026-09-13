import Link from "next/link";
import type { Lang } from "@/lib/page-content";
import { LANG_LABELS, SITE_NAME, SITE_TAGLINE } from "@/lib/site";
import { LogoMark } from "./Logo";
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
            <Link href="/" className="brand-link" aria-label={`${SITE_NAME} — на главную`}>
              <LogoMark />
              <span className="brand-name">{SITE_NAME}</span>
            </Link>
            <span className="brand-tag">{linkHome ? "все коридоры" : SITE_TAGLINE}</span>
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
        <Link href="/terms">Условия использования</Link>
        <Link href="/facts">Как собираются страницы</Link>
        {sanctionsPolicy && <Link href="/terms#s3">Санкционная политика сайта</Link>}
        <Link href="/country">Источники по странам</Link>
        <FeedbackLink />
      </div>
    </footer>
  );
}
