"use client";

import {
  IconAlertTriangle,
  IconHeartRateMonitor,
  IconRefresh,
  IconUsersGroup,
} from "@tabler/icons-react";
import Link from "next/link";
import { AnomalyTable } from "@/components/anomaly/AnomalyTable";
import { TeamHealthCard } from "@/components/team/TeamHealthCard";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState, ErrorState, SkeletonCard } from "@/components/ui/States";
import { useAnomalies, useRefreshNow, useTeams } from "@/lib/queries";
import type { Team } from "@/lib/types";

function summarize(teams: Team[]) {
  const critical = teams.filter((team) => team.status === "critical").length;
  const atRisk = teams.filter((team) => team.status === "at-risk").length;
  const averageHealth = teams.length
    ? Math.round(
        teams.reduce((sum, team) => sum + team.healthScore, 0) / teams.length,
      )
    : 0;
  return { critical, atRisk, averageHealth };
}

function StatTile({
  icon: Icon,
  label,
  value,
  tone = "default",
}: {
  icon: typeof IconUsersGroup;
  label: string;
  value: string;
  tone?: "default" | "warning" | "error";
}) {
  const valueClass =
    tone === "error"
      ? "text-state-error-fg"
      : tone === "warning"
        ? "text-state-warning-fg"
        : "text-neutral-primary";

  return (
    <Card className="p-4">
      <div className="flex items-center gap-1.5 text-neutral-secondary">
        <Icon className="size-4" stroke={1.75} aria-hidden="true" />
        <span className="text-xs font-medium">{label}</span>
      </div>
      <p className={`mt-2 text-2xl font-semibold ${valueClass}`}>{value}</p>
    </Card>
  );
}

export default function OverviewPage() {
  const teamsQuery = useTeams();
  const anomaliesQuery = useAnomalies("critical");
  const refresh = useRefreshNow();

  const teams = teamsQuery.data ?? [];
  const { critical, atRisk, averageHealth } = summarize(teams);

  return (
    <div className="flex w-full flex-col gap-6 p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-neutral-primary">
            Overview
          </h1>
          <p className="mt-1 text-sm text-neutral-secondary">
            Team health and anomaly monitoring at a glance.
          </p>
        </div>
        <Button
          variant="secondary"
          onClick={() => refresh.mutate()}
          disabled={refresh.isPending}
        >
          <IconRefresh
            className={`size-4 ${refresh.isPending ? "animate-spin" : ""}`}
            stroke={1.75}
            aria-hidden="true"
          />
          {refresh.isPending ? "Refreshing" : "Refresh now"}
        </Button>
      </div>

      {teamsQuery.isError ? (
        <ErrorState
          error={teamsQuery.error}
          onRetry={() => teamsQuery.refetch()}
        />
      ) : (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatTile
              icon={IconUsersGroup}
              label="Teams tracked"
              value={teamsQuery.isPending ? "—" : String(teams.length)}
            />
            <StatTile
              icon={IconAlertTriangle}
              label="Critical teams"
              value={teamsQuery.isPending ? "—" : String(critical)}
              tone={critical > 0 ? "error" : "default"}
            />
            <StatTile
              icon={IconAlertTriangle}
              label="At-risk teams"
              value={teamsQuery.isPending ? "—" : String(atRisk)}
              tone={atRisk > 0 ? "warning" : "default"}
            />
            <StatTile
              icon={IconHeartRateMonitor}
              label="Average health"
              value={teamsQuery.isPending ? "—" : `${averageHealth}/100`}
            />
          </div>

          <section>
            <h2 className="text-sm font-semibold text-neutral-primary">
              Team health
            </h2>
            {teamsQuery.isPending ? (
              <div className="mt-3 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
                {Array.from({ length: 3 }, (_, index) => (
                  <SkeletonCard key={index} lines={4} />
                ))}
              </div>
            ) : teams.length === 0 ? (
              <EmptyState
                className="mt-3"
                title="No teams yet"
                description={
                  <>
                    Set <code>GITHUB_REPOS</code> in the backend&apos;s .env and
                    run a refresh to start collecting.
                  </>
                }
              />
            ) : (
              <div className="mt-3 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
                {teams.map((team) => (
                  <TeamHealthCard key={team.id} team={team} />
                ))}
              </div>
            )}
          </section>

          <section>
            <div className="flex items-center justify-between gap-3">
              <h2 className="text-sm font-semibold text-neutral-primary">
                Critical anomalies
              </h2>
              <Link
                href="/anomalies"
                className="text-xs font-medium text-brand hover:underline"
              >
                View all
              </Link>
            </div>
            <div className="mt-3">
              {anomaliesQuery.isPending ? (
                <SkeletonCard lines={4} />
              ) : anomaliesQuery.isError ? (
                <ErrorState
                  error={anomaliesQuery.error}
                  onRetry={() => anomaliesQuery.refetch()}
                />
              ) : (
                <AnomalyTable
                  anomalies={anomaliesQuery.data ?? []}
                  emptyTitle="No critical anomalies"
                  emptyDescription="Every tracked team is inside its baseline right now."
                />
              )}
            </div>
          </section>
        </>
      )}
    </div>
  );
}
