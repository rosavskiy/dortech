import { ManagerInquiryDetail } from "@/components/cabinet/ManagerInquiryDetail";
export default async function Page(p: { params: Promise<{ id: string }> }) { const { id } = await p.params; return <ManagerInquiryDetail id={id} />; }
