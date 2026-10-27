"use client";
import { useRouter } from "next/navigation";
import { useLogout } from "@/lib/auth";
export function LogoutButton() {
  const logout = useLogout();
  const router = useRouter();
  return <button type="button" className="btn btn--ghost btn--sm" style={{ alignSelf: "flex-start" }} onClick={async () => { await logout(); router.push("/"); router.refresh(); }}>Выйти</button>;
}
