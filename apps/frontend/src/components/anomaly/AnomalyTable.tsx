// Cross-team anomaly table: severity pill, title + description, team link, age.
// Usage: <AnomalyTable anomalies={anomalies} emptyTitle="No critical anomalies" />
import Link from "next/link";
import { Badge, type BadgeVariant } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/States";
import { cn } from "@/lib/cn";
import type { Anomaly, AnomalySeverity } from "@/lib/types";

const SEVERITY_BADGE_VARIANT: Record<AnomalySeverity, BadgeVariant> = {
  info: "neutral",
  warning: "warning",
  critical: "error",
};

const SEVERITY_LABEL: Record<AnomalySeverity, string> = {
  info: "Info",
  warning: "Warning",
  critical: "Critical",
};

export function formatDetectedAt(detectedAt: string) {
  const diffHours = Math.max(
    0,
    Math.round((Date.now() - new Date(detectedAt).getTime()) / 3_600_000),
  );
  if (diffHours < 1) return "Just now";
  if (diffHours < 24) return `${diffHours}h ago`;
  return `${Math.round(diffHours / 24)}d ago`;
}

export interface AnomalyTableProps {
  anomalies: Anomaly[];
  emptyTitle: string;
  emptyDescription?: string;
  className?: string;
}

export function AnomalyTable({
  anomalies,
  emptyTitle,
  emptyDescription,
  className,
}: AnomalyTableProps) {
  if (anomalies.length === 0) {
    return (
      <EmptyState
        title={emptyTitle}
        description={emptyDescription}
        className={className}
      />
    );
  }

  return (
    <Card className={cn("overflow-hidden", className)}>
      <ul className="flex flex-col divide-y divide-neutral-light">
        {anomalies.map((anomaly) => (
          <li
            key={anomaly.id}
            className="flex flex-wrap items-start gap-3 p-4 sm:flex-nowrap"
          >
            <Badge
              variant={SEVERITY_BADGE_VARIANT[anomaly.severity]}
              className="shrink-0"
            >
              {SEVERITY_LABEL[anomaly.severity]}
            </Badge>

            <div className="min-w-0 flex-1">
              <p className="text-sm font-semibold text-neutral-primary">
                {anomaly.title}
              </p>
              <p className="mt-0.5 text-sm text-neutral-secondary">
                {anomaly.description}
              </p>
            </div>

            <div className="flex shrink-0 items-center gap-4 text-xs text-neutral-tertiary">
              <Link
                href={`/teams/${anomaly.teamId}`}
                className="font-medium text-brand hover:underline"
              >
                {anomaly.teamId}
              </Link>
              <span>{formatDetectedAt(anomaly.detectedAt)}</span>
            </div>
          </li>
        ))}
      </ul>
    </Card>
  );
}
