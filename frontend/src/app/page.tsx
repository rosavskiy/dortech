import Link from "next/link";
import { api, mediaUrl } from "@/lib/api";
import { EquipmentCard } from "@/components/catalog/EquipmentCard";
import styles from "./page.module.scss";

export const revalidate = 60;

export default async function HomePage() {
  const h = await api.home();
  const s = h.settings;
  const hero = mediaUrl(s.hero_image_url);
  return (
    <>
      <section className={styles.hero} style={hero ? { backgroundImage: `url(${hero})` } : undefined}>
        <div className={`container ${styles.heroInner}`}>
          <h1>{s.hero_title ?? "Аренда спецтехники"}</h1>
          {s.hero_subtitle && <p>{s.hero_subtitle}</p>}
          <div className={styles.heroActions}>
            <Link href="/catalog" className="btn btn--primary">Подобрать технику</Link>
            <Link href="/request" className="btn btn--outline" style={{ color: "#fff", borderColor: "#fff" }}>Оставить заявку</Link>
          </div>
        </div>
      </section>

      {h.featured_categories.length > 0 && (
        <section className="container section">
          <h2 className="section__title">Техника в аренду</h2>
          <div className={styles.cats}>
            {h.featured_categories.map((c) => {
              const img = mediaUrl(c.image_url);
              return (
                <Link key={c.slug} href={`/catalog/${c.slug}`} className={styles.cat}>
                  {img && <img src={img} alt="" width={800} height={600} loading="lazy" />}
                  <span className={styles.catBody}><b>{c.name}</b><small>{c.equipment_count} ед.</small></span>
                </Link>
              );
            })}
          </div>
        </section>
      )}

      {h.featured_equipment.length > 0 && (
        <section className={`container section ${styles.alt}`}>
          <div className={styles.head}><h2>Популярная техника</h2><Link href="/catalog" className="btn btn--ghost btn--sm">Весь каталог →</Link></div>
          <div className={styles.grid}>{h.featured_equipment.map((e) => <EquipmentCard key={e.id} item={e} />)}</div>
        </section>
      )}

      {h.services.length > 0 && (
        <section className="container section">
          <div className={styles.head}><h2>Услуги</h2><Link href="/services" className="btn btn--ghost btn--sm">Все услуги →</Link></div>
          <div className={styles.services}>
            {h.services.map((sv) => (
              <Link key={sv.slug} href={`/services/${sv.slug}`} className={styles.service}><b>{sv.title}</b><span className="muted">{sv.short_description}</span></Link>
            ))}
          </div>
        </section>
      )}

      <section className={styles.about}>
        <div className={`container ${styles.aboutInner}`}>
          <div><h2>О компании</h2><p>{s.about_short}</p><Link href="/about" className="btn btn--outline" style={{ color: "#fff", borderColor: "#fff" }}>Подробнее</Link></div>
          {s.stats && <div className={styles.stats}>{s.stats.map((st) => <div key={st.label}><b>{st.value}</b><span>{st.label}</span></div>)}</div>}
        </div>
      </section>

      {h.projects.length > 0 && (
        <section className="container section">
          <div className={styles.head}><h2>Выполненные проекты</h2><Link href="/projects" className="btn btn--ghost btn--sm">Все проекты →</Link></div>
          <div className={styles.cards3}>
            {h.projects.slice(0, 3).map((p) => {
              const img = mediaUrl(p.cover_url);
              return (
                <Link key={p.slug} href={`/projects/${p.slug}`} className={styles.card}>
                  {img && <img src={img} alt="" width={900} height={600} loading="lazy" />}
                  <span className={styles.cardBody}><small className="muted">{[p.year, p.location].filter(Boolean).join(" · ")}</small><b>{p.title}</b></span>
                </Link>
              );
            })}
          </div>
        </section>
      )}

      {h.publications.length > 0 && (
        <section className="container section">
          <div className={styles.head}><h2>Публикации</h2><Link href="/publications" className="btn btn--ghost btn--sm">Все публикации →</Link></div>
          <div className={styles.cards3}>
            {h.publications.map((p) => {
              const img = mediaUrl(p.cover_url);
              return (
                <Link key={p.slug} href={`/publications/${p.slug}`} className={styles.card}>
                  {img && <img src={img} alt="" width={900} height={600} loading="lazy" />}
                  <span className={styles.cardBody}><small className="muted">{p.published_at ? new Date(p.published_at).toLocaleDateString("ru-RU") : ""}</small><b>{p.title}</b></span>
                </Link>
              );
            })}
          </div>
        </section>
      )}
    </>
  );
}
