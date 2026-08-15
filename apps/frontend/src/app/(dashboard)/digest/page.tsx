"use client";

import {
  IconArrowDown,
  IconArrowUp,
  IconCheck,
  IconMinus,
  IconSend,
  IconSparkles,
} from "@tabler/icons-react";
import Link from "next/link";
import { Badge, type BadgeVariant } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState, ErrorState, SkeletonCard } from "@/components/ui/States";
import { cn } from "@/lib/cn";
import { useDigest, useSendDigest } from "@/lib/queries";
import type { DigestTeam, Metric, TeamStatus } from "@/lib/types";

const STATUS_LABEL: Record<TeamStatus, string> = {
  healthy: "Healthy",
  "at-risk": "At risk",
  critical: "Critical",
};

const STATUS_BADGE_VARIANT: Record<TeamStatus, BadgeVariant> = {
  healthy: "success",
  "at-risk": "warning",
  critical: "error",
};

function formatRange(start: string, end: string) {
  const options: Intl.DateTimeFormatOptions = {
    month: "short",
    day: "numeric",
  };
  return `${new Date(start).toLocaleDateString("en-US", options)} – ${new Date(
    end,
  ).toLocaleDateString("en-US", options)}`;
}

function MetricPill({ metric }: { metric: Metric }) {
  const Icon =
    metric.direction === "up"
      ? IconArrowUp
      : metric.direction === "down"
        ? IconArrowDown
        : IconMinus;

  const tone =
    metric.trend === "bad"
      ? "text-state-error-fg"
      : metric.trend === "caution"
        ? "text-state-warning-fg"
        : "text-neutral-secondary";

  return (
    <span className="inline-flex items-baseline gap-1.5 text-xs">
      <span className="text-neutral-tertiary">{metric.label}</span>
      <span className="font-medium text-neutral-primary">
        {metric.value}
        {metric.unit}
      </span>
      <span className={cn("inline-flex items-center gap-0.5", tone)}>
        <Icon className="size-3" stroke={2.25} aria-hidden="true" />
        {Math.abs(metric.delta)}%
      </span>
    </span>
  );
}

