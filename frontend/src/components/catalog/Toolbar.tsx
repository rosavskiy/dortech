"use client";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";
import styles from "./Toolbar.module.scss";

export function Toolbar({ total }: { total: number }) {
  const router = useRouter();
  const pathname = usePathname();
  const sp = useSearchParams();
  const [q, setQ] = useState(sp.get("q") ?? "");
  const update = (k: string, v: string) => {
    const p = new URLSearchParams(sp.toString());
    if (v) p.set(k, v); else p.delete(k);
    p.delete("page");
    router.push(`${pathname}?${p.toString()}`, { scroll: false });
  };
  return (
    <div className={styles.bar}>
      <form className={styles.search} onSubmit={(e) => { e.preventDefault(); update("q", q.trim()); }} role="search">
        <input type="search" className="input" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Поиск по названию и модели" aria-label="Поиск" />
        <button className="btn btn--secondary" type="submit">Найти</button>
      </form>
      <div className={styles.right}>
        <span className="muted">{total} ед.</span>
        <label className={styles.sort}>Сортировка
          <select className="select" value={sp.get("ordering") ?? "default"} onChange={(e) => update("ordering", e.target.value === "default" ? "" : e.target.value)}>
            <option value="default">по порядку</option>
            <option value="name">по названию А–Я</option>
            <option value="-name">по названию Я–А</option>
            <option value="price">сначала дешевле</option>
            <option value="-price">сначала дороже</option>
            <option value="new">сначала новые</option>
          </select>
        </label>
      </div>
    </div>
  );
}
