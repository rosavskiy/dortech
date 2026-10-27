/** Типы и чистые функции, общие для серверных и клиентских компонентов. */
export type Me = {
  id: number; email: string; first_name: string; last_name: string; patronymic: string | null; phone: string | null;
  position: string | null; role: "client" | "manager" | "admin";
  organization: { id: number; name: string; inn: string | null; kpp: string | null; legal_address: string | null; phone: string | null; email: string | null } | null;
  csrf_token: string | null;
};
export function fullName(m: Pick<Me, "first_name" | "last_name" | "email">): string {
  return [m.last_name, m.first_name].filter(Boolean).join(" ") || m.email;
}
export function homeFor(m: Me): string {
  return m.role === "client" ? "/account/inquiries" : "/manager/inquiries";
}