function TeamDigest({ team }: { team: DigestTeam }) {
  return (
    <Card className="p-4 sm:p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2.5">
            <Link
              href={`/teams/${team.teamId}`}
              className="text-base font-semibold text-neutral-primary hover:text-brand"
            >
              {team.name}
            </Link>
            <Badge variant={STATUS_BADGE_VARIANT[team.status]}>
              {STATUS_LABEL[team.status]}
            </Badge>
          </div>
          <p className="mt-1 text-xs text-neutral-tertiary">
            Health {team.healthScore}/100 · {team.openAnomalies.length} open ·{" "}
            {team.resolved.length} cleared this period
          </p>
        </div>

        <div className="flex flex-wrap gap-x-4 gap-y-1">
          {team.metrics.slice(0, 3).map((metric) => (
            <MetricPill key={metric.id} metric={metric} />
          ))}
        </div>
      </div>

      {team.summary ? (
        <div className="mt-4 rounded-control border-l-4 border-brand bg-neutral-lighter-alt p-3">
          <span className="inline-flex items-center gap-1.5 text-xs font-medium text-brand">
            <IconSparkles
              className="size-3.5"
              stroke={1.75}
              aria-hidden="true"
            />
            Phi-4 summary
          </span>
          <p className="mt-2 text-sm leading-relaxed text-neutral-primary">
            {team.summary}
          </p>
          {team.suggestions.length > 0 && (
            <ul className="mt-3 flex list-disc flex-col gap-1 pl-5 text-sm text-neutral-secondary">
              {team.suggestions.map((suggestion) => (
                <li key={suggestion}>{suggestion}</li>
              ))}
            </ul>
          )}
        </div>
      ) : (
        <p className="mt-4 text-sm text-neutral-tertiary">
          No Phi-4 verdict yet for this team.
        </p>
      )}

      {team.openAnomalies.length > 0 && (
        <div className="mt-4">
          <h3 className="text-xs font-medium text-neutral-tertiary">
            Still open
          </h3>
          <ul className="mt-2 flex flex-col gap-1.5">
            {team.openAnomalies.map((anomaly) => (
              <li key={anomaly.id} className="flex items-start gap-2 text-sm">
                <Badge
                  variant={
                    anomaly.severity === "critical"
                      ? "error"
                      : anomaly.severity === "warning"
                        ? "warning"
                        : "neutral"
                  }
                  className="shrink-0"
                >
                  {anomaly.severity}
                </Badge>
                <span className="text-neutral-secondary">{anomaly.title}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {team.resolved.length > 0 && (
        <div className="mt-4 border-t border-neutral-light pt-3">
          <h3 className="text-xs font-medium text-neutral-tertiary">
            Cleared this period
          </h3>
          <ul className="mt-2 flex flex-col gap-2">
            {team.resolved.map((item) => (
              <li
                key={`${item.metric}-${item.resolvedAt}`}
                className="flex items-start gap-2 text-sm"
              >
                <IconCheck
                  className="mt-0.5 size-4 shrink-0 text-state-success"
                  stroke={2}
                  aria-hidden="true"
                />
                <span className="min-w-0 text-neutral-secondary">
                  <span className="text-neutral-primary">
                    {item.metricLabel}
                  </span>{" "}
                  cleared after {item.openDays} days
                  {item.action && (
                    <>
                      {" "}
                      · advice at the time:{" "}
                      <span className="italic">{item.action}</span>
                    </>
                  )}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </Card>
  );
}

export default function DigestPage() {
  const digestQuery = useDigest();
  const sendDigest = useSendDigest();
  const digest = digestQuery.data;

  return (
    <div className="flex w-full flex-col gap-6 p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-neutral-primary">
            Weekly digest
          </h1>
          <p className="mt-1 text-sm text-neutral-secondary">
            {digest
              ? `${formatRange(digest.periodStart, digest.periodEnd)} · what is wrong, what was advised, and what cleared.`
              : "What is wrong, what was advised, and what cleared."}
          </p>
        </div>

        <div className="flex flex-col items-end gap-1">
          <Button
            variant="secondary"
            onClick={() => sendDigest.mutate()}
            disabled={sendDigest.isPending}
          >
            <IconSend className="size-4" stroke={1.75} aria-hidden="true" />
            {sendDigest.isPending ? "Sending" : "Send to Teams"}
          </Button>
          {sendDigest.isSuccess && (
            <span className="text-xs text-neutral-tertiary">
              {sendDigest.data.webhookConfigured
                ? `${sendDigest.data.sent} team cards posted`
                : "No Teams webhook configured in .env"}
            </span>
          )}
          {sendDigest.isError && (
            <span className="text-xs text-state-error-fg">
              {(sendDigest.error as Error).message}
            </span>
          )}
        </div>
      </div>

      {digestQuery.isPending ? (
        <>
          <SkeletonCard lines={4} />
          <SkeletonCard lines={4} />
        </>
      ) : digestQuery.isError ? (
        <ErrorState
          error={digestQuery.error}
          onRetry={() => digestQuery.refetch()}
        />
      ) : !digest || digest.teams.length === 0 ? (
        <EmptyState
          title="Nothing to report yet"
          description="Load demo data or collect from a repository, and the digest will fill in."
        />
      ) : (
        <>
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            {[
              { label: "Teams", value: digest.totals.teams },
              {
                label: "Needing attention",
                value: digest.totals.needingAttention,
              },
              { label: "Open anomalies", value: digest.totals.openAnomalies },
              {
                label: "Cleared this period",
                value: digest.totals.resolvedInPeriod,
              },
            ].map((tile) => (
              <Card key={tile.label} className="p-4">
                <p className="text-xs font-medium text-neutral-secondary">
                  {tile.label}
                </p>
                <p className="mt-2 text-2xl font-semibold text-neutral-primary">
                  {tile.value}
                </p>
              </Card>
            ))}
          </div>

          <div className="flex flex-col gap-4">
            {digest.teams.map((team) => (
              <TeamDigest key={team.teamId} team={team} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
