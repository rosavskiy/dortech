"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api, ApiError, mediaUrl, money } from "@/lib/api";
import { cart, useCart, CART_LIMIT } from "@/lib/cart";
import type { EstimateIn, EstimateOut, RateUnit } from "@/lib/types";
import { toast } from "@/components/ui/Toast";
import styles from "./RequestForm.module.scss";

function useDebounced<T>(value: T, ms: number): T {
  const [v, setV] = useState(value);
  useEffect(() => { const t = setTimeout(() => setV(value), ms); return () => clearTimeout(t); }, [value, ms]);
  return v;
}

export function RequestForm() {
  const router = useRouter();
  const { items, hydrated } = useCart();
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [extras, setExtras] = useState<number[]>([]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const extraServices = useQuery({ queryKey: ["extra-services"], queryFn: api.extraServices });

  const estimateIn: EstimateIn | null = useMemo(() => items.length ? {
    items: items.map((i) => ({ equipment_id: i.equipment_id, quantity: i.quantity, unit: i.unit, units: i.units })),
    period_from: from || null, period_to: to || null, extra_service_ids: extras,
  } : null, [items, from, to, extras]);
  const debounced = useDebounced(estimateIn, 400);
  const est = useQuery<EstimateOut>({ queryKey: ["estimate", debounced], queryFn: () => api.estimate(debounced!), enabled: !!debounced });

  if (!hydrated) return <p className="muted">Загрузка…</p>;
  if (!items.length) return (
    <div className={styles.empty}><p>В заявке пока нет техники.</p><Link href="/catalog" className="btn btn--primary">Перейти в каталог</Link></div>
  );
  const periodDays = from && to && to >= from ? Math.round((new Date(to).getTime() - new Date(from).getTime()) / 86400000) + 1 : null;

  return (
    <form className={styles.layout} onSubmit={async (e) => {
      e.preventDefault(); setBusy(true); setErr(null);
      const f = new FormData(e.currentTarget);
      try {
        const res = await api.createInquiry({
          ...(estimateIn as EstimateIn),
          contact_name: String(f.get("contact_name") ?? ""), contact_phone: String(f.get("contact_phone") ?? ""),
          contact_email: String(f.get("contact_email") ?? "") || null, company_name: String(f.get("company_name") ?? "") || null,
          work_place: String(f.get("work_place") ?? "") || null, comment: String(f.get("comment") ?? "") || null,
          consent: f.get("consent") === "on", website: String(f.get("website") ?? ""),
        });
        try { sessionStorage.setItem("dt_last_inquiry", JSON.stringify(res)); } catch { /* ignore */ }
        cart.clear();
        router.push("/request/success");
      } catch (ex) {
        const msg = ex instanceof ApiError ? (typeof ex.detail === "object" && ex.detail && Array.isArray((ex.detail as { detail?: unknown }).detail) ? "Проверьте правильность заполнения полей" : ex.message) : "Не удалось отправить заявку";
        setErr(msg); toast(msg, "error");
      } finally { setBusy(false); }
    }}>
      <div className={styles.main}>
        <section>
          <h2>Техника <span className="muted" style={{ fontWeight: 400, fontSize: 14 }}>{items.length} из {CART_LIMIT}</span></h2>
          <div className={styles.items}>
            {items.map((i) => {
              const img = mediaUrl(i.image);
              const line = est.data?.lines.find((l) => l.equipment_id === i.equipment_id);
              return (
                <div key={i.equipment_id} className={styles.item}>
                  <Link href={`/equipment/${i.slug}`} className={styles.itemImg}>{img && <img src={img} alt="" width={160} height={107} />}</Link>
                  <Link href={`/equipment/${i.slug}`} className={styles.itemTitle}><b>{i.name}</b></Link>
                  <button type="button" className={styles.remove} aria-label="Убрать" onClick={() => cart.remove(i.equipment_id)}>×</button>
                  <div className={styles.itemControls}>
                    <label>Кол-во<input type="number" min={1} max={100} className="input" value={i.quantity} onChange={(e) => cart.update(i.equipment_id, { quantity: Math.max(1, Number(e.target.value) || 1) })} /></label>
                    <label>Тариф<select className="select" value={i.unit} onChange={(e) => cart.update(i.equipment_id, { unit: e.target.value as RateUnit })}><option value="shift">за смену</option><option value="day">за сутки</option></select></label>
                    <label>{i.unit === "shift" ? "Смен" : "Суток"}<input type="number" min={1} max={366} className="input" placeholder={periodDays ? String(periodDays) : "1"} value={i.units ?? ""} onChange={(e) => cart.update(i.equipment_id, { units: e.target.value ? Math.max(1, Number(e.target.value)) : null })} /></label>
                  </div>
                  <div className={styles.itemPrice}>{line ? (line.needs_quote ? "по запросу" : <>{money(line.unit_price)} × {line.units} × {line.quantity} = <b>{money(line.line_total)}</b></>) : ""}</div>
                </div>
              );
            })}
          </div>
          <Link href="/catalog" className="btn btn--ghost btn--sm">+ Добавить технику</Link>
        </section>

        <section>
          <h2>Период и место работ</h2>
          <div className={styles.row2}>
            <div className="field"><label className="field__label" htmlFor="from">Начало</label><input id="from" type="date" className="input" value={from} onChange={(e) => setFrom(e.target.value)} /></div>
            <div className="field"><label className="field__label" htmlFor="to">Окончание</label><input id="to" type="date" className="input" value={to} min={from || undefined} onChange={(e) => setTo(e.target.value)} /></div>
          </div>
          <div className="field"><label className="field__label" htmlFor="work_place">Место выполнения работ</label><input id="work_place" name="work_place" className="input" placeholder="Город, адрес объекта" /></div>
          {extraServices.data && extraServices.data.length > 0 && (
            <fieldset className={styles.extras}><legend className="field__label">Дополнительные услуги</legend>
              {extraServices.data.map((s) => (
                <label key={s.id}><input type="checkbox" checked={extras.includes(s.id)} onChange={(e) => setExtras((p) => e.target.checked ? [...p, s.id] : p.filter((x) => x !== s.id))} /> {s.name}{s.description ? <span className="muted"> — {s.description}</span> : null}<b>{money(s.price)}</b></label>
              ))}
            </fieldset>
          )}
        </section>

        <section>
          <h2>Контакты</h2>
          <div className={styles.row2}>
            <div className="field"><label className="field__label" htmlFor="contact_name">Контактное лицо *</label><input id="contact_name" name="contact_name" className="input" required minLength={2} autoComplete="name" /></div>
            <div className="field"><label className="field__label" htmlFor="contact_phone">Телефон *</label><input id="contact_phone" name="contact_phone" className="input" type="tel" required minLength={6} autoComplete="tel" /></div>
            <div className="field"><label className="field__label" htmlFor="contact_email">Email</label><input id="contact_email" name="contact_email" className="input" type="email" autoComplete="email" /></div>
            <div className="field"><label className="field__label" htmlFor="company_name">Организация</label><input id="company_name" name="company_name" className="input" autoComplete="organization" /></div>
          </div>
          <div className="field"><label className="field__label" htmlFor="comment">Комментарий</label><textarea id="comment" name="comment" className="textarea" /></div>
          <input type="text" name="website" tabIndex={-1} autoComplete="off" style={{ position: "absolute", left: -9999 }} aria-hidden="true" />
          <label className="field" style={{ flexDirection: "row", gap: 8, alignItems: "flex-start" }}><input type="checkbox" name="consent" required style={{ marginTop: 4 }} /><span className="field__hint">Согласен на обработку персональных данных в соответствии с <Link href="/privacy">политикой</Link></span></label>
        </section>
      </div>

      <aside className={styles.summary}>
        <h2>Предварительный расчёт</h2>
        {est.isFetching && !est.data && <p className="muted">Считаем…</p>}
        {est.data && (
          <>
            <ul className={styles.sumLines}>
              {est.data.lines.map((l) => <li key={l.equipment_id}><span>{l.name}</span><b>{l.needs_quote ? "по запросу" : money(l.line_total)}</b></li>)}
              {est.data.extras.map((x) => <li key={`x${x.id}`}><span>{x.name}</span><b>{money(x.price)}</b></li>)}
            </ul>
            <div className={styles.total}><span>Итого{est.data.is_partial ? " (от)" : ""}</span><b>{money(est.data.total)}</b></div>
            <small className="muted">{est.data.vat_label}. {est.data.disclaimer}</small>
          </>
        )}
        {err && <p className="field__error">{err}</p>}
        <button className="btn btn--primary btn--block" type="submit" disabled={busy}>{busy ? "Отправляем…" : "Отправить заявку"}</button>
        <small className="muted">Отправка заявки не является заключением договора. Менеджер свяжется с вами для подтверждения условий.</small>
      </aside>
    </form>
  );
}
