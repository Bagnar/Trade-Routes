/** Mark 1 (chosen 13 September 2026): two points and a route between them. Inline SVG, inherits the text colour. */
export function LogoMark({ size = 26 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 30 30" aria-hidden="true" focusable="false">
      <rect x="1.5" y="1.5" width="27" height="27" rx="5" fill="none" stroke="currentColor" strokeWidth="2" />
      <path d="M8 19 L15 11 L22 19" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="8" cy="19" r="2.2" fill="currentColor" />
      <circle cx="22" cy="19" r="2.2" fill="currentColor" />
    </svg>
  );
}
