"use client";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { apiFetch, ApiError } from "@/lib/api";
import { homeFor, type Me } from "@/lib/auth";
import styles from "./AuthForm.module.scss";

export function ResetRequestForm() {
  const [done, setDone] = useState(false);
  const [busy, setBusy] = useState(false);
  if (done) return <div className={`${styles.wrap} ${styles.success}`}><h1>Проверьте почту</h1><p>Если адрес зарегистрирован, мы отправили письмо со ссылкой для смены пароля.</p><Link href="/login" className="btn btn--outline">К входу</Link></div>;
  return (
    <div className={styles.wrap}><h1>Восстановление пароля</h1>
      <form className={styles.card} onSubmit={async (e) => { e.preventDefault(); setBusy(true); const f = new FormData(e.currentTarget); try { await apiFetch("/auth/password-reset", { method: "POST", body: JSON.stringify({ email: String(f.get("email") ?? "") }) }); } catch { /* всегда успех */ } setDone(true); setBusy(false); }}>
        <div className="field"><label className="field__label" htmlFor="email">Email</label><input id="email" name="email" type="email" className="input" required /></div>
        <button className="btn btn--primary btn--block" type="submit" disabled={busy}>Отправить ссылку</button>
        <div className={styles.links}><Link href="/login">Вспомнили пароль? Войти</Link></div>
      </form>
    </div>
  );
}

export function ResetConfirmForm() {
  const sp = useSearchParams();
  const router = useRouter();
  const qc = useQueryClient();
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  return (
    <div className={styles.wrap}><h1>Новый пароль</h1>
      <form className={styles.card} onSubmit={async (e) => {
        e.preventDefault(); setBusy(true); setErr(null);
        const f = new FormData(e.currentTarget);
        const p1 = String(f.get("password") ?? ""), p2 = String(f.get("password2") ?? "");
        if (p1 !== p2) { setErr("Пароли не совпадают"); setBusy(false); return; }
        try {
          const me = await apiFetch<Me>("/auth/password-reset/confirm", { method: "POST", body: JSON.stringify({ token: sp.get("token") ?? "", password: p1 }), credentials: "same-origin" });
          qc.setQueryData(["me"], me); router.push(homeFor(me)); router.refresh();
        } catch (ex) { setErr(ex instanceof ApiError ? ex.message : "Не удалось сменить пароль"); } finally { setBusy(false); }
      }}>
        <div className="field"><label className="field__label" htmlFor="password">Пароль</label><input id="password" name="password" type="password" className="input" required minLength={8} autoComplete="new-password" /></div>
        <div className="field"><label className="field__label" htmlFor="password2">Повторите пароль</label><input id="password2" name="password2" type="password" className="input" required minLength={8} autoComplete="new-password" /></div>
        {err && <p className="field__error">{err}</p>}
        <button className="btn btn--primary btn--block" type="submit" disabled={busy}>Сохранить</button>
      </form>
    </div>
  );
}
