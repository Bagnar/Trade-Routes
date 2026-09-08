import Link from "next/link";
import { SiteFooter, SiteHeader } from "@/components/SiteHeader";

export default function NotFound() {
  return (
    <>
      <SiteHeader languages={["ru"]} current="ru" linkHome />
      <section className="hero">
        <h1>Такой страницы ещё нет</h1>
        <p className="sub">
          Коридор или товарная группа пока не собраны из источников. Страницы появляются по запросу — выберите
          коридор на стартовой или оставьте заявку.
        </p>
        <p>
          <Link href="/">На стартовую</Link>
        </p>
      </section>
      <SiteFooter />
    </>
  );
}
