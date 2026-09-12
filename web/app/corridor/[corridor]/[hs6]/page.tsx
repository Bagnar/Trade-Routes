import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { CorridorPage } from "@/components/CorridorPage";
import type { Mode } from "@/lib/page-content";
import { getPage, listPages } from "@/lib/pages";
import { supplyHref } from "@/lib/routes";
import { findSupplyFor } from "@/lib/supply";

type Params = { corridor: string; hs6: string };

export async function generateStaticParams(): Promise<Params[]> {
  const pages = await listPages();
  return pages.map((p) => ({ corridor: p.corridorId, hs6: p.hs6 }));
}

export async function generateMetadata({ params }: { params: Promise<Params> }): Promise<Metadata> {
  const { corridor, hs6 } = await params;
  const page = await getPage(corridor, hs6);
  if (!page) return { title: "Коридор не найден" };
  const title = `${page.product.name[0].toUpperCase()}${page.product.name.slice(1)} ${page.corridor.from.from} ${page.corridor.to.to} — страница коридора`;
  return { title };
}

export default async function Page({
  params,
  searchParams,
}: {
  params: Promise<Params>;
  searchParams: Promise<{ mode?: string }>;
}) {
  const { corridor, hs6 } = await params;
  const { mode } = await searchParams;
  const page = await getPage(corridor, hs6);
  if (!page) notFound();

  const siblings = (await listPages())
    .filter((p) => p.corridorId === corridor && p.lang === page.lang)
    .map((p) => ({ hs6: p.hs6, name: p.product.name, hsLabel: p.product.hsLabel }));

  const supply = await findSupplyFor(page.corridor.from.code, hs6, page.lang);
  const supplyLink = supply
    ? {
        href: supplyHref(supply.country.code, supply.hs),
        label: `Где купить ${supply.product.name} ${supply.country.loc ?? supply.country.name}`,
        note: `Регионы и кластеры производства (${supply.regionCount}), официальные реестры и выставки.`,
      }
    : undefined;

  const initialMode: Mode = mode === "parcel" ? "parcel" : "b2b";
  return <CorridorPage page={page} siblings={siblings} initialMode={initialMode} supplyLink={supplyLink} />;
}
