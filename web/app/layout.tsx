import type { Metadata } from "next";
import { SITE_TITLE } from "@/lib/site";
import "./globals.css";

// Until the public launch the site is reviewable by link but hidden from search engines (NEXT_PUBLIC_LAUNCHED=true lifts it).
const launched = process.env.NEXT_PUBLIC_LAUNCHED === "true";

export const metadata: Metadata = {
  title: SITE_TITLE,
  robots: launched ? undefined : { index: false, follow: false },
  description:
    "Пошлины и налоги с обеих сторон границы, документы, санкции, господдержка и субсидии — из официальных источников, с датой проверки у каждой строки.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <body>{children}</body>
    </html>
  );
}
