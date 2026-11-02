import type { MetadataRoute } from "next";
export const dynamic = "force-dynamic";
import { api } from "@/lib/api";
export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const base = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";
  const entries = await api.sitemap().catch(() => []);
  return entries.map((e) => ({ url: base + e.path, lastModified: e.updated_at ? new Date(e.updated_at) : undefined, priority: e.priority }));
}
