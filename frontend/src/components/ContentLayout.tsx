import Link from "next/link";
import styles from "./ContentLayout.module.scss";

export function ContentLayout({ crumbs, title, lead, cover, body, facts = [], gallery = [], cta = false }: {
  crumbs: [string, string][]; title: string; lead?: string | null; cover?: string | null; body?: string | null; facts?: string[]; gallery?: { url: string; alt: string }[]; cta?: boolean;
}) {
  return (
    <article className="container section">
      <nav className={styles.crumbs} aria-label="Хлебные крошки"><Link href="/">Главная</Link>{crumbs.map(([h, l]) => <span key={h}><span>/</span><Link href={h}>{l}</Link></span>)}<span>/</span><span>{title}</span></nav>
      <h1>{title}</h1>
      {facts.length > 0 && <p className={styles.facts}>{facts.map((f) => <span key={f}>{f}</span>)}</p>}
      {lead && <p className={styles.lead}>{lead}</p>}
      {cover && <img className={styles.cover} src={cover} alt="" width={1200} height={800} />}
      {body && <div className="prose" dangerouslySetInnerHTML={{ __html: body }} />}
      {gallery.length > 0 && <div className={styles.gallery}>{gallery.map((g) => <img key={g.url} src={g.url} alt={g.alt} loading="lazy" width={600} height={400} />)}</div>}
      {cta && <div className={styles.cta}><b>Нужна техника под эту задачу?</b><Link href="/catalog" className="btn btn--primary">Подобрать в каталоге</Link></div>}
    </article>
  );
}
