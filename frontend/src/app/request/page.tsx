import { RequestForm } from "@/components/request/RequestForm";
export const metadata = { title: "Заявка на аренду", robots: { index: false } };
export default function Page() {
  return <div className="container section"><h1>Заявка на аренду техники</h1><RequestForm /></div>;
}
