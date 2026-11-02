import Link from "next/link";
import { api, mediaUrl } from "@/lib/api";
import styles from "@/app/page.module.scss";
export const metadata = { title: "Услуги", description: "Услуги компании Дортех: аренда спецтехники с экипажем и без, земляные работы, перевозки." };
export default async function Page() {
  const items = await api.services();
  return (
    <div className="container section"><h1>Услуги</h1>
      <div className={styles.cards3}>{items.map((s) => { const img = mediaUrl(s.cover_url); return (
        <Link key={s.slug} href={`/services/${s.slug}`} className={styles.card}>{img && <img src={img} alt="" width={900} height={600} loading="lazy" />}<span className={styles.cardBody}><b>{s.title}</b><span className="muted">{s.short_description}</span></span></Link>); })}</div>
    </div>
  );
}
