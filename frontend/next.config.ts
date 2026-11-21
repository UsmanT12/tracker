import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  distDir: process.env.NEXT_DIST_DIR ?? ".next",
  outputFileTracingRoot: process.cwd(),
  reactStrictMode: true,
  async rewrites() {
    // Vercel Services routes /api directly to FastAPI; proxy it for local Next.js.
    if (process.env.VERCEL) return [];
    return [{
      source: "/api/v1/:path*",
      destination: "http://localhost:8000/api/v1/:path*",
    }];
  },
};

export default nextConfig;
