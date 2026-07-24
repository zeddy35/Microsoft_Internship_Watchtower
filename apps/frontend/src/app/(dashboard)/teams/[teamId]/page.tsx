"use client";

import { notFound, useParams } from "next/navigation";
import { ReviewTimeChart } from "@/components/charts/ReviewTimeChart";
import { ActiveAnomaliesCard } from "@/components/team/ActiveAnomaliesCard";
import { BusFactorRiskCard } from "@/components/team/BusFactorRiskCard";
import { Phi4Summary } from "@/components/team/Phi4Summary";
import { TeamHeader } from "@/components/team/TeamHeader";
import { TeamMembersCard } from "@/components/team/TeamMembersCard";
import { SectionCard } from "@/components/ui/SectionCard";
import { KpiCard } from "@/components/ui/KpiCard";
import {
  anomalies,
  metrics,
  reviewTimeHistory,
  team,
  teamSummary,
} from "@/lib/mock/azure-core-networking";
import type { Metric } from "@/lib/types";

function formatMetricValue(metric: Metric) {
  return `${metric.value}${metric.unit}`;
}

function formatTrendLabel(metric: Metric) {
  if (metric.id === "on-goal-commits") {
    return `Goal: ${metric.baseline}%`;
  }
  return `${Math.abs(metric.delta)}%`;
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
    <div className="space-y-6 p-margin_page">
      <TeamHeader
        name={team.name}
        status={team.status}
        engineerCount={team.engineerCount}
        source={team.source}
        healthScore={team.healthScore}
      />

      <div className="grid grid-cols-12 gap-gutter">
        <Phi4Summary
          summary={teamSummary.summary}
          suggestions={teamSummary.suggestions}
          onAsk={handleAsk}
          className="col-span-12 lg:col-span-8"
        />

        <BusFactorRiskCard areas={team.busFactorAreas} className="col-span-12 lg:col-span-4" />

        <div className="col-span-12 grid grid-cols-1 gap-gutter md:grid-cols-2 lg:grid-cols-4">
          {metrics.map((metric) => (
            <KpiCard
              key={metric.id}
              label={metric.label}
              value={formatMetricValue(metric)}
              trend={metric.trend}
              direction={metric.id === "on-goal-commits" ? "flat" : metric.direction}
              trendLabel={formatTrendLabel(metric)}
            />
          ))}
        </div>

        <SectionCard
          title="PR review time · last 30 days"
          className="col-span-12 lg:col-span-7"
          action={
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-1.5">
                <div className="size-2.5 rounded-full bg-primary" />
                <span className="text-body-sm">Current</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="h-0.5 w-2.5 bg-outline opacity-40" />
                <span className="text-body-sm text-secondary">Baseline</span>
              </div>
            </div>
          }
        >
          <ReviewTimeChart data={reviewTimeHistory} />
        </SectionCard>

        <ActiveAnomaliesCard anomalies={anomalies} className="col-span-12 lg:col-span-5" />

        <TeamMembersCard members={team.members} className="col-span-12" />
      </div>
    </div>
  );
}
