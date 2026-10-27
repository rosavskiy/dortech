import { cookies } from "next/headers";
import type { Me } from "./auth-shared";

/** Текущий пользователь для серверных layout'ов кабинетов. Никогда не кэшируется. */
export async function getMe(): Promise<Me | null> {
  const jar = await cookies();
  const cookie = jar.getAll().map((c) => `${c.name}=${c.value}`).join("; ");
  if (!cookie.includes("dt_session=")) return null;
  const base = (process.env.INTERNAL_API_URL ?? "http://localhost:8000") + "/api/v1";
  const res = await fetch(`${base}/auth/me`, { headers: { Cookie: cookie, Accept: "application/json" }, cache: "no-store" });
  if (!res.ok) return null;
  return (await res.json()) as Me;
}
