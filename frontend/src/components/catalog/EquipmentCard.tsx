import Link from "next/link";
import type { EquipmentCard as Card } from "@/lib/types";
import { money, mediaUrl } from "@/lib/api";
import { CardActions } from "./CardActions";
import styles from "./EquipmentCard.module.scss";

export function EquipmentCard({ item }: { item: Card }) {
  const img = mediaUrl(item.image?.url);
  return (
    <article className={styles.card}>
      <Link href={`/equipment/${item.slug}`} className={styles.media}>
        {img ? <img src={img} alt={item.image?.alt ?? item.name} loading="lazy" width={600} height={400} /> : <span className={styles.noimg}>Фото скоро</span>}
        {item.status && <span className={`${styles.status} ${styles["status_" + item.status.color]}`}>{item.status.name}</span>}
      </Link>
      <div className={styles.body}>
        <div className={styles.cat}>{item.category.name}{item.manufacturer ? ` · ${item.manufacturer.name}` : ""}</div>
        <h3 className={styles.title}><Link href={`/equipment/${item.slug}`}>{item.name}</Link></h3>
        {item.key_attributes.length > 0 && (
          <ul className={styles.attrs}>
            {item.key_attributes.map((a) => <li key={a.code}><span>{a.name}</span><b>{a.value}{a.unit ? ` ${a.unit}` : ""}</b></li>)}
          </ul>
        )}
        <div className={styles.price}>
          {item.tariff && !item.price_hidden ? (
            <><b>{money(item.tariff.price_per_shift)}</b><span> / смена</span></>
          ) : (
            <b>Цена по запросу</b>
          )}
        </div>
        <CardActions item={item} />
      </div>
    </article>
  );
}
