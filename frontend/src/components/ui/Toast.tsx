"use client";
import { useEffect, useState } from "react";
import styles from "./Toast.module.scss";

type ToastItem = { id: number; text: string; kind: "success" | "error" | "info" };
const listeners = new Set<(t: ToastItem) => void>();
let seq = 0;
export function toast(text: string, kind: ToastItem["kind"] = "info") { listeners.forEach((l) => l({ id: ++seq, text, kind })); }

export function Toaster() {
  const [items, setItems] = useState<ToastItem[]>([]);
  useEffect(() => {
    const l = (t: ToastItem) => {
      setItems((prev) => [...prev.slice(-4), t]);
      setTimeout(() => setItems((prev) => prev.filter((i) => i.id !== t.id)), 3500);
    };
    listeners.add(l);
    return () => { listeners.delete(l); };
  }, []);
  if (!items.length) return null;
  return (
    <div className={styles.stack} role="status" aria-live="polite">
      {items.map((t) => <div key={t.id} className={`${styles.toast} ${styles[t.kind]}`}>{t.text}</div>)}
    </div>
  );
}
