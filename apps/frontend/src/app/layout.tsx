import type { Metadata } from "next";
import "./globals.css";
import { QueryProvider } from "@/components/providers/QueryProvider";
import { THEME_INIT_SCRIPT, ThemeProvider } from "@/lib/theme";

export const metadata: Metadata = {
  title: "Watchtower",
  description: "Team health and anomaly monitoring",
};

// The shell lives in the (dashboard) layout, not here: the sign-in page is a
// centered card with no nav rail, and it shares only the html/body chrome.
export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased" suppressHydrationWarning>
      <head>
        {/* Blocking on purpose: it sets the theme class before first paint, so
            a dark-mode user never sees a white flash. */}
        <script dangerouslySetInnerHTML={{ __html: THEME_INIT_SCRIPT }} />
      </head>
      <body className="flex min-h-full flex-col">
        <ThemeProvider>
          <QueryProvider>{children}</QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
