// Overview card for one team: status pill, health score, activity sparkline, 3-up stats.
// Usage: <TeamHealthCard team={team} />
import Link from "next/link";
import { Sparkline } from "@/components/charts/Sparkline";
import { Badge, type BadgeVariant } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { cn } from "@/lib/cn";
import type { Team, TeamStatus } from "@/lib/types";

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

const SCORE_TEXT_CLASSES: Record<TeamStatus, string> = {
  healthy: "text-state-success",
  "at-risk": "text-state-warning-fg",
  critical: "text-state-error-fg",
};

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0">
      <p className="truncate text-xs text-neutral-tertiary">{label}</p>
      <p className="mt-0.5 truncate text-sm font-medium text-neutral-primary">
        {value}
      </p>
    </div>
  );
}

export function TeamHealthCard({
  team,
  className,
}: {
  team: Team;
  className?: string;
}) {
  const topRisk = team.busFactorAreas[0];
  const commitsInWindow = team.activity.reduce((sum, day) => sum + day, 0);

  return (
    <Card
      className={cn(
        "p-4 transition-shadow hover:shadow-fluent sm:p-5",
        className,
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <Link
            href={`/teams/${team.id}`}
            className="truncate text-sm font-semibold text-neutral-primary hover:text-brand"
          >
            {team.name}
          </Link>
          <p className="mt-0.5 truncate text-xs text-neutral-tertiary">
            {team.source}
          </p>
        </div>
        <Badge variant={STATUS_BADGE_VARIANT[team.status]}>
          {STATUS_LABEL[team.status]}
        </Badge>
      </div>

      <p className="mt-3 flex items-baseline gap-1">
        <span
          className={cn(
            "text-3xl font-semibold",
            SCORE_TEXT_CLASSES[team.status],
          )}
        >
          {team.healthScore}
        </span>
        <span className="text-sm text-neutral-tertiary">/100</span>
      </p>

      <Sparkline data={team.activity} status={team.status} className="mt-3" />

      <div className="mt-4 grid grid-cols-3 gap-3 border-t border-neutral-light pt-3">
        <Stat label="Engineers" value={String(team.engineerCount)} />
        <Stat label="Commits · 14d" value={String(Math.round(commitsInWindow))} />
        <Stat
          label="Top owner"
          value={topRisk ? `${topRisk.ownershipPercent}%` : "—"}
        />
      </div>
    </Card>
  );
}
