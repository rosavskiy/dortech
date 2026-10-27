export const metadata = { title: "UI-kit", robots: { index: false } };
const statuses = [["green", "В наличии"], ["orange", "Занята"], ["gray", "Под заказ"], ["red", "Недоступна"]];
export default function Page() {
  return (
    <div className="container section" style={{ display: "flex", flexDirection: "column", gap: 40 }}>
      <section><h1>UI-kit</h1><p className="muted">Базовые элементы интерфейса. Цвета бренда заменяются после получения фирменного стиля Заказчика.</p></section>
      <section><h2>Типографика</h2><h1>Заголовок первого уровня</h1><h2>Заголовок второго уровня</h2><h3>Заголовок третьего уровня</h3><h4>Заголовок четвёртого уровня</h4>
        <p>Основной текст: аренда спецтехники для дорожного и промышленного строительства. <a href="#">Ссылка в тексте</a>.</p><p className="muted">Вторичный текст (muted).</p></section>
      <section><h2>Кнопки</h2><div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "center" }}>
        <button className="btn btn--primary">Основная</button><button className="btn btn--secondary">Вторичная</button><button className="btn btn--outline">Контурная</button><button className="btn btn--ghost">Прозрачная</button><button className="btn btn--primary btn--sm">Маленькая</button><button className="btn btn--primary" disabled>Недоступна</button></div></section>
      <section><h2>Статусы</h2><div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        {statuses.map(([c, l]) => <span key={c} style={{ padding: "4px 10px", borderRadius: 4, fontSize: 13, fontWeight: 600, color: "#fff", background: { green: "#28a745", orange: "#e67e22", gray: "#666", red: "#dc3545" }[c] }}>{l}</span>)}</div></section>
      <section><h2>Формы</h2><div style={{ maxWidth: 480 }}>
        <div className="field"><label className="field__label">Текстовое поле</label><input className="input" placeholder="Подсказка" /><span className="field__hint">Пояснение к полю</span></div>
        <div className="field"><label className="field__label">Поле с ошибкой</label><input className="input" aria-invalid="true" defaultValue="неверно" /><span className="field__error">Текст ошибки</span></div>
        <div className="field"><label className="field__label">Список</label><select className="select"><option>Вариант 1</option><option>Вариант 2</option></select></div>
        <div className="field"><label className="field__label">Многострочное</label><textarea className="textarea" /></div>
        <label style={{ display: "flex", gap: 8 }}><input type="checkbox" /> Флажок</label></div></section>
      <section><h2>Сетка каталога</h2><p className="muted">360 px — 1 колонка, 480+ — 2, 1024+ — 3, 1440 — 4. Фильтры: слева от 1024 px, в шторке на меньших.</p></section>
    </div>
  );
}
