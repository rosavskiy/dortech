"use client";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { authFetch } from "@/lib/auth";
import { STATUS_LABELS, type InquiryDetail, type UserBrief } from "@/lib/cabinet-types";
import { toast } from "@/components/ui/Toast";
import { InquiryDetailView } from "./InquiryDetailView";
import styles from "./ManagerActions.module.scss";

export function ManagerInquiryDetail({ id }: { id: string }) {
  const key = ["manager-inquiry", id];
  const qc = useQueryClient();
  const q = useQuery({ queryKey: key, queryFn: () => authFetch<InquiryDetail>(`/manager/inquiries/${id}`) });
  const managers = useQuery({ queryKey: ["managers"], queryFn: () => authFetch<UserBrief[]>("/manager/managers"), staleTime: 300_000 });
  const [status, setStatus] = useState("");
  const [note, setNote] = useState("");
  const setStatusM = useMutation({
    mutationFn: () => authFetch<InquiryDetail>(`/manager/inquiries/${id}/status`, { method: "POST", body: JSON.stringify({ status, comment: note || null }) }),
    onSuccess: (d) => { qc.setQueryData(key, d); setStatus(""); setNote(""); toast(`Статус: ${d.status_label}`, "success"); },
    onError: (e) => toast((e as Error).message, "error"),
  });
  const assign = useMutation({
    mutationFn: (assigned_to_id: number | null) => authFetch<InquiryDetail>(`/manager/inquiries/${id}`, { method: "PATCH", body: JSON.stringify({ assigned_to_id }) }),
    onSuccess: (d) => { qc.setQueryData(key, d); toast("Ответственный изменён", "success"); },
    onError: (e) => toast((e as Error).message, "error"),
  });
  if (q.isLoading) return <p className="muted">Загрузка…</p>;
  if (q.error || !q.data) return <p className="field__error">{(q.error as Error)?.message ?? "Заявка не найдена"}</p>;
  const d = q.data;
  return (
    <InquiryDetailView data={d} apiBase="/manager" queryKey={key} canUploadKinds={{ accept: ".pdf", label: "Загрузить предложение (PDF)" }}>
      <div className={styles.actions}>
        <div className={styles.block}>
          <label className="field__label">Ответственный</label>
          <select className="select" value={d.assigned_to?.id ?? ""} onChange={(e) => assign.mutate(e.target.value ? Number(e.target.value) : null)} disabled={assign.isPending}>
            <option value="">Не назначен</option>{managers.data?.map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}
          </select>
        </div>
        <form className={styles.block} onSubmit={(e) => { e.preventDefault(); if (status) setStatusM.mutate(); }}>
          <label className="field__label">Изменить статус</label>
          <div className={styles.row}>
            <select className="select" value={status} onChange={(e) => setStatus(e.target.value)} required>
              <option value="">Выберите…</option>{d.allowed_transitions.map((s) => <option key={s} value={s}>{STATUS_LABELS[s]}</option>)}
            </select>
            <input className="input" value={note} onChange={(e) => setNote(e.target.value)} placeholder="Комментарий для клиента (необязательно)" />
            <button className="btn btn--primary" type="submit" disabled={!status || setStatusM.isPending}>Применить</button>
          </div>
          {d.allowed_transitions.length === 0 && <span className="field__hint">Из этого статуса переходов нет.</span>}
        </form>
      </div>
    </InquiryDetailView>
  );
}
