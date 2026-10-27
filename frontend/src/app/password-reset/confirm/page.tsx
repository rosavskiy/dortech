import { Suspense } from "react";
import { ResetConfirmForm } from "@/components/auth/ResetForms";
export const metadata = { title: "Новый пароль", robots: { index: false } };
export default function Page() { return <div className="container section"><Suspense><ResetConfirmForm /></Suspense></div>; }
