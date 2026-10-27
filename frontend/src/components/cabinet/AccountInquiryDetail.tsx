"use client";
import { useQuery } from "@tanstack/react-query";
import { authFetch } from "@/lib/auth";
import type { InquiryDetail } from "@/lib/cabinet-types";
import { InquiryDetailView } from "./InquiryDetailView";
export function AccountInquiryDetail({ id }: { id: string }) {
  const key = ["account-inquiry", id];
  const q = useQuery({ queryKey: key, queryFn: () => authFetch<InquiryDetail>(`/account/inquiries/${id}`) });
  if (q.isLoading) return <p className="muted">Загрузка…</p>;
  if (q.error || !q.data) return <p className="field__error">{(q.error as Error)?.message ?? "Заявка не найдена"}</p>;
  return <InquiryDetailView data={q.data} apiBase="/account" queryKey={key} canUploadKinds={{ accept: ".pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png", label: "Загрузить документ" }} />;
}
