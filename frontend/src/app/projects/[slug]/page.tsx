import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { api, ApiError, mediaUrl } from "@/lib/api";
import { ContentLayout } from "@/components/ContentLayout";
export const revalidate = 60;
async function load(slug: string) { try { return await api.project(slug); } catch (e) { if (e instanceof ApiError && e.status === 404) return null; throw e; } }
export async function generateMetadata(p: { params: Promise<{ slug: string }> }): Promise<Metadata> { const { slug } = await p.params; const s = await load(slug); return s ? { title: s.meta_title ?? s.title, description: s.meta_description ?? s.short_description ?? undefined, robots: s.noindex ? { index: false } : undefined } : { title: "Не найдено" }; }
export default async function Page(p: { params: Promise<{ slug: string }> }) {
  const { slug } = await p.params; const s = await load(slug); if (!s) notFound();
  const facts = [s.year && `Год: ${s.year}`, s.customer_name && `Заказчик: ${s.customer_name}`, s.location && `Место: ${s.location}`].filter(Boolean) as string[];
  return <ContentLayout crumbs={[["/projects", "Проекты"]]} title={s.title} lead={s.short_description} cover={mediaUrl(s.cover_url)} body={s.body} facts={facts} gallery={s.images.map((i) => ({ url: mediaUrl(i.url)!, alt: i.alt ?? s.title }))} />;
}
