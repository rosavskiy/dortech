import type {
  CategoryOut, CompareOut, EquipmentCard, EquipmentDetail, EstimateIn, EstimateOut, ExtraServiceOut, Facets, HomeOut,
  InquiryCreateIn, InquiryCreatedOut, PageOut, Paginated, ProjectOut, PublicationOut, RedirectOut, ServiceOut,
  SitemapEntry, SiteSettingsOut,
} from "./types";

/** На сервере ходим во внутренний адрес бэкенда, в браузере — в относительный /api (dev: rewrite, prod: Caddy). */
export function apiBase(): string {
  if (typeof window === "undefined") return (process.env.INTERNAL_API_URL ?? "http://localhost:8000") + "/api/v1";
  return "/api/v1";
}

export class ApiError extends Error {
  constructor(public status: number, message: string, public detail?: unknown) {
    super(message);
  }
}

type Opts = RequestInit & { revalidate?: number | false; tags?: string[] };

export async function apiFetch<T>(path: string, opts: Opts = {}): Promise<T> {
  const { revalidate, tags, ...init } = opts;
  const next = revalidate === undefined ? undefined : { revalidate, tags };
  const res = await fetch(apiBase() + path, {
    ...init,
    headers: { Accept: "application/json", ...(init.body ? { "Content-Type": "application/json" } : {}), ...(init.headers ?? {}) },
    ...(next ? { next } : { cache: "no-store" as const }),
  });
  if (!res.ok) {
    let detail: unknown = undefined;
    try { detail = await res.json(); } catch { /* ignore */ }
    const message = typeof (detail as { detail?: unknown })?.detail === "string" ? (detail as { detail: string }).detail : `Ошибка ${res.status}`;
    throw new ApiError(res.status, message, detail);
  }
  return (await res.json()) as T;
}

const PUBLIC = { revalidate: 60 };

export const api = {
  settings: () => apiFetch<SiteSettingsOut>("/content/settings", PUBLIC),
  home: () => apiFetch<HomeOut>("/content/home", PUBLIC),
  page: (slug: string) => apiFetch<PageOut>(`/content/pages/${encodeURIComponent(slug)}`, PUBLIC),
  services: () => apiFetch<ServiceOut[]>("/content/services", PUBLIC),
  service: (slug: string) => apiFetch<ServiceOut>(`/content/services/${encodeURIComponent(slug)}`, PUBLIC),
  projects: () => apiFetch<ProjectOut[]>("/content/projects", PUBLIC),
  project: (slug: string) => apiFetch<ProjectOut>(`/content/projects/${encodeURIComponent(slug)}`, PUBLIC),
  publications: (page = 1) => apiFetch<Paginated<PublicationOut>>(`/content/publications?page=${page}`, PUBLIC),
  publication: (slug: string) => apiFetch<PublicationOut>(`/content/publications/${encodeURIComponent(slug)}`, PUBLIC),
  redirects: () => apiFetch<RedirectOut[]>("/content/redirects", PUBLIC),
  sitemap: () => apiFetch<SitemapEntry[]>("/content/sitemap", { revalidate: 600 }),

  categories: () => apiFetch<CategoryOut[]>("/catalog/categories", PUBLIC),
  facets: (qs: string) => apiFetch<Facets>(`/catalog/facets${qs ? "?" + qs : ""}`, { revalidate: 30 }),
  equipmentList: (qs: string) => apiFetch<Paginated<EquipmentCard>>(`/catalog/equipment${qs ? "?" + qs : ""}`, { revalidate: 30 }),
  equipment: (slug: string) => apiFetch<EquipmentDetail>(`/catalog/equipment/${encodeURIComponent(slug)}`, PUBLIC),
  compare: (ids: number[]) => apiFetch<CompareOut>(`/catalog/compare?ids=${ids.join(",")}`),

  extraServices: () => apiFetch<ExtraServiceOut[]>("/inquiries/extra-services", PUBLIC),
  estimate: (data: EstimateIn) => apiFetch<EstimateOut>("/inquiries/estimate", { method: "POST", body: JSON.stringify(data) }),
  createInquiry: (data: InquiryCreateIn) => apiFetch<InquiryCreatedOut>("/inquiries", { method: "POST", body: JSON.stringify(data) }),
  contactMessage: (data: { name: string; phone?: string; email?: string; text: string; consent: boolean; website?: string }) =>
    apiFetch<{ ok: boolean }>("/contact-messages", { method: "POST", body: JSON.stringify(data) }),
};

export function money(v: string | number | null | undefined, suffix = " ₽"): string {
  if (v === null || v === undefined || v === "") return "по запросу";
  const n = typeof v === "string" ? Number(v) : v;
  if (Number.isNaN(n)) return String(v);
  return new Intl.NumberFormat("ru-RU", { maximumFractionDigits: 0 }).format(n) + suffix;
}

export function mediaUrl(url: string | null | undefined): string | null {
  if (!url) return null;
  if (url.startsWith("http")) return url;
  if (typeof window === "undefined") return (process.env.INTERNAL_API_URL ?? "http://localhost:8000") + url;
  return url;
}
