export type CategoryOut = {
  id: number; name: string; slug: string; parent_id: number | null; description: string | null;
  image_url: string | null; is_featured: boolean; equipment_count: number;
};
export type ManufacturerOut = { id: number; name: string; slug: string; logo_url: string | null };
export type StatusOut = { id: number; code: string; name: string; color: string; allow_request: boolean };
export type TariffOut = { price_per_shift: string | null; price_per_day: string | null; shift_hours: number; min_units: number; note: string | null };
export type AttributeValueOut = { code: string; name: string; unit: string | null; value: string; raw: string | number | boolean | null };
export type ImageOut = { url: string; alt: string | null };
export type EquipmentCard = {
  id: number; slug: string; name: string; model: string | null; year: number | null; category: CategoryOut;
  manufacturer: ManufacturerOut | null; status: StatusOut | null; image: ImageOut | null; short_description: string | null;
  price_hidden: boolean; tariff: TariffOut | null; is_featured: boolean; key_attributes: AttributeValueOut[];
};
export type EquipmentDetail = EquipmentCard & {
  description: string | null; terms: string | null; images: ImageOut[]; attributes: AttributeValueOut[];
  meta_title: string | null; meta_description: string | null; og_image_url: string | null; noindex: boolean;
};
export type Paginated<T> = { items: T[]; page: number; page_size: number; total: number; pages: number };
export type FacetOption = { value: string; label: string; count: number };
export type FacetAttribute = { code: string; name: string; unit: string | null; type: "number" | "string" | "bool" | "choice"; options: FacetOption[]; min: string | null; max: string | null };
export type Facets = { manufacturers: FacetOption[]; statuses: FacetOption[]; categories: FacetOption[]; attributes: FacetAttribute[] };
export type CompareRow = { code: string; name: string; unit: string | null; values: (string | null)[] };
export type CompareOut = { items: EquipmentCard[]; rows: CompareRow[] };

export type Seo = { meta_title: string | null; meta_description: string | null; og_image_url: string | null; noindex: boolean };
export type PageBrief = { slug: string; title: string };
export type SiteSettingsOut = {
  company_name: string; phone: string | null; email: string | null; address: string | null; working_hours: string | null;
  map_embed: string | null; hero_title: string | null; hero_subtitle: string | null; hero_image_url: string | null;
  about_short: string | null; stats: { value: string; label: string }[] | null; footer_text: string | null;
  default_meta_title: string | null; default_meta_description: string | null; footer_pages: PageBrief[];
};
export type PageOut = Seo & { slug: string; title: string; body: string | null; updated_at: string };
export type ServiceOut = Seo & { id: number; slug: string; title: string; short_description: string | null; body: string | null; cover_url: string | null; icon: string | null; updated_at: string };
export type ProjectOut = Seo & { id: number; slug: string; title: string; short_description: string | null; body: string | null; cover_url: string | null; year: number | null; customer_name: string | null; location: string | null; images: { url: string; alt: string | null }[]; updated_at: string };
export type PublicationOut = Seo & { id: number; slug: string; title: string; short_description: string | null; body: string | null; cover_url: string | null; published_at: string | null; updated_at: string };
export type HomeOut = { settings: SiteSettingsOut; featured_categories: CategoryOut[]; featured_equipment: EquipmentCard[]; services: ServiceOut[]; projects: ProjectOut[]; publications: PublicationOut[] };
export type RedirectOut = { old_path: string; new_path: string; status_code: number };
export type SitemapEntry = { path: string; updated_at: string | null; priority: number };

export type RateUnit = "shift" | "day";
export type EstimateItemIn = { equipment_id: number; quantity: number; units?: number | null; unit: RateUnit };
export type EstimateIn = { items: EstimateItemIn[]; period_from?: string | null; period_to?: string | null; extra_service_ids: number[] };
export type EstimateLine = { equipment_id: number; name: string; model: string | null; quantity: number; units: number; unit: RateUnit; unit_price: string | null; line_total: string | null; needs_quote: boolean };
export type EstimateOut = { lines: EstimateLine[]; extras: { id: number; name: string; price: string }[]; total: string; is_partial: boolean; currency: string; vat_label: string; disclaimer: string; rounding_step: number };
export type ExtraServiceOut = { id: number; name: string; description: string | null; price: string };
export type InquiryCreateIn = EstimateIn & { contact_name: string; contact_phone: string; contact_email?: string | null; company_name?: string | null; work_place?: string | null; comment?: string | null; consent: boolean; website?: string };
export type InquiryCreatedOut = { public_id: string; number: string; status: string; estimate: EstimateOut; created_at: string };
