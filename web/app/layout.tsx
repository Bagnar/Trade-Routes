import type { Metadata } from "next";
import { SITE_TITLE } from "@/lib/site";
import "./globals.css";

export const metadata: Metadata = {
  title: SITE_TITLE,
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
