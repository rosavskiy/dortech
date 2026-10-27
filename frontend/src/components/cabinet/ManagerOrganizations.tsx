"use client";
import Link from "next/link";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { authFetch } from "@/lib/auth";
type Org = { id: number; name: string; inn: string | null; kpp: string | null; legal_address: string | null; phone: string | null; email: string | null };
export function ManagerOrganizations() {
  const [q, setQ] = useState("");
  const list = useQuery({ queryKey: ["orgs", q], queryFn: () => authFetch<Org[]>(`/manager/organizations?q=${encodeURIComponent(q)}`) });
  return (
    <div>
      <h1>Организации</h1>
      <input className="input" placeholder="Поиск по названию или ИНН" value={q} onChange={(e) => setQ(e.target.value)} style={{ maxWidth: 420, marginBottom: 16 }} />
      {list.isLoading ? <p className="muted">Загрузка…</p> : (
        <div style={{ display: "grid", gap: 12 }}>
          {list.data?.map((o) => (
            <div key={o.id} style={{ border: "1px solid #e5e5e5", borderRadius: 8, padding: 16, display: "flex", justifyContent: "space-between", gap: 16, flexWrap: "wrap" }}>
              <div><b>{o.name}</b><div className="muted" style={{ fontSize: 14 }}>{[o.inn && `ИНН ${o.inn}`, o.kpp && `КПП ${o.kpp}`, o.phone, o.email].filter(Boolean).join(" · ")}</div>{o.legal_address && <div className="muted" style={{ fontSize: 14 }}>{o.legal_address}</div>}</div>
              <Link href={`/manager/inquiries?organization=${o.id}`} className="btn btn--outline btn--sm">Заявки</Link>
            </div>
          ))}
          {list.data?.length === 0 && <p className="muted">Ничего не найдено.</p>}
        </div>
      )}
    </div>
  );
}
