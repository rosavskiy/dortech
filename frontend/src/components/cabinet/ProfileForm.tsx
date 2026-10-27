"use client";
import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useSession } from "@/components/auth/SessionProvider";
import { authFetch, type Me } from "@/lib/auth";
import { toast } from "@/components/ui/Toast";

function F({ name, label, def, required = false, type = "text" }: { name: string; label: string; def?: string | null; required?: boolean; type?: string }) {
  return (
    <div className="field"><label className="field__label" htmlFor={name}>{label}{required ? " *" : ""}</label><input id={name} name={name} type={type} className="input" defaultValue={def ?? ""} required={required} /></div>
  );
}

export function ProfileForm() {
  const me = useSession();
  const qc = useQueryClient();
  const [busy, setBusy] = useState(false);
  const o = me.organization;
  return (
    <form style={{ maxWidth: 640 }} onSubmit={async (e) => {
      e.preventDefault(); setBusy(true);
      const f = new FormData(e.currentTarget);
      const body = Object.fromEntries([...f.entries()].map(([k, v]) => [k, String(v) || null]));
      try { const upd = await authFetch<Me>("/account/profile", { method: "PATCH", body: JSON.stringify(body) }); qc.setQueryData(["me"], upd); toast("Профиль сохранён", "success"); }
      catch (ex) { toast((ex as Error).message, "error"); } finally { setBusy(false); }
    }}>
      <h1>Профиль организации</h1>
      <h2 style={{ fontSize: 20 }}>Организация</h2>
      <F name="org_name" label="Название" def={o?.name} required />
      <div style={{ display: "grid", gap: "0 16px", gridTemplateColumns: "1fr 1fr" }}><F name="org_inn" label="ИНН" def={o?.inn} /><F name="org_kpp" label="КПП" def={o?.kpp} /></div>
      <F name="org_legal_address" label="Юридический адрес" def={o?.legal_address} />
      <div style={{ display: "grid", gap: "0 16px", gridTemplateColumns: "1fr 1fr" }}><F name="org_phone" label="Телефон организации" def={o?.phone} type="tel" /><F name="org_email" label="Email организации" def={o?.email} type="email" /></div>
      <h2 style={{ fontSize: 20, marginTop: 24 }}>Контактное лицо</h2>
      <div style={{ display: "grid", gap: "0 16px", gridTemplateColumns: "1fr 1fr 1fr" }}><F name="last_name" label="Фамилия" def={me.last_name} required /><F name="first_name" label="Имя" def={me.first_name} required /><F name="patronymic" label="Отчество" def={me.patronymic} /></div>
      <div style={{ display: "grid", gap: "0 16px", gridTemplateColumns: "1fr 1fr" }}><F name="phone" label="Телефон" def={me.phone} type="tel" /><F name="position" label="Должность" def={me.position} /></div>
      <p className="field__hint">Email для входа: {me.email}. Для смены email обратитесь к менеджеру.</p>
      <button className="btn btn--primary" type="submit" disabled={busy}>{busy ? "Сохранение…" : "Сохранить"}</button>
    </form>
  );
}
