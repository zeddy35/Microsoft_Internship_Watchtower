import type { NextConfig } from "next";

/**
 * Demo mode is on by default when the build runs on Vercel.
 *
 * Watchtower's backend needs a local DuckDB file, a background scheduler, and
 * a Phi-4 endpoint on the same machine, so a hosted build has nothing to talk
 * to. Rather than deploy a dashboard full of error cards, a Vercel build
 * serves the bundled snapshot from `app/api/demo` and labels itself as a demo
 * in the top bar. Set NEXT_PUBLIC_DEMO_MODE=0 in the Vercel project to point a
 * deployment at a real API instead.
 *
 * Local builds are unaffected: `VERCEL` is only set by Vercel's builders.
 */
const nextConfig: NextConfig = {
  env: {
    NEXT_PUBLIC_DEMO_MODE:
      process.env.NEXT_PUBLIC_DEMO_MODE ?? (process.env.VERCEL ? "1" : "0"),
  },
};

export default nextConfig;
