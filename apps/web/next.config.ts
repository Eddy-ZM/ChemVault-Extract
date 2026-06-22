import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export",
  transpilePackages: ["@chemvault-extract/schemas"],
  images: {
    unoptimized: true,
  },
};

export default nextConfig;

