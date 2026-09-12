import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { SupplyPage } from "@/components/SupplyPage";
import { getSupplyPage, listSupplyPages } from "@/lib/supply";

type Params = { country: string; hs: string };

export async function generateStaticParams(): Promise<Params[]> {
  const pages = await listSupplyPages();
  return pages.map((p) => ({ country: p.country.code.toLowerCase(), hs: p.hs }));
}

export async function generateMetadata({ params }: { params: Promise<Params> }): Promise<Metadata> {
  const { country, hs } = await params;
  const page = await getSupplyPage(country, hs);
  if (!page) return { title: "Страница не найдена" };
  const name = page.product.name[0].toUpperCase() + page.product.name.slice(1);
  return { title: `${name} ${page.country.loc ?? page.country.name} — где купить` };
}

export default async function Page({ params }: { params: Promise<Params> }) {
  const { country, hs } = await params;
  const page = await getSupplyPage(country, hs);
  if (!page) notFound();
  return <SupplyPage page={page} />;
}
