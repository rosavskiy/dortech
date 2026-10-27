import type { MetadataRoute } from "next";
export default function robots(): MetadataRoute.Robots {
  const base = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";
  const allow = process.env.ROBOTS_ALLOW !== "0";
  return allow
    ? { rules: [{ userAgent: "*", allow: "/", disallow: ["/api/", "/account/", "/manager/", "/request", "/compare"] }], sitemap: `${base}/sitemap.xml` }
    : { rules: [{ userAgent: "*", disallow: "/" }] };
}
