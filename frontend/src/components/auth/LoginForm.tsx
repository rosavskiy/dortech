"use client";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { apiFetch, ApiError } from "@/lib/api";
import { homeFor, type Me } from "@/lib/auth";
import styles from "./AuthForm.module.scss";

export function LoginForm() {
  const router = useRouter();
  const sp = useSearchParams();
  const qc = useQueryClient();
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [needConfirm, setNeedConfirm] = useState<string | null>(null);
  return (
    <div className={styles.wrap}>
      <h1>Вход в кабинет</h1>
      <form className={styles.card} onSubmit={async (e) => {
        e.preventDefault(); setBusy(true); setErr(null); setNeedConfirm(null);
        const f = new FormData(e.currentTarget);
        const email = String(f.get("email") ?? "");
        try {
          const me = await apiFetch<Me>("/auth/login", { method: "POST", body: JSON.stringify({ email, password: String(f.get("password") ?? "") }), credentials: "same-origin" });
          qc.setQueryData(["me"], me);
          const next = sp.get("next");
          router.push(next && next.startsWith("/") ? next : homeFor(me));
          router.refresh();
        } catch (ex) {
          const msg = ex instanceof ApiError ? ex.message : "Не удалось войти";
          setErr(msg);
          if (msg.includes("Подтвердите email")) setNeedConfirm(email);
        } finally { setBusy(false); }
      }}>
        <div className="field"><label className="field__label" htmlFor="email">Email</label><input id="email" name="email" type="email" className="input" required autoComplete="email" /></div>
        <div className="field"><label className="field__label" htmlFor="password">Пароль</label><input id="password" name="password" type="password" className="input" required autoComplete="current-password" /></div>
        {err && <p className="field__error">{err}{needConfirm && <> · <button type="button" className="btn btn--ghost btn--sm" onClick={async () => { await apiFetch("/auth/resend-confirmation", { method: "POST", body: JSON.stringify({ email: needConfirm }) }); setErr("Письмо отправлено повторно"); }}>отправить письмо ещё раз</button></>}</p>}
        <button className="btn btn--primary btn--block" type="submit" disabled={busy}>{busy ? "Входим…" : "Войти"}</button>
        <div className={styles.links}><Link href="/password-reset">Забыли пароль?</Link><span>Нет кабинета? <Link href="/register">Зарегистрироваться</Link></span></div>
      </form>
    </div>
  );
}
