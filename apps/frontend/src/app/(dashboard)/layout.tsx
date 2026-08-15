import { redirect } from "next/navigation";
import type { ReactNode } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { auth, isAuthConfigured } from "@/auth";

/**
 * Everything behind the nav rail.
 *
 * The guard is skipped when no Entra app is configured so the dashboard still
 * runs locally with nothing but the API; once the AUTH_MICROSOFT_ENTRA_ID_*
 * variables are set, an unauthenticated visitor lands on /signin.
 */
export default async function DashboardLayout({
  children,
}: {
  children: ReactNode;
}) {
  if (isAuthConfigured) {
    const session = await auth();
    if (!session?.user) redirect("/signin");
  }

  return <AppShell>{children}</AppShell>;
}
