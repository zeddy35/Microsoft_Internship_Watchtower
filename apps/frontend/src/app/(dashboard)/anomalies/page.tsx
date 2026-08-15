"use client";

import { useState } from "react";
import { AnomalyTable } from "@/components/anomaly/AnomalyTable";
import { ErrorState, SkeletonCard } from "@/components/ui/States";
import { cn } from "@/lib/cn";
import { useAnomalies } from "@/lib/queries";
import type { AnomalySeverity } from "@/lib/types";

const FILTERS: { label: string; value: AnomalySeverity | undefined }[] = [
  { label: "All", value: undefined },
  { label: "Critical", value: "critical" },
  { label: "Warning", value: "warning" },
  { label: "Info", value: "info" },
];

export default function AnomaliesPage() {
  const [severity, setSeverity] = useState<AnomalySeverity | undefined>();
  const anomaliesQuery = useAnomalies(severity);

  return (
    <div className="flex w-full flex-col gap-6 p-6">
      <div>
        <h1 className="text-2xl font-semibold text-neutral-primary">
          Anomalies
        </h1>
        <p className="mt-1 text-sm text-neutral-secondary">
          Every open deviation across tracked teams, worst first.
        </p>
      </div>

      <div className="flex flex-wrap gap-2" role="group" aria-label="Filter by severity">
        {FILTERS.map((filter) => {
          const active = filter.value === severity;
          return (
            <button
              key={filter.label}
              type="button"
              aria-pressed={active}
              onClick={() => setSeverity(filter.value)}
              className={cn(
                "rounded-control border px-3 py-1.5 text-xs font-medium transition-colors",
                active
                  ? "border-brand bg-brand-tint text-brand"
                  : "border-neutral-light bg-neutral-white text-neutral-secondary hover:bg-neutral-lighter",
              )}
            >
              {filter.label}
            </button>
          );
        })}
      </div>

      {anomaliesQuery.isPending ? (
        <SkeletonCard lines={6} />
      ) : anomaliesQuery.isError ? (
        <ErrorState
          error={anomaliesQuery.error}
          onRetry={() => anomaliesQuery.refetch()}
        />
      ) : (
        <AnomalyTable
          anomalies={anomaliesQuery.data ?? []}
          emptyTitle="Nothing flagged"
          emptyDescription="No open anomalies match this filter."
        />
      )}
    </div>
  );
}
