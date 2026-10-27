import Link from "next/link";
export default function NotFound() {
  return (<div className="container section" style={{ textAlign: "center" }}><h1>Страница не найдена</h1><p className="muted">Возможно, адрес изменился или страница была удалена.</p><Link href="/" className="btn btn--primary">На главную</Link></div>);
}
