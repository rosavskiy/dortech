import Link from "next/link";
import { fullName, type Me } from "@/lib/auth-shared";
import { LogoutButton } from "./LogoutButton";
import { CabinetNav } from "./CabinetNav";
import styles from "./CabinetLayout.module.scss";

export function CabinetLayout({ me, items, children }: { me: Me; items: { href: string; label: string }[]; children: React.ReactNode }) {
  return (
    <div className={`container ${styles.layout}`}>
      <aside className={styles.side}>
        <div className={styles.user}><b>{fullName(me)}</b><span className="muted">{me.organization?.name ?? (me.role === "admin" ? "Администратор" : "Менеджер")}</span></div>
        <CabinetNav items={items} />
        {me.role !== "client" && <Link href={`/${process.env.NEXT_PUBLIC_ADMIN_PATH ?? "admin"}/`} className={styles.adminLink}>Панель управления ↗</Link>}
        <LogoutButton />
      </aside>
      <section className={styles.main}>{children}</section>
    </div>
  );
}
