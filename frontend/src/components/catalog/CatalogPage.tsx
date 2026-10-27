import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { api } from "@/lib/api";
import type { CategoryOut } from "@/lib/types";
import { EquipmentCard } from "./EquipmentCard";
import { Filters } from "./Filters";
import { Toolbar } from "./Toolbar";
import { Pagination } from "./Pagination";
import styles from "./CatalogPage.module.scss";

export type SP = Record<string, string | string[] | undefined>;

export function flatten(sp: SP): Record<string, string> {
  const out: Record<string, string> = {};
  for (const [k, v] of Object.entries(sp)) if (typeof v === "string" && v) out[k] = v;
  return out;
}

export async function catalogMetadata(category?: CategoryOut | null): Promise<Metadata> {
  if (category) return { title: category.meta_title ?? `${category.name} — аренда`, description: category.meta_description ?? category.description ?? undefined };
  return { title: "Каталог спецтехники", description: "Аренда спецтехники: фильтры по категории, производителю, характеристикам. Сравнение и онлайн-заявка." };
}

export async function CatalogPage({ sp, categorySlug }: { sp: SP; categorySlug?: string }) {
  const params = flatten(sp);
  if (categorySlug) params.category = categorySlug;
  const qs = new URLSearchParams(params).toString();
  const [list, facets, categories] = await Promise.all([api.equipmentList(qs), api.facets(categorySlug ? `category=${categorySlug}` : ""), api.categories()]);
  const category = categorySlug ? categories.find((c) => c.slug === categorySlug) ?? null : null;
  const basePath = categorySlug ? `/catalog/${categorySlug}` : "/catalog";
  const { page: _p, ...rest } = params;
  void _p;
  return (
    <div className="container section">
      <nav className={styles.crumbs} aria-label="Хлебные крошки">
        <Link href="/">Главная</Link><span>/</span><Link href="/catalog">Каталог</Link>{category && <><span>/</span><span>{category.name}</span></>}
      </nav>
      <h1>{category ? category.name : "Каталог спецтехники"}</h1>
      {category?.description && <p className="muted">{category.description}</p>}
      {!categorySlug && (
        <div className={styles.cats}>
          {categories.filter((c) => !c.parent_id).map((c) => (
            <Link key={c.slug} href={`/catalog/${c.slug}`} className={styles.cat}>{c.name}<span>{c.equipment_count}</span></Link>
          ))}
        </div>
      )}
      <div className={styles.layout}>
        <Suspense><Filters facets={facets} basePath={basePath} /></Suspense>
        <div>
          <Suspense><Toolbar total={list.total} /></Suspense>
          {list.items.length === 0 ? (
            <div className={styles.empty}><p>По вашему запросу ничего не найдено.</p><Link href={basePath} className="btn btn--outline">Сбросить фильтры</Link></div>
          ) : (
            <div className={styles.grid}>{list.items.map((e) => <EquipmentCard key={e.id} item={e} />)}</div>
          )}
          <Pagination page={list.page} pages={list.pages} basePath={basePath} sp={rest} />
        </div>
      </div>
    </div>
  );
}
