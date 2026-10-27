import { Suspense } from "react";
import { LoginForm } from "@/components/auth/LoginForm";
export const metadata = { title: "Вход", robots: { index: false } };
export default function Page() { return <div className="container section"><Suspense><LoginForm /></Suspense></div>; }
