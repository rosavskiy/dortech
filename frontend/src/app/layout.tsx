import type { Metadata } from "next";
import "@fontsource-variable/roboto";
import "@/styles/globals.scss";

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: { default: "Дортех — аренда спецтехники", template: "%s — Дортех" },
  description: "ООО «ДОРТЕХ»: аренда спецтехники, услуги и выполненные проекты.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <body>{children}</body>
    </html>
  );
}
