import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // data/corridors.yaml (repository root) is read with fs at build/request time; the web app must run from a
  // checkout that contains the whole repository. Standalone output tracing is a stage-3 (hosting) concern.
};

export default nextConfig;
