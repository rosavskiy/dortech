import { redirect } from "next/navigation";
import { getMe } from "@/lib/server-auth";
import { SessionProvider } from "@/components/auth/SessionProvider";
import { CabinetLayout } from "@/components/cabinet/CabinetLayout";
export const dynamic = "force-dynamic";
export const metadata = { title: "Кабинет менеджера", robots: { index: false } };
export default async function Layout({ children }: { children: React.ReactNode }) {
  const me = await getMe();
  if (!me) redirect("/login?next=/manager/inquiries");
  if (me.role === "client") redirect("/account/inquiries");
  return <SessionProvider me={me}><CabinetLayout me={me} items={[{ href: "/manager/inquiries", label: "Заявки" }, { href: "/manager/organizations", label: "Организации" }]}>{children}</CabinetLayout></SessionProvider>;
}
