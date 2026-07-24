// "Active anomalies" card: severity dot, bold title, description, and a relative timestamp.
import { Card } from "@/components/ui/Card";
import { cn } from "@/lib/cn";
import type { Anomaly, AnomalySeverity } from "@/lib/types";

export interface ActiveAnomaliesCardProps {
  anomalies: Anomaly[];
  className?: string;
}

const SEVERITY_DOT_CLASSES: Record<AnomalySeverity, string> = {
  info: "bg-neutral-tertiary",
  warning: "bg-state-warning",
  critical: "bg-state-error",
};

function formatDetectedAt(detectedAt: string) {
  const detected = new Date(detectedAt).getTime();
  const diffHours = Math.max(
    0,
    Math.round((Date.now() - detected) / 3_600_000),
  );

  if (diffHours < 1) return "Just now";
  if (diffHours < 24) return `${diffHours}h ago`;
  return `${Math.round(diffHours / 24)}d ago`;
}

export function ActiveAnomaliesCard({
  anomalies,
  className,
}: ActiveAnomaliesCardProps) {
  return (
    <Card className={cn("p-4 sm:p-5", className)}>
      <h2 className="text-sm font-semibold text-neutral-primary">
        Active anomalies
      </h2>
      <ul className="mt-4 flex flex-col divide-y divide-neutral-light">
        {anomalies.map((anomaly) => (
          <li key={anomaly.id} className="flex gap-3 py-3 first:pt-0 last:pb-0">
            <span
              aria-hidden="true"
              className={cn(
                "mt-1.5 size-2 shrink-0 rounded-full",
                SEVERITY_DOT_CLASSES[anomaly.severity],
              )}
            />
            <div className="min-w-0 flex-1">
              <div className="flex items-baseline justify-between gap-3">
                <p className="text-sm font-semibold text-neutral-primary">
                  {anomaly.title}
                </p>
                <span className="shrink-0 text-xs text-neutral-tertiary">
                  {formatDetectedAt(anomaly.detectedAt)}
                </span>
              </div>
              <p className="mt-0.5 text-sm text-neutral-secondary">
                {anomaly.description}
              </p>
            </div>
          </li>
        ))}
      </ul>
    </Card>
  );
}
