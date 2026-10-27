"use client";
import Link from "next/link";
import { useCart } from "@/lib/cart";

export function CartLink() {
  const { items, hydrated } = useCart();
  const n = hydrated ? items.length : 0;
  return (
    <Link href="/request" className="btn btn--primary btn--sm" aria-label="Перейти к заявке">
      Заявка{n > 0 && <span style={{ background: "#fff", color: "#ff6b00", borderRadius: 10, padding: "0 7px", fontSize: 12, fontWeight: 700 }}>{n}</span>}
    </Link>
  );
}
