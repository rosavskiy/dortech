"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { money } from "@/lib/api";
import type { InquiryCreatedOut } from "@/lib/types";

export function SuccessView() {
  const [res, setRes] = useState<InquiryCreatedOut | null | undefined>(undefined);
  useEffect(() => { try { const raw = sessionStorage.getItem("dt_last_inquiry"); setRes(raw ? JSON.parse(raw) : null); } catch { setRes(null); } }, []);
  if (res === undefined) return null;
  if (!res) return <div style={{ textAlign: "center" }}><h1>Заявка отправлена</h1><Link href="/catalog" className="btn btn--primary">В каталог</Link></div>;
  return (
    <div style={{ maxWidth: 640, margin: "0 auto", textAlign: "center" }}>
      <h1>Заявка {res.number} принята</h1>
      <p>Мы получили вашу заявку и свяжемся с вами в ближайшее время{res.estimate.lines.length ? `. Предварительная стоимость: ${res.estimate.is_partial ? "от " : ""}${money(res.estimate.total)} ${res.estimate.vat_label}` : ""}.</p>
      <p className="muted">{res.estimate.disclaimer}</p>
      <div style={{ display: "flex", gap: 8, justifyContent: "center", flexWrap: "wrap" }}>
        <Link href="/catalog" className="btn btn--primary">Вернуться в каталог</Link>
        <Link href="/register" className="btn btn--outline">Создать личный кабинет</Link>
      </div>
    </div>
  );
}
