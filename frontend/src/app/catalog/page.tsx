import { CatalogPage, catalogMetadata, type SP } from "@/components/catalog/CatalogPage";

export const dynamic = "force-dynamic";
export async function generateMetadata() { return catalogMetadata(); }

export default async function Page(props: { searchParams: Promise<SP> }) {
  const sp = await props.searchParams;
  return <CatalogPage sp={sp} />;
}
