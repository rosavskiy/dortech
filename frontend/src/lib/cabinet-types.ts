export type UserBrief = { id: number; name: string; email: string | null; role: string };
export type InquiryBrief = {
  public_id: string; number: string; status: string; status_label: string; created_at: string; period_from: string | null; period_to: string | null;
  items_count: number; estimated_total: string | null; is_partial: boolean; organization: string | null; contact_name: string; assigned_to: UserBrief | null; source: string;
};
export type ItemOut = { equipment_id: number; slug: string | null; name: string; model: string | null; quantity: number; units: number; unit: "shift" | "day"; unit_price: string | null; line_total: string | null; needs_quote: boolean };
export type HistoryOut = { from_status: string | null; to_status: string; to_label: string; changed_by: string | null; comment: string | null; created_at: string };
export type CommentOut = { id: number; author: string; is_staff: boolean; is_internal: boolean; text: string; created_at: string };
export type AttachmentOut = { public_id: string; original_name: string; content_type: string; size: number; kind: string; uploaded_by: string | null; created_at: string; download_url: string };
export type InquiryDetail = InquiryBrief & {
  contact_phone: string; contact_email: string | null; work_place: string | null; comment: string | null; items: ItemOut[]; extras: { name: string; price: string }[];
  total_label: string; vat_label: string | null; history: HistoryOut[]; comments: CommentOut[]; attachments: AttachmentOut[]; allowed_transitions: string[]; parent_number: string | null;
};
export type Paginated<T> = { items: T[]; page: number; page_size: number; total: number; pages: number };
export const STATUS_LABELS: Record<string, string> = { new: "Новая", clarification: "Уточнение", offer_sent: "Предложение направлено", agreed: "Согласована", completed: "Завершена", cancelled: "Отменена" };
export function fmtSize(n: number): string { return n > 1048576 ? `${(n / 1048576).toFixed(1)} МБ` : `${Math.max(1, Math.round(n / 1024))} КБ`; }
export function fmtDate(s: string): string { return new Date(s).toLocaleString("ru-RU", { dateStyle: "short", timeStyle: "short" }); }
