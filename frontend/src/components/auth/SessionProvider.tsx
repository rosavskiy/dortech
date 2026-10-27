"use client";
import { createContext, useContext, useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import type { Me } from "@/lib/auth-shared";

const Ctx = createContext<Me | null>(null);
export function SessionProvider({ me, children }: { me: Me; children: React.ReactNode }) {
  const qc = useQueryClient();
  useEffect(() => { qc.setQueryData(["me"], me); }, [me, qc]);
  return <Ctx.Provider value={me}>{children}</Ctx.Provider>;
}
export function useSession(): Me {
  const me = useContext(Ctx);
  if (!me) throw new Error("SessionProvider отсутствует");
  return me;
}
