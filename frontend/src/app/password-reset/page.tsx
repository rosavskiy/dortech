import { ResetRequestForm } from "@/components/auth/ResetForms";
export const metadata = { title: "Восстановление пароля", robots: { index: false } };
export default function Page() { return <div className="container section"><ResetRequestForm /></div>; }
