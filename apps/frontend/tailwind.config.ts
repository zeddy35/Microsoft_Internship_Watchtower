import forms from "@tailwindcss/forms";
import type { Config } from "tailwindcss";

// Design tokens aligned to the approved Stitch exports (Microsoft Fluent look,
// Material-3 token names). Fonts prefer Segoe UI on Microsoft machines and fall
// back to Inter so the design matches Stitch everywhere else.

const sans = [
  '"Segoe UI"',
  '"Segoe UI Web (West European)"',
  "Inter",
  "system-ui",
  "sans-serif",
];
const mono = ['"JetBrains Mono"', "ui-monospace", "monospace"];

const config: Config = {
  darkMode: "class",
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: "#005faa",
        "primary-container": "#0078d4", // Fluent communication blue (buttons/brand)
        "on-primary": "#ffffff",
        "on-primary-container": "#ffffff",
        "primary-fixed": "#d3e3ff",
        "primary-fixed-dim": "#a3c9ff",
        "on-primary-fixed": "#001c39",
        "on-primary-fixed-variant": "#004883",
        "inverse-primary": "#a3c9ff",
        secondary: "#605e5c",
        "on-secondary": "#ffffff",
        "secondary-container": "#e6e2df",
        "on-secondary-container": "#666462",
        "secondary-fixed": "#e6e2df",
        "secondary-fixed-dim": "#c9c6c3",
        "on-secondary-fixed": "#1c1b1a",
        "on-secondary-fixed-variant": "#484645",
        tertiary: "#974700", // "at risk" amber/orange accent
        "on-tertiary": "#ffffff",
        "tertiary-container": "#bc5b00",
        "tertiary-fixed": "#ffdbc8",
        "tertiary-fixed-dim": "#ffb689",
        "on-tertiary-fixed": "#311300",
        "on-tertiary-fixed-variant": "#743500",
        "on-tertiary-container": "#ffffff",
        error: "#ba1a1a",
        "on-error": "#ffffff",
        "error-container": "#ffdad6",
        "on-error-container": "#93000a",
        background: "#faf9f8",
        "on-background": "#1a1c1c",
        surface: "#faf9f8",
        "on-surface": "#1a1c1c",
        "surface-variant": "#e3e2e1",
        "on-surface-variant": "#404752",
        "surface-dim": "#dadad9",
        "surface-bright": "#faf9f8",
        "surface-container-lowest": "#ffffff",
        "surface-container-low": "#f4f3f2",
        "surface-container": "#eeeeed",
        "surface-container-high": "#e9e8e7",
        "surface-container-highest": "#e3e2e1",
        "surface-tint": "#0060ab",
        outline: "#717783",
        "outline-variant": "#c0c7d4", // soften to #edebe9 for a lighter hairline
        "inverse-surface": "#2f3130",
        "inverse-on-surface": "#f1f0ef",
      },
      borderRadius: {
        DEFAULT: "2px",
        lg: "4px",
        xl: "8px",
        "2xl": "12px",
        full: "9999px", // fixed from Stitch export so avatars/pills are truly round
      },
      spacing: {
        base: "4px",
        xs: "4px",
        sm: "8px",
        md: "16px",
        lg: "24px",
        xl: "32px",
        gutter: "16px",
        "margin-mobile": "16px",
        "margin-desktop": "40px",
        margin_page: "24px",
        stack_sm: "4px",
        stack_md: "8px",
        stack_lg: "16px",
        card_padding: "16px",
        nav_width: "200px",
        nav_rail_width: "200px",
      },
      fontFamily: {
        sans,
        fluent: sans,
        "body-md": sans,
        "body-lg": sans,
        "body-sm": sans,
        "label-md": sans,
        "label-uppercase": sans,
        "title-sm": sans,
        "display-lg": sans,
        "headline-sm": sans,
        "headline-md": sans,
        "headline-lg": sans,
        "headline-lg-mobile": sans,
        code: mono,
        "code-snippet": mono,
      },
      fontSize: {
        "body-sm": ["12px", { lineHeight: "16px", fontWeight: "400" }],
        "body-md": ["14px", { lineHeight: "20px", fontWeight: "400" }],
        "body-lg": ["16px", { lineHeight: "24px", fontWeight: "400" }],
        "label-md": ["12px", { lineHeight: "16px", fontWeight: "600" }],
        "label-uppercase": [
          "11px",
          { lineHeight: "16px", letterSpacing: "0.05em", fontWeight: "700" },
        ],
        "title-sm": ["16px", { lineHeight: "22px", fontWeight: "600" }],
        "display-lg": [
          "28px",
          { lineHeight: "36px", letterSpacing: "-0.01em", fontWeight: "600" },
        ],
        "headline-sm": ["16px", { lineHeight: "22px", fontWeight: "600" }],
        "headline-md": ["20px", { lineHeight: "28px", fontWeight: "600" }],
        "headline-lg": [
          "28px",
          { lineHeight: "36px", letterSpacing: "-0.01em", fontWeight: "600" },
        ],
        "headline-lg-mobile": ["28px", { lineHeight: "36px", fontWeight: "600" }],
        code: ["13px", { lineHeight: "18px", fontWeight: "400" }],
        "code-snippet": ["13px", { lineHeight: "20px", fontWeight: "400" }],
      },
      boxShadow: {
        card: "0px 1.6px 3.6px rgba(0,0,0,0.13), 0px 0.3px 0.9px rgba(0,0,0,0.11)",
        "card-hover":
          "0px 3.2px 7.2px rgba(0,0,0,0.13), 0px 0.6px 1.8px rgba(0,0,0,0.11)",
      },
    },
  },
  plugins: [forms],
};

export default config;
