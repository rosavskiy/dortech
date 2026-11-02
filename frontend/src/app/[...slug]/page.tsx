import type { Metadata } from "next";
import { notFound, permanentRedirect, redirect } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { ContentLayout } from "@/components/ContentLayout";

async function load(slug: string) { try { return await api.page(slug); } catch (e) { if (e instanceof ApiError && e.status === 404) return null; throw e; } }

export async function generateMetadata(p: { params: Promise<{ slug: string[] }> }): Promise<Metadata> {
  const { slug } = await p.params; const page = slug.length === 1 ? await load(slug[0]) : null;
  return page ? { title: page.meta_title ?? page.title, description: page.meta_description ?? undefined, robots: page.noindex ? { index: false } : undefined } : { title: "Страница не найдена" };
}

export default async function Page(p: { params: Promise<{ slug: string[] }> }) {
  const { slug } = await p.params;
  const path = "/" + slug.join("/");
  const page = slug.length === 1 ? await load(slug[0]) : null;
  if (page) return <ContentLayout crumbs={[]} title={page.title} body={page.body} />;
  const redirects = await api.redirects().catch(() => []);
  const r = redirects.find((x) => x.old_path === path || x.old_path === path + "/");
  if (r) { if (r.status_code === 301) permanentRedirect(r.new_path); redirect(r.new_path); }
  notFound();
}
