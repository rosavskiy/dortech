"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import styles from "./MobileNav.module.scss";

export function MobileNav({ items, phone }: { items: { href: string; label: string }[]; phone: string | null }) {
  const [open, setOpen] = useState(false);
  const pathname = usePathname();
  useEffect(() => setOpen(false), [pathname]);
  useEffect(() => {
    document.body.style.overflow = open ? "hidden" : "";
    return () => { document.body.style.overflow = ""; };
  }, [open]);
  return (
    <>
      <button className={styles.burger} aria-label={open ? "Закрыть меню" : "Открыть меню"} aria-expanded={open} onClick={() => setOpen((v) => !v)}>
        <span /><span /><span />
      </button>
      {open && (
        <div className={styles.panel} role="dialog" aria-label="Меню">
          <nav className={styles.list}>
            {items.map((n) => <Link key={n.href} href={n.href}>{n.label}</Link>)}
            <Link href="/compare">Сравнение</Link>
            <Link href="/request">Заявка</Link>
          </nav>
          {phone && <a className="btn btn--primary btn--block" href={`tel:${phone.replace(/[^\d+]/g, "")}`}>{phone}</a>}
        </div>
      )}
    </>
  );
}
