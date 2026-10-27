"use client";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useSession } from "@/components/auth/SessionProvider";
import { authFetch } from "@/lib/auth";
import { fmtDate } from "@/lib/cabinet-types";
import { toast } from "@/components/ui/Toast";

type Job = { id: number; file_name: string; dry_run: boolean; status: string; total: number; created: number; updated: number; skipped: number; failed: number; warnings: number; errors: { row: number; external_id: string; field: string; message: string; level: string }[]; created_at: string; finished_at: string | null; started_by: string | null };

export function ImportPage() {
  const me = useSession();
  const qc = useQueryClient();
  const [dry, setDry] = useState(true);
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<Job | null>(null);
  const jobs = useQuery({ queryKey: ["import-jobs"], queryFn: () => authFetch<Job[]>("/manager/import"), enabled: me.role === "admin" });
  const run = useMutation({
    mutationFn: () => { const fd = new FormData(); fd.append("file", file!); fd.append("dry_run", dry ? "true" : "false"); return authFetch<Job>("/manager/import", { method: "POST", body: fd }); },
    onSuccess: (j) => { setResult(j); qc.invalidateQueries({ queryKey: ["import-jobs"] }); toast(dry ? "Проверка завершена" : "Импорт выполнен", "success"); },
    onError: (e) => toast((e as Error).message, "error"),
  });
  if (me.role !== "admin") return <p className="field__error">Импорт доступен только администратору.</p>;
  return (
    <div>
      <h1>Импорт каталога из CSV</h1>
      <p className="muted">UTF-8, разделитель «;». Обязательные колонки: external_id, name, category (slug категории). Повторный импорт обновляет карточки по external_id, дубли не создаются. <a href="/api/v1/manager/import/template.csv">Скачать шаблон</a>.</p>
      <form style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "center", margin: "16px 0 24px" }} onSubmit={(e) => { e.preventDefault(); if (file) run.mutate(); }}>
        <input type="file" accept=".csv,text/csv" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
        <label style={{ display: "flex", gap: 8, alignItems: "center" }}><input type="checkbox" checked={dry} onChange={(e) => setDry(e.target.checked)} /> Только проверка (ничего не записывать)</label>
        <button className="btn btn--primary" type="submit" disabled={!file || run.isPending}>{run.isPending ? "Обработка…" : dry ? "Проверить" : "Импортировать"}</button>
      </form>
      {result && (
        <section style={{ border: "1px solid #e5e5e5", borderRadius: 8, padding: 16, marginBottom: 24 }}>
          <h2 style={{ fontSize: 20 }}>{result.dry_run ? "Результат проверки" : "Результат импорта"} — {result.file_name}</h2>
          <p>Строк: <b>{result.total}</b> · создано: <b>{result.created}</b> · обновлено: <b>{result.updated}</b> · дублей в файле: <b>{result.skipped}</b> · с ошибками: <b style={{ color: result.failed ? "#dc3545" : undefined }}>{result.failed}</b> · предупреждений: <b>{result.warnings}</b>
            {result.errors.length > 0 && <> · <a href={`/api/v1/manager/import/${result.id}/report.csv`}>отчёт CSV</a></>}</p>
          {result.errors.length > 0 && (
            <div style={{ maxHeight: 360, overflow: "auto" }}>
              <table style={{ fontSize: 14 }}><thead><tr><th style={{ textAlign: "left", padding: 6 }}>Строка</th><th style={{ textAlign: "left", padding: 6 }}>external_id</th><th style={{ textAlign: "left", padding: 6 }}>Поле</th><th style={{ textAlign: "left", padding: 6 }}>Сообщение</th></tr></thead>
                <tbody>{result.errors.slice(0, 500).map((e, i) => <tr key={i} style={{ color: e.level === "error" ? "#dc3545" : "#666" }}><td style={{ padding: 6 }}>{e.row || "—"}</td><td style={{ padding: 6 }}>{e.external_id}</td><td style={{ padding: 6 }}>{e.field}</td><td style={{ padding: 6 }}>{e.message}</td></tr>)}</tbody></table>
            </div>
          )}
        </section>
      )}
      <h2 style={{ fontSize: 20 }}>Журнал импортов</h2>
      {jobs.data?.length ? (
        <table style={{ fontSize: 14 }}><thead><tr>{["Дата", "Файл", "Режим", "Строк", "Создано", "Обновлено", "Ошибок", "Кто", ""].map((h) => <th key={h} style={{ textAlign: "left", padding: 6, borderBottom: "1px solid #e5e5e5" }}>{h}</th>)}</tr></thead>
          <tbody>{jobs.data.map((j) => <tr key={j.id}><td style={{ padding: 6 }}>{fmtDate(j.created_at)}</td><td style={{ padding: 6 }}>{j.file_name}</td><td style={{ padding: 6 }}>{j.dry_run ? "проверка" : "импорт"}</td><td style={{ padding: 6 }}>{j.total}</td><td style={{ padding: 6 }}>{j.created}</td><td style={{ padding: 6 }}>{j.updated}</td><td style={{ padding: 6 }}>{j.failed}</td><td style={{ padding: 6 }}>{j.started_by ?? "CLI"}</td><td style={{ padding: 6 }}><a href={`/api/v1/manager/import/${j.id}/report.csv`}>отчёт</a></td></tr>)}</tbody></table>
      ) : <p className="muted">Импортов ещё не было.</p>}
    </div>
  );
}
