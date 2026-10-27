"use client";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { apiFetch, ApiError } from "@/lib/api";
import { homeFor, type Me } from "@/lib/auth";
import styles from "./AuthForm.module.scss";

export function ConfirmEmail() {
  const sp = useSearchParams();
  const router = useRouter();
  const qc = useQueryClient();
  const token = sp.get("token");
  const [state, setState] = useState<"work" | "ok" | "err">(token ? "work" : "err");
  const [err, setErr] = useState(token ? "" : "Нет токена подтверждения");
  useEffect(() => {
    if (!token) return;
    apiFetch<Me>("/auth/confirm-email", { method: "POST", body: JSON.stringify({ token }), credentials: "same-origin" })
      .then((me) => { qc.setQueryData(["me"], me); setState("ok"); setTimeout(() => { router.push(homeFor(me)); router.refresh(); }, 1200); })
      .catch((ex) => { setState("err"); setErr(ex instanceof ApiError ? ex.message : "Не удалось подтвердить email"); });
  }, [token, router, qc]);
  return (
    <div className={`${styles.wrap} ${styles.success}`}>
      {state === "work" && <><h1>Подтверждаем email…</h1><p className="muted">Секунду.</p></>}
      {state === "ok" && <><h1>Email подтверждён</h1><p>Переходим в кабинет…</p></>}
      {state === "err" && <><h1>Не удалось подтвердить</h1><p className="field__error">{err}</p><Link href="/login" className="btn btn--outline">К входу</Link></>}
    </div>
  );
}
