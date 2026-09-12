import type { NextConfig } from "next";

// Free hosting (docs/expansion-plan.md, 1.11): the site is exported as static HTML (`next build` -> web/out) and
// published to GitHub Pages by .github/workflows/pages.yml, rebuilt daily after the source check. Every page is
// pre-rendered from web/data and data/* at build time; there is no server. NEXT_PUBLIC_BASE_PATH is the
// sub-path GitHub Pages serves a project site from ("/Trade-Routes"); empty for local runs and custom domains.
const basePath = process.env.NEXT_PUBLIC_BASE_PATH ?? "";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  output: "export",
  basePath: basePath || undefined,
  trailingSlash: true,
  images: { unoptimized: true },
};

export default nextConfig;
