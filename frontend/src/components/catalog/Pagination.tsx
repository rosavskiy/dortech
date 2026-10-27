import Link from "next/link";

export function Pagination({ page, pages, basePath, sp }: { page: number; pages: number; basePath: string; sp: Record<string, string> }) {
  if (pages <= 1) return null;
  const href = (p: number) => { const q = new URLSearchParams(sp); if (p > 1) q.set("page", String(p)); else q.delete("page"); const s = q.toString(); return s ? `${basePath}?${s}` : basePath; };
  const nums = Array.from({ length: pages }, (_, i) => i + 1).filter((p) => p === 1 || p === pages || Math.abs(p - page) <= 2);
  return (
    <nav aria-label="Страницы" style={{ display: "flex", gap: 6, flexWrap: "wrap", justifyContent: "center", marginTop: 32 }}>
      {page > 1 && <Link className="btn btn--outline btn--sm" href={href(page - 1)}>← Назад</Link>}
      {nums.map((p, i) => (
        <span key={p} style={{ display: "contents" }}>
          {i > 0 && nums[i - 1] !== p - 1 && <span style={{ padding: "8px 4px" }}>…</span>}
          <Link className={`btn btn--sm ${p === page ? "btn--primary" : "btn--ghost"}`} href={href(p)} aria-current={p === page ? "page" : undefined}>{p}</Link>
        </span>
      ))}
      {page < pages && <Link className="btn btn--outline btn--sm" href={href(page + 1)}>Вперёд →</Link>}
    </nav>
  );
}
