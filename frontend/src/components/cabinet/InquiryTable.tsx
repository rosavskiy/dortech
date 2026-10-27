import Link from "next/link";
import { money } from "@/lib/api";
import type { InquiryBrief } from "@/lib/cabinet-types";
import styles from "./InquiryTable.module.scss";

export const STATUS_COLORS: Record<string, string> = { new: "#2563eb", clarification: "#d97706", offer_sent: "#7c3aed", agreed: "#059669", completed: "#374151", cancelled: "#9ca3af" };

export function StatusBadge({ status, label }: { status: string; label: string }) {
  return <span className={styles.badge} style={{ background: STATUS_COLORS[status] ?? "#666" }}>{label}</span>;
}

export function InquiryTable({ items, base, manager = false }: { items: InquiryBrief[]; base: string; manager?: boolean }) {
  if (!items.length) return <p className="muted">Заявок пока нет.</p>;
  return (
    <div className={styles.wrap}>
      <table className={styles.table}>
        <thead><tr><th>Номер</th><th>Дата</th><th>Статус</th>{manager && <th>Организация</th>}<th>Период</th><th>Позиций</th><th>Сумма</th>{manager && <th>Ответственный</th>}</tr></thead>
        <tbody>
          {items.map((i) => (
            <tr key={i.public_id}>
              <td data-label="Номер"><Link href={`${base}/${i.public_id}`} className={styles.num}>{i.number}</Link></td>
              <td data-label="Дата">{new Date(i.created_at).toLocaleDateString("ru-RU")}</td>
              <td data-label="Статус"><StatusBadge status={i.status} label={i.status_label} /></td>
              {manager && <td data-label="Организация">{i.organization ?? "—"}<br /><small className="muted">{i.contact_name}</small></td>}
              <td data-label="Период">{i.period_from ? `${new Date(i.period_from).toLocaleDateString("ru-RU")} — ${i.period_to ? new Date(i.period_to).toLocaleDateString("ru-RU") : ""}` : "—"}</td>
              <td data-label="Позиций">{i.items_count}</td>
              <td data-label="Сумма">{i.estimated_total !== null ? `${i.is_partial ? "от " : ""}${money(i.estimated_total)}` : "по запросу"}</td>
              {manager && <td data-label="Ответственный">{i.assigned_to?.name ?? <span className="muted">не назначен</span>}</td>}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
