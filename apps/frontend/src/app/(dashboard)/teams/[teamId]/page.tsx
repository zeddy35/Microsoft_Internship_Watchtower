"use client";

import {
  IconClockHour4,
  IconGitCommit,
  IconTarget,
  IconUpload,
} from "@tabler/icons-react";
import { useParams } from "next/navigation";
import type { ComponentType } from "react";
import { ReviewTimeChart } from "@/components/charts/ReviewTimeChart";
import { ActiveAnomaliesCard } from "@/components/team/ActiveAnomaliesCard";
import { BusFactorRiskCard } from "@/components/team/BusFactorRiskCard";
import { Phi4Summary } from "@/components/team/Phi4Summary";
import { TeamHeader } from "@/components/team/TeamHeader";
import { TeamMembersCard } from "@/components/team/TeamMembersCard";
import { Card } from "@/components/ui/Card";
import { KpiCard } from "@/components/ui/KpiCard";
import { EmptyState, ErrorState, Skeleton, SkeletonCard } from "@/components/ui/States";
import {
  useAskTeam,
  useTeam,
  useTeamAnomalies,
  useTeamMetrics,
  useTeamSummary,
} from "@/lib/queries";
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

// Fallback chips when the resolver has not produced suggestions yet, so the
// question box is still useful on a cold database.
const DEFAULT_QUESTIONS = [
  "What changed this week?",
  "Who is carrying the review load?",
  "What should we do first?",
];

export default function TeamDrillDownPage() {
  const params = useParams<{ teamId: string }>();
  const teamId = params.teamId;

  const teamQuery = useTeam(teamId);
  const metricsQuery = useTeamMetrics(teamId);
  const anomaliesQuery = useTeamAnomalies(teamId);
  const summaryQuery = useTeamSummary(teamId);
  const ask = useAskTeam(teamId);

  if (teamQuery.isError) {
    return (
      <div className="p-6">
        <ErrorState
          error={teamQuery.error}
          onRetry={() => teamQuery.refetch()}
        />
      </div>
    );
  }

  const team = teamQuery.data;
  const metrics = metricsQuery.data?.metrics ?? [];
  const reviewTimeHistory = metricsQuery.data?.reviewTimeHistory ?? [];
  const summary = summaryQuery.data;

  return (
    <div className="flex w-full flex-col gap-6 p-6">
      {team ? (
        <TeamHeader
          name={team.name}
          status={team.status}
          engineerCount={team.engineerCount}
          source={team.source}
          healthScore={team.healthScore}
        />
      ) : (
        <Skeleton className="h-16 w-72" />
      )}

      {summaryQuery.isPending ? (
        <SkeletonCard lines={3} />
      ) : summary ? (
        <Phi4Summary
          summary={summary.summary}
          suggestions={summary.suggestions}
          onAsk={ask.ask}
          isStreaming={ask.isStreaming}
          answer={ask.answer}
          errorMessage={ask.error}
          onClearAnswer={ask.reset}
        />
      ) : (
        <Phi4Summary
          summary="No Phi-4 verdict has been generated for this team yet. Start the local model and run a refresh, or ask a question directly."
          suggestions={DEFAULT_QUESTIONS}
          onAsk={ask.ask}
          isStreaming={ask.isStreaming}
          answer={ask.answer}
          errorMessage={ask.error}
          onClearAnswer={ask.reset}
        />
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {metricsQuery.isPending
          ? Array.from({ length: 4 }, (_, index) => (
              <SkeletonCard key={index} lines={2} />
            ))
          : metrics.map((metric) => (
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
        {metricsQuery.isPending ? (
          <Skeleton className="mt-4 h-64 w-full" />
        ) : reviewTimeHistory.length > 0 ? (
          <ReviewTimeChart data={reviewTimeHistory} className="mt-4" />
        ) : (
          <EmptyState
            className="mt-4 border-0 shadow-none"
            title="No review data yet"
            description="No pull request in this window has been reviewed."
          />
        )}
      </Card>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {team ? (
          <BusFactorRiskCard areas={team.busFactorAreas} />
        ) : (
          <SkeletonCard lines={3} />
        )}

        {anomaliesQuery.isPending ? (
          <SkeletonCard lines={3} />
        ) : anomaliesQuery.isError ? (
          <ErrorState
            error={anomaliesQuery.error}
            onRetry={() => anomaliesQuery.refetch()}
          />
        ) : (anomaliesQuery.data ?? []).length > 0 ? (
          <ActiveAnomaliesCard anomalies={anomaliesQuery.data ?? []} />
        ) : (
          <EmptyState
            title="No active anomalies"
            description="This team is inside its baseline on every tracked metric."
          />
        )}
      </div>

      {team ? (
        <TeamMembersCard members={team.members} />
      ) : (
        <SkeletonCard lines={5} />
      )}
    </div>
  );
}
