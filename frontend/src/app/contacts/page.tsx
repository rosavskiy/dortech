import { api } from "@/lib/api";
import { ContactForm } from "@/components/ContactForm";
import styles from "./page.module.scss";
export const metadata = { title: "Контакты", description: "Контакты ООО «ДОРТЕХ»: телефон, email, адрес, режим работы." };
export default async function Page() {
  const s = await api.settings();
  return (
    <div className="container section"><h1>Контакты</h1>
      <div className={styles.grid}>
        <div className={styles.info}>
          {s.phone && <p><span className="muted">Телефон</span><a href={`tel:${s.phone.replace(/[^\d+]/g, "")}`}>{s.phone}</a></p>}
          {s.email && <p><span className="muted">Email</span><a href={`mailto:${s.email}`}>{s.email}</a></p>}
          {s.address && <p><span className="muted">Адрес</span><span>{s.address}</span></p>}
          {s.working_hours && <p><span className="muted">Режим работы</span><span>{s.working_hours}</span></p>}
          {s.map_embed && <div className={styles.map} dangerouslySetInnerHTML={{ __html: s.map_embed }} />}
        </div>
        <div><h2>Напишите нам</h2><ContactForm /></div>
      </div>
    </div>
  );
}
