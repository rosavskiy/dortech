import Link from "next/link";
import { api, mediaUrl } from "@/lib/api";
import { Pagination } from "@/components/catalog/Pagination";
import styles from "@/app/page.module.scss";
export const metadata = { title: "Публикации", description: "Новости и статьи компании Дортех." };
export default async function Page(props: { searchParams: Promise<{ page?: string }> }) {
  const { page } = await props.searchParams;
  const list = await api.publications(Number(page) || 1);
  return (
    <div className="container section"><h1>Публикации</h1>
      <div className={styles.cards3}>{list.items.map((p) => { const img = mediaUrl(p.cover_url); return (
        <Link key={p.slug} href={`/publications/${p.slug}`} className={styles.card}>{img && <img src={img} alt="" width={900} height={600} loading="lazy" />}<span className={styles.cardBody}><small className="muted">{p.published_at ? new Date(p.published_at).toLocaleDateString("ru-RU") : ""}</small><b>{p.title}</b><span className="muted">{p.short_description}</span></span></Link>); })}</div>
      <Pagination page={list.page} pages={list.pages} basePath="/publications" sp={{}} />
    </div>
  );
}
