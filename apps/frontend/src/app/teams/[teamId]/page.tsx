"use client";

import {
  IconClockHour4,
  IconGitCommit,
  IconTarget,
  IconUpload,
} from "@tabler/icons-react";
import { notFound, useParams } from "next/navigation";
import type { ComponentType } from "react";
import { ReviewTimeChart } from "@/components/charts/ReviewTimeChart";
import { ActiveAnomaliesCard } from "@/components/team/ActiveAnomaliesCard";
import { BusFactorRiskCard } from "@/components/team/BusFactorRiskCard";
import { Phi4Summary } from "@/components/team/Phi4Summary";
import { TeamHeader } from "@/components/team/TeamHeader";
import { TeamMembersCard } from "@/components/team/TeamMembersCard";
import { Card } from "@/components/ui/Card";
import { KpiCard } from "@/components/ui/KpiCard";
import {
  anomalies,
  metrics,
  reviewTimeHistory,
  team,
  teamSummary,
} from "@/lib/mock/azure-core-networking";
import type { Metric, MetricDirection } from "@/lib/types";

type IconComponent = ComponentType<{ className?: string; stroke?: number }>;

const METRIC_ICONS: Record<string, IconComponent> = {
  "commit-activity": IconGitCommit,
  "push-frequency": IconUpload,
  "pr-review-time": IconClockHour4,
  "on-goal-commits": IconTarget,
};

const DIRECTION_LABEL: Record<MetricDirection, string> = {
  up: "Up",
  down: "Down",
  flat: "Flat",
};

function formatMetricValue(metric: Metric) {
  return `${metric.value}${metric.unit}`;
}

function formatDeltaLabel(metric: Metric) {
  return `${DIRECTION_LABEL[metric.direction]} ${Math.abs(metric.delta)}%`;
}

export default function TeamDrillDownPage() {
  const params = useParams<{ teamId: string }>();

  if (params.teamId !== team.id) {
    notFound();
  }

  function handleAsk(question: string) {
    console.log("Ask Phi-4:", question);
  }

  return (
    <div className="flex w-full flex-col gap-6 p-6">
      <TeamHeader
        name={team.name}
        status={team.status}
        engineerCount={team.engineerCount}
        source={team.source}
        healthScore={team.healthScore}
      />

      <Phi4Summary
        summary={teamSummary.summary}
        suggestions={teamSummary.suggestions}
        onAsk={handleAsk}
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {metrics.map((metric) => (
          <KpiCard
            key={metric.id}
            icon={METRIC_ICONS[metric.id] ?? IconGitCommit}
            label={metric.label}
            value={formatMetricValue(metric)}
            direction={metric.direction}
            deltaLabel={formatDeltaLabel(metric)}
            trend={metric.trend}
          />
        ))}
      </div>

      <Card className="p-4 sm:p-5">
        <h2 className="text-sm font-semibold text-neutral-primary">
          PR review time · last 30 days
        </h2>
        <ReviewTimeChart data={reviewTimeHistory} className="mt-4" />
      </Card>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <BusFactorRiskCard areas={team.busFactorAreas} />
        <ActiveAnomaliesCard anomalies={anomalies} />
      </div>

      <TeamMembersCard members={team.members} />
    </div>
  );
}
