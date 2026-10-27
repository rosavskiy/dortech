import Link from "next/link";
import type { SiteSettingsOut } from "@/lib/types";
import { CartLink } from "@/components/layout/CartLink";
import { MobileNav } from "@/components/layout/MobileNav";
import { HeaderAuth } from "@/components/layout/HeaderAuth";
import styles from "./Header.module.scss";

export const NAV = [
  { href: "/catalog", label: "Каталог техники" },
  { href: "/services", label: "Услуги" },
  { href: "/projects", label: "Проекты" },
  { href: "/publications", label: "Публикации" },
  { href: "/about", label: "О компании" },
  { href: "/contacts", label: "Контакты" },
];

export function Header({ settings }: { settings: SiteSettingsOut }) {
  return (
    <header className={styles.header}>
      <div className={styles.top}>
        <div className={`container ${styles.topInner}`}>
          <span>{settings.working_hours}</span>
          <span className={styles.topContacts}>
            {settings.email && <a href={`mailto:${settings.email}`}>{settings.email}</a>}
            {settings.phone && <a href={`tel:${settings.phone.replace(/[^\d+]/g, "")}`}>{settings.phone}</a>}
          </span>
        </div>
      </div>
      <div className={`container ${styles.main}`}>
        <Link href="/" className={styles.logo} aria-label="На главную">
          <span className={styles.logoMark}>ДТ</span>
          <span className={styles.logoText}>ДОРТЕХ<small>аренда спецтехники</small></span>
        </Link>
        <nav className={styles.nav} aria-label="Основное меню">
          {NAV.map((n) => (
            <Link key={n.href} href={n.href}>{n.label}</Link>
          ))}
        </nav>
        <div className={styles.actions}>
          {settings.phone && (
            <a className={styles.phone} href={`tel:${settings.phone.replace(/[^\d+]/g, "")}`}>{settings.phone}</a>
          )}
          <Link href="/compare" className={`btn btn--ghost btn--sm ${styles.compare}`}>Сравнение</Link>
          <HeaderAuth className={styles.compare} />
          <CartLink />
          <MobileNav items={NAV} phone={settings.phone} />
        </div>
      </div>
    </header>
  );
}
