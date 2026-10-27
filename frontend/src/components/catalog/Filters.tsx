"use client";
import { useRouter, usePathname, useSearchParams } from "next/navigation";
import { useState, useTransition } from "react";
import type { Facets } from "@/lib/types";
import styles from "./Filters.module.scss";

export function Filters({ facets, basePath }: { facets: Facets; basePath: string }) {
  const router = useRouter();
  const pathname = usePathname();
  const sp = useSearchParams();
  const [open, setOpen] = useState(false);
  const [pending, start] = useTransition();

  const current = new URLSearchParams(sp.toString());
  const getList = (k: string) => (current.get(k) ?? "").split(",").filter(Boolean);
  const push = (params: URLSearchParams) => {
    params.delete("page");
    start(() => router.push(`${pathname}?${params.toString()}`, { scroll: false }));
  };
  const toggleList = (k: string, v: string) => {
    const p = new URLSearchParams(current);
    const list = getList(k);
    const next = list.includes(v) ? list.filter((x) => x !== v) : [...list, v];
    if (next.length) p.set(k, next.join(",")); else p.delete(k);
    push(p);
  };
  const setValue = (k: string, v: string) => {
    const p = new URLSearchParams(current);
    if (v) p.set(k, v); else p.delete(k);
    push(p);
  };
  const reset = () => start(() => router.push(basePath));
  const active = [...current.keys()].filter((k) => !["page", "ordering", "q"].includes(k)).length;

  const body = (
    <div className={styles.body} aria-busy={pending}>
      {facets.categories.length > 0 && !basePath.startsWith("/catalog/") && (
        <fieldset className={styles.group}><legend>Категория</legend>
          {facets.categories.map((c) => <a key={c.value} className={styles.link} href={`/catalog/${c.value}`}>{c.label} <span>{c.count}</span></a>)}
        </fieldset>
      )}
      {facets.manufacturers.length > 0 && (
        <fieldset className={styles.group}><legend>Производитель</legend>
          {facets.manufacturers.map((m) => (
            <label key={m.value} className={styles.check}><input type="checkbox" checked={getList("manufacturer").includes(m.value)} onChange={() => toggleList("manufacturer", m.value)} /> {m.label} <span>{m.count}</span></label>
          ))}
        </fieldset>
      )}
      {facets.statuses.length > 0 && (
        <fieldset className={styles.group}><legend>Доступность</legend>
          {facets.statuses.map((s) => (
            <label key={s.value} className={styles.check}><input type="checkbox" checked={getList("status").includes(s.value)} onChange={() => toggleList("status", s.value)} /> {s.label} <span>{s.count}</span></label>
          ))}
        </fieldset>
      )}
      {facets.attributes.map((a) => (
        <fieldset key={a.code} className={styles.group}><legend>{a.name}{a.unit ? `, ${a.unit}` : ""}</legend>
          {a.type === "choice" && a.options.map((o) => (
            <label key={o.value} className={styles.check}><input type="checkbox" checked={getList(`attr_${a.code}`).includes(o.value)} onChange={() => toggleList(`attr_${a.code}`, o.value)} /> {o.label} <span>{o.count}</span></label>
          ))}
          {a.type === "bool" && (
            <label className={styles.check}><input type="checkbox" checked={current.get(`attr_${a.code}`) === "true"} onChange={(e) => setValue(`attr_${a.code}`, e.target.checked ? "true" : "")} /> Да</label>
          )}
          {a.type === "number" && (
            <div className={styles.range}>
              <input type="number" inputMode="decimal" className="input" placeholder={`от ${a.min ?? ""}`} defaultValue={current.get(`attr_${a.code}_min`) ?? ""} onBlur={(e) => setValue(`attr_${a.code}_min`, e.target.value)} aria-label={`${a.name} от`} />
              <input type="number" inputMode="decimal" className="input" placeholder={`до ${a.max ?? ""}`} defaultValue={current.get(`attr_${a.code}_max`) ?? ""} onBlur={(e) => setValue(`attr_${a.code}_max`, e.target.value)} aria-label={`${a.name} до`} />
            </div>
          )}
        </fieldset>
      ))}
      {active > 0 && <button type="button" className="btn btn--outline btn--sm btn--block" onClick={reset}>Сбросить фильтры</button>}
    </div>
  );

  return (
    <>
      <button type="button" className={`btn btn--outline ${styles.toggle}`} onClick={() => setOpen(true)}>Фильтры{active ? ` (${active})` : ""}</button>
      <aside className={styles.desktop}>{body}</aside>
      {open && (
        <div className={styles.sheet} role="dialog" aria-label="Фильтры">
          <div className={styles.sheetHead}><b>Фильтры</b><button type="button" className="btn btn--ghost btn--sm" onClick={() => setOpen(false)}>Закрыть</button></div>
          {body}
          <button type="button" className="btn btn--primary btn--block" onClick={() => setOpen(false)}>Показать</button>
        </div>
      )}
    </>
  );
}
