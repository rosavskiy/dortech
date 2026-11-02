import Link from "next/link";
import { api, mediaUrl } from "@/lib/api";
import styles from "@/app/page.module.scss";
export const metadata = { title: "Выполненные проекты", description: "Объекты, на которых работала техника Дортех." };
export default async function Page() {
  const items = await api.projects();
  return (
    <div className="container section"><h1>Выполненные проекты</h1>
      <div className={styles.cards3}>{items.map((p) => { const img = mediaUrl(p.cover_url); return (
        <Link key={p.slug} href={`/projects/${p.slug}`} className={styles.card}>{img && <img src={img} alt="" width={900} height={600} loading="lazy" />}<span className={styles.cardBody}><small className="muted">{[p.year, p.location].filter(Boolean).join(" · ")}</small><b>{p.title}</b></span></Link>); })}</div>
    </div>
  );
}
