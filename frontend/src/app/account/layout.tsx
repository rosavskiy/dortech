import { redirect } from "next/navigation";
import { getMe } from "@/lib/server-auth";
import { SessionProvider } from "@/components/auth/SessionProvider";
import { CabinetLayout } from "@/components/cabinet/CabinetLayout";
export const dynamic = "force-dynamic";
export const metadata = { title: "Личный кабинет", robots: { index: false } };
export default async function Layout({ children }: { children: React.ReactNode }) {
  const me = await getMe();
  if (!me) redirect("/login?next=/account/inquiries");
  if (me.role !== "client") redirect("/manager/inquiries");
  return <SessionProvider me={me}><CabinetLayout me={me} items={[{ href: "/account/inquiries", label: "Мои заявки" }, { href: "/account/profile", label: "Профиль организации" }]}>{children}</CabinetLayout></SessionProvider>;
}
