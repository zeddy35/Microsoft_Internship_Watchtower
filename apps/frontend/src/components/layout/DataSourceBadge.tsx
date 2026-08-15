"use client";

import Link from "next/link";
import { Badge } from "@/components/ui/Badge";
import { IS_HOSTED_DEMO } from "@/lib/api";
import { useAppSettings } from "@/lib/queries";

/**
 * Says out loud when the numbers on screen are fabricated.
 *
 * A dashboard that cannot tell you where its data came from is worse than an
 * empty one, and demo data is exactly the situation where someone might
 * forget. Nothing is shown for real data: that is the unremarkable case.
 */
export function DataSourceBadge() {
  const { data } = useAppSettings();
  if (data?.dataSource !== "demo") return null;

  return (
    <Link
      href="/settings"
      title={
        IS_HOSTED_DEMO
          ? "Fabricated data served from a snapshot; no backend is attached"
          : "Change the data source in Settings"
      }
    >
      <Badge variant="warning">
        {IS_HOSTED_DEMO ? "Hosted demo · fabricated data" : "Demo data"}
      </Badge>
    </Link>
  );
}
