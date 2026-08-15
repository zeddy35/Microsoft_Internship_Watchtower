"use client";

import { IconMoon, IconSun } from "@tabler/icons-react";
import { useTheme } from "@/lib/theme";

/**
 * Quick light/dark flip for the top bar.
 *
 * It sets an explicit preference rather than cycling through System: someone
 * reaching for this button wants the theme to change now, and Settings is
 * where the three-way choice lives.
 */
export function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();
  const next = resolvedTheme === "dark" ? "light" : "dark";

  return (
    <button
      type="button"
      onClick={() => setTheme(next)}
      aria-label={`Switch to ${next} theme`}
      title={`Switch to ${next} theme`}
      className="flex size-8 shrink-0 items-center justify-center rounded-control text-neutral-secondary transition-colors hover:bg-neutral-lighter hover:text-neutral-primary"
    >
      {resolvedTheme === "dark" ? (
        <IconSun className="size-4" stroke={1.75} aria-hidden="true" />
      ) : (
        <IconMoon className="size-4" stroke={1.75} aria-hidden="true" />
      )}
    </button>
  );
}
