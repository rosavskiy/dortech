import type { NextConfig } from "next";

const API_PROXY = process.env.INTERNAL_API_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  output: "standalone",
  poweredByHeader: false,
  sassOptions: {
    includePaths: ["./src/styles"],
  },
  images: {
    remotePatterns: [{ protocol: "https", hostname: "**" }],
    dangerouslyAllowLocalIP: process.env.NODE_ENV === "development",
  },
  async rewrites() {
    // В dev браузер ходит на /api и /media через Next → FastAPI.
    // В prod эти пути маршрутизирует Caddy напрямую на backend.
    if (process.env.NODE_ENV !== "development") return [];
    return [
      { source: "/api/:path*", destination: `${API_PROXY}/api/:path*` },
      { source: "/media/:path*", destination: `${API_PROXY}/media/:path*` },
    ];
  },
};

export default nextConfig;
