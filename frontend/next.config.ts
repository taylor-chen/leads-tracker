import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  poweredByHeader: false,
  // Lint runs as its own step (`npm run lint`); type-checking still runs during build.
  eslint: { ignoreDuringBuilds: true },
};

export default nextConfig;
