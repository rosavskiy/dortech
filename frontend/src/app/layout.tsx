import type { Metadata } from "next";
import "@fontsource-variable/roboto";
import "@/styles/globals.scss";
import { api } from "@/lib/api";
import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";
import { Providers } from "@/components/Providers";
import { Toaster } from "@/components/ui/Toast";

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

export async function generateMetadata(): Promise<Metadata> {
  const s = await api.settings().catch(() => null);
  return {
    metadataBase: new URL(siteUrl),
    title: { default: s?.default_meta_title ?? "Дортех — аренда спецтехники", template: "%s — Дортех" },
    description: s?.default_meta_description ?? "ООО «ДОРТЕХ»: аренда спецтехники, услуги и выполненные проекты.",
    robots: process.env.ROBOTS_ALLOW === "0" ? { index: false, follow: false } : undefined,
  };
}

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const settings = await api.settings().catch(() => ({
    company_name: "ООО «ДОРТЕХ»", phone: null, email: null, address: null, working_hours: null, map_embed: null,
    hero_title: null, hero_subtitle: null, hero_image_url: null, about_short: null, stats: null, footer_text: null,
    default_meta_title: null, default_meta_description: null, footer_pages: [],
  }));
  return (
    <html lang="ru">
      <body>
        <Providers>
          <Header settings={settings} />
          <main>{children}</main>
          <Footer settings={settings} />
          <Toaster />
        </Providers>
      </body>
    </html>
  );
}
