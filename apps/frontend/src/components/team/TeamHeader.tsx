// Team drill-down header: team name, status pill, subline, and Last 30 days / Export digest actions.
import { IconChevronDown, IconDownload } from "@tabler/icons-react";
import { Badge, type BadgeVariant } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import type { TeamStatus } from "@/lib/types";

export interface TeamHeaderProps {
  name: string;
  status: TeamStatus;
  engineerCount: number;
  source: string;
  healthScore: number;
}

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

export function TeamHeader({
  name,
  status,
  engineerCount,
  source,
  healthScore,
}: TeamHeaderProps) {
  return (
    <div className="flex flex-wrap items-start justify-between gap-4">
      <div>
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-semibold text-neutral-primary">
            {name}
          </h1>
          <Badge variant={STATUS_BADGE_VARIANT[status]}>
            {STATUS_LABEL[status]}
          </Badge>
        </div>
        <p className="mt-1 text-sm text-neutral-secondary">
          {engineerCount} engineers · {source} · health score {healthScore}
          /100
        </p>
      </div>

      <div className="flex items-center gap-2">
        <Button variant="secondary">
          Last 30 days
          <IconChevronDown
            className="size-4"
            stroke={1.75}
            aria-hidden="true"
          />
        </Button>
        <Button variant="primary">
          <IconDownload className="size-4" stroke={1.75} aria-hidden="true" />
          Export digest
        </Button>
      </div>
    </div>
  );
}
