"use client";
import Link from "next/link";
import { useSearchParams, useRouter, usePathname } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { authFetch } from "@/lib/auth";
import { STATUS_LABELS, type InquiryBrief, type Paginated } from "@/lib/cabinet-types";
import { InquiryTable } from "./InquiryTable";
import { Pagination } from "@/components/catalog/Pagination";

export function AccountInquiries() {
  const sp = useSearchParams(); const router = useRouter(); const path = usePathname();
  const status = sp.get("status") ?? ""; const page = sp.get("page") ?? "1";
  const q = useQuery({ queryKey: ["account-inquiries", status, page], queryFn: () => authFetch<Paginated<InquiryBrief>>(`/account/inquiries?status=${status}&page=${page}`) });
  const set = (s: string) => router.push(s ? `${path}?status=${s}` : path);
  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 16, flexWrap: "wrap", alignItems: "center", marginBottom: 16 }}><h1 style={{ margin: 0 }}>Мои заявки</h1><Link href="/catalog" className="btn btn--primary btn--sm">Новая заявка</Link></div>
      <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 16 }}>
        <button type="button" className={`btn btn--sm ${!status ? "btn--secondary" : "btn--ghost"}`} onClick={() => set("")}>Все</button>
        {Object.entries(STATUS_LABELS).map(([k, v]) => <button key={k} type="button" className={`btn btn--sm ${status === k ? "btn--secondary" : "btn--ghost"}`} onClick={() => set(k)}>{v}</button>)}
      </div>
      {q.isLoading ? <p className="muted">Загрузка…</p> : q.error ? <p className="field__error">{(q.error as Error).message}</p> : q.data && (
        <><InquiryTable items={q.data.items} base="/account/inquiries" /><Pagination page={q.data.page} pages={q.data.pages} basePath="/account/inquiries" sp={status ? { status } : {}} /></>
      )}
    </div>
  );
}
