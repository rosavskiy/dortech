import { SuccessView } from "@/components/request/SuccessView";
export const metadata = { title: "Заявка отправлена", robots: { index: false } };
export default function Page() { return <div className="container section"><SuccessView /></div>; }
