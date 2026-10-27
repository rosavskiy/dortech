import { Suspense } from "react";
import { ConfirmEmail } from "@/components/auth/ConfirmEmail";
export const metadata = { title: "Подтверждение email", robots: { index: false } };
export default function Page() { return <div className="container section"><Suspense><ConfirmEmail /></Suspense></div>; }
