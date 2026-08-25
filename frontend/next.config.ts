import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Standalone output lets the Docker runtime stage copy just the built
  // server + pruned node_modules instead of the whole workspace (see
  // frontend/Dockerfile).
  output: "standalone",
};

export default nextConfig;
