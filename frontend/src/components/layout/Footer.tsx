import Link from "next/link";
import type { SiteSettingsOut } from "@/lib/types";
import { NAV } from "./Header";
import styles from "./Footer.module.scss";

export function Footer({ settings }: { settings: SiteSettingsOut }) {
  return (
    <footer className={styles.footer}>
      <div className={`container ${styles.grid}`}>
        <div>
          <div className={styles.brand}>ДОРТЕХ</div>
          <p className={styles.muted}>{settings.about_short}</p>
        </div>
        <div>
          <div className={styles.title}>Разделы</div>
          <ul>{NAV.map((n) => <li key={n.href}><Link href={n.href}>{n.label}</Link></li>)}</ul>
        </div>
        <div>
          <div className={styles.title}>Контакты</div>
          <ul>
            {settings.phone && <li><a href={`tel:${settings.phone.replace(/[^\d+]/g, "")}`}>{settings.phone}</a></li>}
            {settings.email && <li><a href={`mailto:${settings.email}`}>{settings.email}</a></li>}
            {settings.address && <li>{settings.address}</li>}
            {settings.working_hours && <li>{settings.working_hours}</li>}
          </ul>
        </div>
        <div>
          <div className={styles.title}>Клиентам</div>
          <ul>
            <li><Link href="/account">Личный кабинет</Link></li>
            <li><Link href="/request">Оформить заявку</Link></li>
            {settings.footer_pages.map((p) => <li key={p.slug}><Link href={`/${p.slug}`}>{p.title}</Link></li>)}
          </ul>
        </div>
      </div>
      <div className={`container ${styles.bottom}`}>
        <span>{settings.footer_text ?? `© ${settings.company_name}`}, {new Date().getFullYear()}</span>
      </div>
    </footer>
  );
}
