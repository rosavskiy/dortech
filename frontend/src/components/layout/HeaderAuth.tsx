"use client";
import Link from "next/link";
import { useMe, homeFor } from "@/lib/auth";

export function HeaderAuth({ className }: { className?: string }) {
  const { data: me } = useMe();
  if (me) return <Link href={homeFor(me)} className={`btn btn--ghost btn--sm ${className ?? ""}`}>Кабинет</Link>;
  return <Link href="/login" className={`btn btn--ghost btn--sm ${className ?? ""}`}>Войти</Link>;
}
