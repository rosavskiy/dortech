import { RegisterForm } from "@/components/auth/RegisterForm";
export const metadata = { title: "Регистрация", robots: { index: false } };
export default function Page() { return <div className="container section"><RegisterForm /></div>; }
