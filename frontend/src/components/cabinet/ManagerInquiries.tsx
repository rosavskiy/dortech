"use client";
import { useSearchParams, useRouter, usePathname } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { authFetch } from "@/lib/auth";
import { STATUS_LABELS, type InquiryBrief, type Paginated, type UserBrief } from "@/lib/cabinet-types";
import { InquiryTable } from "./InquiryTable";
import { Pagination } from "@/components/catalog/Pagination";
import styles from "./ManagerInquiries.module.scss";

const KEYS = ["status", "assigned_to", "organization", "date_from", "date_to", "q", "page"] as const;

export function ManagerInquiries() {
  const sp = useSearchParams(); const router = useRouter(); const path = usePathname();
  const params: Record<string, string> = {};
  for (const k of KEYS) { const v = sp.get(k); if (v) params[k] = v; }
  const qs = new URLSearchParams(params).toString();
  const q = useQuery({ queryKey: ["manager-inquiries", qs], queryFn: () => authFetch<Paginated<InquiryBrief>>(`/manager/inquiries?${qs}`) });
  const managers = useQuery({ queryKey: ["managers"], queryFn: () => authFetch<UserBrief[]>("/manager/managers"), staleTime: 300_000 });
  const orgs = useQuery({ queryKey: ["orgs"], queryFn: () => authFetch<{ id: number; name: string }[]>("/manager/organizations"), staleTime: 300_000 });
  const update = (patch: Record<string, string>) => { const p = new URLSearchParams({ ...params, ...patch }); for (const [k, v] of Object.entries(patch)) if (!v) p.delete(k); p.delete("page"); router.push(`${path}?${p.toString()}`); };
  const { page: _p, ...rest } = params; void _p;
  const exportQs = new URLSearchParams(rest).toString();
  return (
    <div>
      <div className={styles.head}><h1>Заявки</h1><a className="btn btn--outline btn--sm" href={`/api/v1/manager/inquiries/export.csv?${exportQs}`}>Выгрузить CSV</a></div>
      <form className={styles.filters} onSubmit={(e) => { e.preventDefault(); const f = new FormData(e.currentTarget); update({ q: String(f.get("q") ?? ""), date_from: String(f.get("date_from") ?? ""), date_to: String(f.get("date_to") ?? "") }); }}>
        <select className="select" value={params.status ?? ""} onChange={(e) => update({ status: e.target.value })} aria-label="Статус"><option value="">Все статусы</option>{Object.entries(STATUS_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select>
        <select className="select" value={params.assigned_to ?? ""} onChange={(e) => update({ assigned_to: e.target.value })} aria-label="Ответственный"><option value="">Любой ответственный</option><option value="none">Не назначен</option>{managers.data?.map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}</select>
        <select className="select" value={params.organization ?? ""} onChange={(e) => update({ organization: e.target.value })} aria-label="Организация"><option value="">Все организации</option>{orgs.data?.map((o) => <option key={o.id} value={o.id}>{o.name}</option>)}</select>
        <input className="input" type="date" name="date_from" defaultValue={params.date_from ?? ""} aria-label="С даты" />
        <input className="input" type="date" name="date_to" defaultValue={params.date_to ?? ""} aria-label="По дату" />
        <input className="input" name="q" defaultValue={params.q ?? ""} placeholder="Номер, контакт, телефон, компания" aria-label="Поиск" />
        <button className="btn btn--secondary" type="submit">Применить</button>
        {Object.keys(rest).length > 0 && <button type="button" className="btn btn--ghost" onClick={() => router.push(path)}>Сбросить</button>}
      </form>
      {q.isLoading ? <p className="muted">Загрузка…</p> : q.error ? <p className="field__error">{(q.error as Error).message}</p> : q.data && (
        <><p className="muted">{q.data.total} заявок</p><InquiryTable items={q.data.items} base="/manager/inquiries" manager /><Pagination page={q.data.page} pages={q.data.pages} basePath="/manager/inquiries" sp={rest} /></>
      )}
    </div>
  );
}
