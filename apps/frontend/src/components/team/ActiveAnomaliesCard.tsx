import { SectionCard } from "@/components/ui/SectionCard";
import { cn } from "@/lib/cn";
import type { Anomaly, AnomalySeverity } from "@/lib/types";

export interface ActiveAnomaliesCardProps {
  anomalies: Anomaly[];
  className?: string;
}

const SEVERITY_STYLES: Record<
  AnomalySeverity,
  { container: string; dot: string }
> = {
  critical: { container: "border-error/10 bg-error-container/5", dot: "bg-error animate-pulse" },
  warning: { container: "border-tertiary/10 bg-tertiary-fixed/10", dot: "bg-tertiary" },
  info: { container: "border-outline-variant bg-surface-container/50", dot: "bg-outline" },
};

const ACTION_LABEL: Record<AnomalySeverity, string> = {
  critical: "View details",
  warning: "Investigate",
  info: "View details",
};

function formatDetectedAt(detectedAt: string) {
  const detected = new Date(detectedAt).getTime();
  const diffHours = Math.max(0, Math.round((Date.now() - detected) / 3_600_000));

  if (diffHours < 1) return "Just now";
  if (diffHours < 24) return `${diffHours}h ago`;
  return `${Math.round(diffHours / 24)}d ago`;
}

export function ActiveAnomaliesCard({ anomalies, className }: ActiveAnomaliesCardProps) {
  return (
    <SectionCard title="Active Anomalies" className={className}>
      <div className="space-y-4">
        {anomalies.map((anomaly) => {
          const styles = SEVERITY_STYLES[anomaly.severity];

          return (
            <div key={anomaly.id} className={cn("flex gap-4 rounded border p-4", styles.container)}>
              <div className={cn("mt-1.5 size-2 shrink-0 rounded-full", styles.dot)} />
              <div className="flex-1">
                <div className="mb-1 flex items-start justify-between">
                  <h4 className="text-body-md font-semibold">{anomaly.title}</h4>
                  <span className="text-body-sm text-secondary">
                    {formatDetectedAt(anomaly.detectedAt)}
                  </span>
                </div>
                <p className="text-body-sm text-on-surface-variant">
                  {anomaly.description}
                </p>
                <button
                  type="button"
                  className="mt-3 text-body-sm font-semibold text-primary hover:underline"
                >
                  {ACTION_LABEL[anomaly.severity]}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </SectionCard>
  );
}
