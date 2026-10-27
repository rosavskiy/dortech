"use client";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { api, mediaUrl } from "@/lib/api";
import { cart, useCart } from "@/lib/cart";
import { CardActions } from "./CardActions";
import styles from "./CompareView.module.scss";

export function CompareView() {
  const { compare, hydrated } = useCart();
  const q = useQuery({ queryKey: ["compare", compare], queryFn: () => api.compare(compare), enabled: hydrated && compare.length > 0 });
  if (!hydrated) return null;
  if (!compare.length) return <div className={styles.empty}><p>Добавьте до четырёх карточек из каталога, чтобы сравнить характеристики.</p><Link href="/catalog" className="btn btn--primary">В каталог</Link></div>;
  if (q.isLoading) return <p className="muted">Загрузка…</p>;
  if (!q.data) return <p className="field__error">Не удалось загрузить сравнение.</p>;
  const { items, rows } = q.data;
  return (
    <div className={styles.wrap}>
      <div className={styles.actions}><span className="muted">{items.length} из 4</span><button type="button" className="btn btn--ghost btn--sm" onClick={() => cart.clearCompare()}>Очистить</button></div>
      <div className={styles.scroll}>
        <table className={styles.table}>
          <thead><tr><th scope="col" />{items.map((e) => { const img = mediaUrl(e.image?.url); return (
            <th key={e.id} scope="col"><div className={styles.head}>{img && <img src={img} alt="" width={300} height={200} />}<Link href={`/equipment/${e.slug}`}>{e.name}</Link><CardActions item={e} /><button type="button" className={styles.rm} onClick={() => cart.toggleCompare(e.id)}>Убрать</button></div></th>); })}</tr></thead>
          <tbody>{rows.map((r) => <tr key={r.code}><th scope="row">{r.name}{r.unit ? `, ${r.unit}` : ""}</th>{r.values.map((v, i) => <td key={i}>{v ?? "—"}</td>)}</tr>)}</tbody>
        </table>
      </div>
    </div>
  );
}
