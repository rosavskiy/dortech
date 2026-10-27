"use client";
import Link from "next/link";
import { useState } from "react";
import { apiFetch, ApiError } from "@/lib/api";
import styles from "./AuthForm.module.scss";

export function RegisterForm() {
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [done, setDone] = useState(false);
  if (done) return <div className={`${styles.wrap} ${styles.success}`}><h1>Проверьте почту</h1><p>Мы отправили письмо со ссылкой для подтверждения email. Ссылка действует 24 часа.</p><Link href="/login" className="btn btn--outline">К входу</Link></div>;
  return (
    <div className={styles.wrap}>
      <h1>Регистрация</h1>
      <form className={styles.card} onSubmit={async (e) => {
        e.preventDefault(); setBusy(true); setErr(null);
        const f = new FormData(e.currentTarget);
        const body = Object.fromEntries(["email", "password", "first_name", "last_name", "phone", "company_name", "inn", "website"].map((k) => [k, String(f.get(k) ?? "")]));
        try {
          await apiFetch("/auth/register", { method: "POST", body: JSON.stringify({ ...body, phone: body.phone || null, inn: body.inn || null, consent: f.get("consent") === "on" }) });
          setDone(true);
        } catch (ex) {
          const d = ex instanceof ApiError ? ex.detail as { detail?: unknown } : null;
          setErr(Array.isArray(d?.detail) ? (d!.detail as { msg: string }[]).map((x) => x.msg.replace(/^Value error, /, "")).join("; ") : ex instanceof ApiError ? ex.message : "Ошибка регистрации");
        } finally { setBusy(false); }
      }}>
        <div className="field"><label className="field__label" htmlFor="company_name">Организация *</label><input id="company_name" name="company_name" className="input" required minLength={2} autoComplete="organization" /></div>
        <div className="field"><label className="field__label" htmlFor="inn">ИНН</label><input id="inn" name="inn" className="input" inputMode="numeric" pattern="[0-9]{10}|[0-9]{12}" title="10 или 12 цифр" /></div>
        <div className="field"><label className="field__label" htmlFor="last_name">Фамилия *</label><input id="last_name" name="last_name" className="input" required autoComplete="family-name" /></div>
        <div className="field"><label className="field__label" htmlFor="first_name">Имя *</label><input id="first_name" name="first_name" className="input" required autoComplete="given-name" /></div>
        <div className="field"><label className="field__label" htmlFor="phone">Телефон</label><input id="phone" name="phone" type="tel" className="input" autoComplete="tel" /></div>
        <div className="field"><label className="field__label" htmlFor="email">Email *</label><input id="email" name="email" type="email" className="input" required autoComplete="email" /></div>
        <div className="field"><label className="field__label" htmlFor="password">Пароль *</label><input id="password" name="password" type="password" className="input" required minLength={8} autoComplete="new-password" /><span className="field__hint">Не менее 8 символов, буквы и цифры</span></div>
        <input type="text" name="website" tabIndex={-1} autoComplete="off" style={{ position: "absolute", left: -9999 }} aria-hidden="true" />
        <label className="field" style={{ flexDirection: "row", gap: 8, alignItems: "flex-start" }}><input type="checkbox" name="consent" required style={{ marginTop: 4 }} /><span className="field__hint">Согласен на обработку персональных данных в соответствии с <Link href="/privacy">политикой</Link></span></label>
        {err && <p className="field__error">{err}</p>}
        <button className="btn btn--primary btn--block" type="submit" disabled={busy}>{busy ? "Отправка…" : "Зарегистрироваться"}</button>
        <div className={styles.links}><span>Уже есть кабинет? <Link href="/login">Войти</Link></span></div>
      </form>
    </div>
  );
}
