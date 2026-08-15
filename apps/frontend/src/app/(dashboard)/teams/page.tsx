"use client";

import Link from "next/link";
import { Badge, type BadgeVariant } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { EmptyState, ErrorState, SkeletonCard } from "@/components/ui/States";
import { useTeams } from "@/lib/queries";
import type { TeamStatus } from "@/lib/types";

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

export default function TeamsPage() {
  const teamsQuery = useTeams();
  const teams = teamsQuery.data ?? [];

  return (
    <div className="flex w-full flex-col gap-6 p-6">
      <div>
        <h1 className="text-2xl font-semibold text-neutral-primary">Teams</h1>
        <p className="mt-1 text-sm text-neutral-secondary">
          Browse team health and membership.
        </p>
      </div>

      {teamsQuery.isPending ? (
        <SkeletonCard lines={5} />
      ) : teamsQuery.isError ? (
        <ErrorState
          error={teamsQuery.error}
          onRetry={() => teamsQuery.refetch()}
        />
      ) : teams.length === 0 ? (
        <EmptyState
          title="No teams yet"
          description="Point the collector at a repo and run a refresh."
        />
      ) : (
        <Card className="overflow-x-auto">
          <table className="w-full min-w-[640px] text-left text-sm">
            <thead>
              <tr className="border-b border-neutral-light text-xs text-neutral-tertiary">
                <th scope="col" className="px-4 py-3 font-medium">
                  Team
                </th>
                <th scope="col" className="px-4 py-3 font-medium">
                  Status
                </th>
                <th scope="col" className="px-4 py-3 font-medium">
                  Health
                </th>
                <th scope="col" className="px-4 py-3 font-medium">
                  Engineers
                </th>
                <th scope="col" className="px-4 py-3 font-medium">
                  Top ownership risk
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-light">
              {teams.map((team) => {
                const topRisk = team.busFactorAreas[0];
                return (
                  <tr key={team.id} className="hover:bg-neutral-lighter-alt">
                    <td className="px-4 py-3">
                      <Link
                        href={`/teams/${team.id}`}
                        className="font-medium text-neutral-primary hover:text-brand"
                      >
                        {team.name}
                      </Link>
                      <p className="text-xs text-neutral-tertiary">
                        {team.source}
                      </p>
                    </td>
                    <td className="px-4 py-3">
                      <Badge variant={STATUS_BADGE_VARIANT[team.status]}>
                        {STATUS_LABEL[team.status]}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-neutral-primary">
                      {team.healthScore}/100
                    </td>
                    <td className="px-4 py-3 text-neutral-secondary">
                      {team.engineerCount}
                    </td>
                    <td className="px-4 py-3 text-neutral-secondary">
                      {topRisk
                        ? `${topRisk.topOwner} · ${topRisk.ownershipPercent}%`
                        : "—"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}
