import type { ReactNode } from "react";
import { AppNav } from "@/components/layout/AppNav";
import { TopBar } from "@/components/layout/TopBar";

/**
 * App shell: a fixed-height frame with exactly one scroll region.
 *
 * The height is bounded (`h-dvh` + `overflow-hidden`) so the only element that
 * scrolls is `<main>`. With `min-h-screen` the frame had no upper bound, the
 * document scrolled instead, and the nav rail and top bar slid off the top of
 * a long page. `dvh` rather than `vh` so a mobile browser's collapsing address
 * bar does not leave a dead strip at the bottom.
 *
 * Content is capped and centred: on an ultrawide display an uncapped dashboard
 * stretches KPI rows and card grids across the full width and turns every line
 * of text into an unreadable measure.
 */
export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="flex h-dvh overflow-hidden">
      <AppNav />
      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar />
        <main className="min-w-0 flex-1 overflow-y-auto">
          <div className="mx-auto w-full max-w-[1600px]">{children}</div>
        </main>
      </div>
    </div>
  );
}
