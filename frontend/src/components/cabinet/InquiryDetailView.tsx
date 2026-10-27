"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { money } from "@/lib/api";
import { authFetch } from "@/lib/auth";
import { cart } from "@/lib/cart";
import { fmtDate, fmtSize, type InquiryDetail } from "@/lib/cabinet-types";
import { toast } from "@/components/ui/Toast";
import { StatusBadge } from "./InquiryTable";
import styles from "./InquiryDetailView.module.scss";

/** Общая часть детали заявки для клиента и менеджера. */
export function InquiryDetailView({ data, apiBase, queryKey, canUploadKinds, children }: {
  data: InquiryDetail; apiBase: string; queryKey: unknown[]; canUploadKinds: { accept: string; label: string } | null; children?: React.ReactNode;
}) {
  const qc = useQueryClient();
  const router = useRouter();
  const [internal, setInternal] = useState(false);
  const isManager = apiBase.startsWith("/manager");
  const comment = useMutation({
    mutationFn: (text: string) => authFetch<InquiryDetail>(`${apiBase}/inquiries/${data.public_id}/comments`, { method: "POST", body: JSON.stringify({ text, is_internal: internal }) }),
    onSuccess: (d) => { qc.setQueryData(queryKey, d); toast("Комментарий добавлен", "success"); },
    onError: (e) => toast((e as Error).message, "error"),
  });
  const upload = useMutation({
    mutationFn: (file: File) => { const fd = new FormData(); fd.append("file", file); return authFetch<InquiryDetail>(`${apiBase}/inquiries/${data.public_id}/files`, { method: "POST", body: fd }); },
    onSuccess: (d) => { qc.setQueryData(queryKey, d); toast("Файл загружен", "success"); },
    onError: (e) => toast((e as Error).message, "error"),
  });
  const repeat = () => {
    cart.replace(data.items.map((i) => ({ equipment_id: i.equipment_id, slug: i.slug ?? "", name: i.name, model: i.model, image: null, quantity: i.quantity, unit: i.unit, units: i.units })));
    try { sessionStorage.setItem("dt_repeat_parent", data.public_id); } catch { /* ignore */ }
    router.push("/request");
  };
  return (
    <div className={styles.wrap}>
      <div className={styles.head}>
        <div><Link href={`${isManager ? "/manager" : "/account"}/inquiries`} className="muted">← К списку</Link><h1>Заявка {data.number}</h1>
          <div className={styles.meta}><StatusBadge status={data.status} label={data.status_label} /><span className="muted">от {fmtDate(data.created_at)}</span>{data.parent_number && <span className="muted">повтор {data.parent_number}</span>}</div></div>
        {!isManager && <button type="button" className="btn btn--outline" onClick={repeat}>Повторить заявку</button>}
      </div>
      {children}
      <div className={styles.grid}>
        <section className={styles.card}>
          <h2>Состав</h2>
          <table className={styles.items}><tbody>
            {data.items.map((i) => <tr key={i.equipment_id}><td>{i.slug ? <Link href={`/equipment/${i.slug}`}>{i.name}</Link> : i.name}<br /><small className="muted">{i.quantity} × {i.units} {i.unit === "shift" ? "см." : "сут."}{i.unit_price ? ` × ${money(i.unit_price)}` : ""}</small></td><td className={styles.sum}>{i.needs_quote ? "по запросу" : money(i.line_total)}</td></tr>)}
            {data.extras.map((e) => <tr key={e.name}><td>{e.name}</td><td className={styles.sum}>{money(e.price)}</td></tr>)}
            <tr className={styles.total}><td>Предварительно{data.vat_label ? `, ${data.vat_label}` : ""}</td><td className={styles.sum}>{data.total_label}</td></tr>
          </tbody></table>
        </section>
        <section className={styles.card}>
          <h2>Детали</h2>
          <dl className={styles.dl}>
            <dt>Период</dt><dd>{data.period_from ? `${new Date(data.period_from).toLocaleDateString("ru-RU")} — ${data.period_to ? new Date(data.period_to).toLocaleDateString("ru-RU") : "…"}` : "не указан"}</dd>
            <dt>Место работ</dt><dd>{data.work_place || "не указано"}</dd>
            <dt>Контакт</dt><dd>{data.contact_name}, {data.contact_phone}{data.contact_email ? `, ${data.contact_email}` : ""}</dd>
            {data.organization && <><dt>Организация</dt><dd>{data.organization}</dd></>}
            <dt>Ответственный</dt><dd>{data.assigned_to?.name ?? "не назначен"}</dd>
            {data.comment && <><dt>Комментарий</dt><dd>{data.comment}</dd></>}
          </dl>
        </section>
        <section className={styles.card}>
          <h2>Файлы</h2>
          {data.attachments.length ? (
            <ul className={styles.files}>{data.attachments.map((a) => <li key={a.public_id}><a href={a.download_url}>{a.original_name}</a><small className="muted">{a.kind === "offer_pdf" ? "предложение" : "документ"} · {fmtSize(a.size)} · {a.uploaded_by ?? ""} · {fmtDate(a.created_at)}</small></li>)}</ul>
          ) : <p className="muted">Файлов нет.</p>}
          {canUploadKinds && (
            <label className={`btn btn--outline btn--sm ${upload.isPending ? "" : ""}`}>{upload.isPending ? "Загрузка…" : canUploadKinds.label}
              <input type="file" accept={canUploadKinds.accept} hidden disabled={upload.isPending} onChange={(e) => { const f = e.target.files?.[0]; if (f) upload.mutate(f); e.target.value = ""; }} /></label>
          )}
          <p className="field__hint">До 20 МБ: pdf, doc, docx, xls, xlsx, jpg, png.</p>
        </section>
        <section className={styles.card}>
          <h2>История</h2>
          <ul className={styles.timeline}>{data.history.map((h, i) => <li key={i}><b>{h.to_label}</b><span className="muted">{fmtDate(h.created_at)}{h.changed_by ? ` · ${h.changed_by}` : ""}</span>{h.comment && <small>{h.comment}</small>}</li>)}</ul>
        </section>
      </div>
      <section className={styles.card}>
        <h2>Комментарии</h2>
        {data.comments.length ? (
          <ul className={styles.comments}>{data.comments.map((c) => <li key={c.id} className={c.is_internal ? styles.internal : c.is_staff ? styles.staff : ""}><div className={styles.cHead}><b>{c.author}</b><span className="muted">{fmtDate(c.created_at)}</span>{c.is_internal && <span className={styles.tag}>внутренний</span>}</div><p>{c.text}</p></li>)}</ul>
        ) : <p className="muted">Комментариев нет.</p>}
        <form onSubmit={(e) => { e.preventDefault(); const f = new FormData(e.currentTarget); const t = String(f.get("text") ?? "").trim(); if (t) { comment.mutate(t); e.currentTarget.reset(); } }}>
          <div className="field"><textarea name="text" className="textarea" placeholder="Написать комментарий" required style={{ minHeight: 80 }} /></div>
          <div className={styles.cActions}>
            {isManager && <label style={{ display: "flex", gap: 8, alignItems: "center", fontSize: 14 }}><input type="checkbox" checked={internal} onChange={(e) => setInternal(e.target.checked)} /> Внутренний (не виден клиенту)</label>}
            <button className="btn btn--primary btn--sm" type="submit" disabled={comment.isPending}>Отправить</button>
          </div>
        </form>
      </section>
    </div>
  );
}
