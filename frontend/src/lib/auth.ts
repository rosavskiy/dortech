"use client";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch, ApiError } from "./api";

import { type Me } from "./auth-shared";
export { fullName, homeFor, type Me } from "./auth-shared";

export function csrfToken(): string {
  if (typeof document === "undefined") return "";
  const m = document.cookie.match(/(?:^|; )dt_csrf=([^;]*)/);
  return m ? decodeURIComponent(m[1]) : "";
}

/** Запрос с учётом сессии и CSRF (для кабинетов). */
export function authFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = { ...(init.headers as Record<string, string> | undefined) };
  if (init.method && init.method !== "GET") headers["X-CSRF-Token"] = csrfToken();
  return apiFetch<T>(path, { ...init, headers, credentials: "same-origin" });
}

export async function fetchMe(): Promise<Me | null> {
  try { return await apiFetch<Me>("/auth/me", { credentials: "same-origin" }); }
  catch (e) { if (e instanceof ApiError && (e.status === 401 || e.status === 403)) return null; throw e; }
}

export function useMe() {
  return useQuery({ queryKey: ["me"], queryFn: fetchMe, staleTime: 60_000, retry: false });
}

export function useLogout() {
  const qc = useQueryClient();
  return async () => {
    await authFetch("/auth/logout", { method: "POST" });
    qc.setQueryData(["me"], null);
    qc.clear();
  };
}

