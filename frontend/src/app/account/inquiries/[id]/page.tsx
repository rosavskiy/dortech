import { AccountInquiryDetail } from "@/components/cabinet/AccountInquiryDetail";
export default async function Page(p: { params: Promise<{ id: string }> }) { const { id } = await p.params; return <AccountInquiryDetail id={id} />; }
