import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
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
          DEFAULT: "#0078d4",
          hover: "#106ebe",
          dark: "#005a9e",
          darker: "#004578",
          light: "#c7e0f4",
          lighter: "#deecf9",
          tint: "#eff6fc",
        },
        neutral: {
          white: "#ffffff",
          "lighter-alt": "#faf9f8",
          lighter: "#f3f2f1",
          light: "#edebe9",
          quaternary: "#e1dfdd",
          "tertiary-alt": "#c8c6c4",
          tertiary: "#a19f9d",
          secondary: "#605e5c",
          "primary-alt": "#3b3a39",
          primary: "#323130",
          dark: "#201f1e",
        },
        state: {
          success: "#107c10",
          "success-bg": "#dff6dd",
          warning: "#ffb900",
          "warning-fg": "#8a6d00",
          "warning-bg": "#fff4ce",
          severe: "#d83b01",
          "severe-bg": "#fed9cc",
          "severe-fg": "#8a3707",
          error: "#d13438",
          "error-fg": "#a4262c",
          "error-bg": "#fde7e9",
        },
      },
      borderRadius: {
        card: "6px",
        control: "4px",
      },
      boxShadow: {
        card: "0 1px 2px rgba(0,0,0,.06)",
        fluent: "0 1.6px 3.6px rgba(0,0,0,.132), 0 0.3px 0.9px rgba(0,0,0,.108)",
      },
    },
  },
  plugins: [],
};

export default config;
