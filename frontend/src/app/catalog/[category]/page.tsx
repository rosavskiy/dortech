import { notFound } from "next/navigation";
import { api } from "@/lib/api";
import { CatalogPage, catalogMetadata, type SP } from "@/components/catalog/CatalogPage";

export const dynamic = "force-dynamic";

export async function generateMetadata(props: { params: Promise<{ category: string }> }) {
  const { category } = await props.params;
  const cats = await api.categories().catch(() => []);
  return catalogMetadata(cats.find((c) => c.slug === category) ?? null);
}

export default async function Page(props: { params: Promise<{ category: string }>; searchParams: Promise<SP> }) {
  const [{ category }, sp] = await Promise.all([props.params, props.searchParams]);
  const cats = await api.categories();
  if (!cats.some((c) => c.slug === category)) notFound();
  return <CatalogPage sp={sp} categorySlug={category} />;
}
