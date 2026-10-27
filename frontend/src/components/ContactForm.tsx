"use client";
import { useState } from "react";
import Link from "next/link";
import { api, ApiError } from "@/lib/api";
import { toast } from "@/components/ui/Toast";

export function ContactForm() {
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  if (done) return <p className="muted">Спасибо! Сообщение отправлено, мы свяжемся с вами.</p>;
  return (
    <form onSubmit={async (e) => {
      e.preventDefault(); setBusy(true); setErr(null);
      const f = new FormData(e.currentTarget);
      try {
        await api.contactMessage({ name: String(f.get("name") ?? ""), phone: String(f.get("phone") ?? "") || undefined, email: String(f.get("email") ?? "") || undefined, text: String(f.get("text") ?? ""), consent: f.get("consent") === "on", website: String(f.get("website") ?? "") });
        setDone(true); toast("Сообщение отправлено", "success");
      } catch (ex) { setErr(ex instanceof ApiError ? ex.message : "Не удалось отправить. Попробуйте позже."); }
      finally { setBusy(false); }
    }}>
      <div className="field"><label className="field__label" htmlFor="c-name">Имя *</label><input id="c-name" name="name" className="input" required minLength={2} /></div>
      <div className="field"><label className="field__label" htmlFor="c-phone">Телефон</label><input id="c-phone" name="phone" className="input" type="tel" /></div>
      <div className="field"><label className="field__label" htmlFor="c-email">Email</label><input id="c-email" name="email" className="input" type="email" /></div>
      <div className="field"><label className="field__label" htmlFor="c-text">Сообщение *</label><textarea id="c-text" name="text" className="textarea" required minLength={5} /></div>
      <input type="text" name="website" tabIndex={-1} autoComplete="off" style={{ position: "absolute", left: -9999 }} aria-hidden="true" />
      <label className="field" style={{ flexDirection: "row", gap: 8, alignItems: "flex-start" }}><input type="checkbox" name="consent" required style={{ marginTop: 4 }} /><span className="field__hint">Согласен на обработку персональных данных в соответствии с <Link href="/privacy">политикой</Link></span></label>
      {err && <p className="field__error">{err}</p>}
      <button className="btn btn--primary" type="submit" disabled={busy}>{busy ? "Отправка…" : "Отправить"}</button>
    </form>
  );
}
