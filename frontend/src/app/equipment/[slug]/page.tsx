import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { api, ApiError, mediaUrl, money } from "@/lib/api";
import { CardActions } from "@/components/catalog/CardActions";
import { Gallery } from "@/components/catalog/Gallery";
import styles from "./page.module.scss";

export const revalidate = 60;

async function load(slug: string) {
  try { return await api.equipment(slug); } catch (e) { if (e instanceof ApiError && e.status === 404) return null; throw e; }
}

export async function generateMetadata(props: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const { slug } = await props.params;
  const e = await load(slug);
  if (!e) return { title: "Техника не найдена" };
  return {
    title: e.meta_title ?? `${e.name} — аренда`,
    description: e.meta_description ?? e.short_description ?? undefined,
    robots: e.noindex ? { index: false } : undefined,
    openGraph: { title: e.meta_title ?? e.name, images: e.og_image_url ? [e.og_image_url] : e.images[0] ? [e.images[0].url] : [] },
  };
}

export default async function Page(props: { params: Promise<{ slug: string }> }) {
  const { slug } = await props.params;
  const e = await load(slug);
  if (!e) notFound();
  const images = e.images.map((i) => ({ url: mediaUrl(i.url)!, alt: i.alt ?? e.name }));
  return (
    <div className="container section">
      <nav className={styles.crumbs} aria-label="Хлебные крошки">
        <Link href="/">Главная</Link><span>/</span><Link href="/catalog">Каталог</Link><span>/</span>
        <Link href={`/catalog/${e.category.slug}`}>{e.category.name}</Link><span>/</span><span>{e.name}</span>
      </nav>
      <div className={styles.top}>
        <Gallery images={images} />
        <div className={styles.info}>
          <div className={styles.meta}>{e.category.name}{e.manufacturer ? ` · ${e.manufacturer.name}` : ""}{e.year ? ` · ${e.year} г.` : ""}</div>
          <h1 className={styles.title}>{e.name}</h1>
          {e.status && <span className={`${styles.status} ${styles["status_" + e.status.color]}`}>{e.status.name}</span>}
          {e.short_description && <p className="muted">{e.short_description}</p>}
          <div className={styles.priceBox}>
            {e.tariff && !e.price_hidden ? (
              <>
                <div><span className="muted">За смену ({e.tariff.shift_hours} ч)</span><b>{money(e.tariff.price_per_shift)}</b></div>
                <div><span className="muted">За сутки</span><b>{money(e.tariff.price_per_day)}</b></div>
                {e.tariff.min_units > 1 && <small className="muted">Минимум {e.tariff.min_units} смен/суток</small>}
                {e.tariff.note && <small className="muted">{e.tariff.note}</small>}
              </>
            ) : (
              <div><b>Стоимость по запросу</b><small className="muted">Отправьте заявку — менеджер подготовит предложение</small></div>
            )}
          </div>
          <CardActions item={e} big />
          {e.attributes.length > 0 && (
            <table className={styles.attrs}>
              <tbody>{e.attributes.map((a) => <tr key={a.code}><th scope="row">{a.name}</th><td>{a.value}{a.unit ? ` ${a.unit}` : ""}</td></tr>)}</tbody>
            </table>
          )}
        </div>
      </div>
      {(e.description || e.terms) && (
        <div className={styles.text}>
          {e.description && <section><h2>Описание</h2><div className="prose" dangerouslySetInnerHTML={{ __html: e.description }} /></section>}
          {e.terms && <section><h2>Условия аренды</h2><div className="prose" dangerouslySetInnerHTML={{ __html: e.terms }} /></section>}
        </div>
      )}
    </div>
  );
}
