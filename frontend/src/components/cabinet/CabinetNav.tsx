"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import styles from "./CabinetNav.module.scss";
export function CabinetNav({ items }: { items: { href: string; label: string }[] }) {
  const path = usePathname();
  return (
    <nav className={styles.nav} aria-label="Кабинет">
      {items.map((i) => <Link key={i.href} href={i.href} className={path.startsWith(i.href) ? styles.active : ""}>{i.label}</Link>)}
    </nav>
  );
}
