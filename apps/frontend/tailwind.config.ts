import type { Config } from "tailwindcss";

/**
 * Colours resolve through CSS variables defined in globals.css, so the same
 * utility class (`bg-neutral-white`, `text-brand`) means the right thing in
 * both themes and no component carries `dark:` variants. The `<alpha-value>`
 * placeholder keeps opacity utilities like `bg-brand/30` working.
 */
const withAlpha = (variable: string) => `rgb(var(${variable}) / <alpha-value>)`;

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      fontFamily: {
        sans: [
          '"Segoe UI"',
          '"Segoe UI Web (West European)"',
          "-apple-system",
          "system-ui",
          "sans-serif",
        ],
      },
      colors: {
        brand: {
          DEFAULT: withAlpha("--brand"),
          hover: withAlpha("--brand-hover"),
          dark: withAlpha("--brand-dark"),
          darker: withAlpha("--brand-darker"),
          light: withAlpha("--brand-light"),
          lighter: withAlpha("--brand-lighter"),
          tint: withAlpha("--brand-tint"),
        },
        neutral: {
          white: withAlpha("--neutral-white"),
          "lighter-alt": withAlpha("--neutral-lighter-alt"),
          lighter: withAlpha("--neutral-lighter"),
          light: withAlpha("--neutral-light"),
          quaternary: withAlpha("--neutral-quaternary"),
          "tertiary-alt": withAlpha("--neutral-tertiary-alt"),
          tertiary: withAlpha("--neutral-tertiary"),
          secondary: withAlpha("--neutral-secondary"),
          "primary-alt": withAlpha("--neutral-primary-alt"),
          primary: withAlpha("--neutral-primary"),
          dark: withAlpha("--neutral-dark"),
        },
        state: {
          success: withAlpha("--state-success"),
          "success-bg": withAlpha("--state-success-bg"),
          warning: withAlpha("--state-warning"),
          "warning-fg": withAlpha("--state-warning-fg"),
          "warning-bg": withAlpha("--state-warning-bg"),
          severe: withAlpha("--state-severe"),
          "severe-bg": withAlpha("--state-severe-bg"),
          "severe-fg": withAlpha("--state-severe-fg"),
          error: withAlpha("--state-error"),
          "error-fg": withAlpha("--state-error-fg"),
          "error-bg": withAlpha("--state-error-bg"),
        },
      },
      borderRadius: {
        card: "6px",
        control: "4px",
      },
      boxShadow: {
        card: "0 1px 2px rgba(0,0,0,.06)",
        "card-hover": "0 3.2px 7.2px rgba(0,0,0,.132), 0 0.6px 1.8px rgba(0,0,0,.108)",
        fluent: "0 1.6px 3.6px rgba(0,0,0,.132), 0 0.3px 0.9px rgba(0,0,0,.108)",
      },
    },
  },
  plugins: [],
};

export default config;
