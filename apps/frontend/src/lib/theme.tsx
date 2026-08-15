"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

/**
 * Theme state: an explicit Light/Dark choice, or System, which follows the OS.
 *
 * The class on <html> is what actually switches the palette (see globals.css);
 * this provider only decides which class to set and remembers the preference.
 */

export type Theme = "light" | "dark" | "system";
export type ResolvedTheme = "light" | "dark";

export const THEME_STORAGE_KEY = "watchtower-theme";

interface ThemeContextValue {
  theme: Theme;
  resolvedTheme: ResolvedTheme;
  setTheme: (theme: Theme) => void;
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

function systemTheme(): ResolvedTheme {
  if (typeof window === "undefined") return "light";
  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

function readStoredTheme(): Theme {
  if (typeof window === "undefined") return "system";
  const stored = window.localStorage.getItem(THEME_STORAGE_KEY);
  return stored === "light" || stored === "dark" || stored === "system"
    ? stored
    : "system";
}

/**
 * Runs before first paint, from a blocking inline script in the document head.
 *
 * Without it the page renders light, then flips to dark once React hydrates —
 * a white flash on every navigation for anyone using the dark theme.
 */
export const THEME_INIT_SCRIPT = `
(function () {
  try {
    var stored = localStorage.getItem('${THEME_STORAGE_KEY}');
    var theme = stored === 'light' || stored === 'dark' ? stored
      : (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    document.documentElement.classList.toggle('dark', theme === 'dark');
    document.documentElement.style.colorScheme = theme;
  } catch (e) {}
})();
`;

export function ThemeProvider({ children }: { children: ReactNode }) {
  // Start from "system" on the server and correct on mount: reading
  // localStorage during render would not match the server-rendered HTML.
  const [theme, setThemeState] = useState<Theme>("system");
  const [resolved, setResolved] = useState<ResolvedTheme>("light");

  const apply = useCallback((next: Theme) => {
    const effective = next === "system" ? systemTheme() : next;
    document.documentElement.classList.toggle("dark", effective === "dark");
    document.documentElement.style.colorScheme = effective;
    setResolved(effective);
  }, []);

  useEffect(() => {
    const stored = readStoredTheme();
    setThemeState(stored);
    apply(stored);
  }, [apply]);

  // Follow the OS while the preference is "system".
  useEffect(() => {
    if (theme !== "system") return;
    const query = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = () => apply("system");
    query.addEventListener("change", onChange);
    return () => query.removeEventListener("change", onChange);
  }, [theme, apply]);

  const setTheme = useCallback(
    (next: Theme) => {
      setThemeState(next);
      window.localStorage.setItem(THEME_STORAGE_KEY, next);
      apply(next);
    },
    [apply],
  );

  const value = useMemo(
    () => ({ theme, resolvedTheme: resolved, setTheme }),
    [theme, resolved, setTheme],
  );

  return (
    <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
  );
}

export function useTheme(): ThemeContextValue {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useTheme must be used inside ThemeProvider");
  }
  return context;
}

/**
 * Chart colours, read from the same CSS variables the rest of the UI uses.
 *
 * Canvas cannot consume CSS classes, so charts would otherwise need literal
 * hex values — which is exactly how they end up wrong in one theme. Reading
 * the computed variables keeps one source of truth and re-reads them whenever
 * the theme changes.
 */
export function useThemeColors(): (token: string, alpha?: number) => string {
  const { resolvedTheme } = useTheme();

  return useCallback(
    (token: string, alpha = 1) => {
      if (typeof window === "undefined") return "transparent";
      const channels = getComputedStyle(document.documentElement)
        .getPropertyValue(token)
        .trim();
      if (!channels) return "transparent";
      return alpha === 1 ? `rgb(${channels})` : `rgb(${channels} / ${alpha})`;
    },
    // resolvedTheme is not read directly, but it is what makes the values
    // change, so it has to invalidate this callback.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [resolvedTheme],
  );
}
