import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { api, ApiError, mediaUrl } from "@/lib/api";
import { ContentLayout } from "@/components/ContentLayout";
export const revalidate = 60;
async function load(slug: string) { try { return await api.publication(slug); } catch (e) { if (e instanceof ApiError && e.status === 404) return null; throw e; } }
export async function generateMetadata(p: { params: Promise<{ slug: string }> }): Promise<Metadata> { const { slug } = await p.params; const s = await load(slug); return s ? { title: s.meta_title ?? s.title, description: s.meta_description ?? s.short_description ?? undefined, robots: s.noindex ? { index: false } : undefined } : { title: "Не найдено" }; }
export default async function Page(p: { params: Promise<{ slug: string }> }) {
  const { slug } = await p.params; const s = await load(slug); if (!s) notFound();
  return <ContentLayout crumbs={[["/publications", "Публикации"]]} title={s.title} lead={s.short_description} cover={mediaUrl(s.cover_url)} body={s.body} facts={s.published_at ? [new Date(s.published_at).toLocaleDateString("ru-RU")] : []} />;
}
