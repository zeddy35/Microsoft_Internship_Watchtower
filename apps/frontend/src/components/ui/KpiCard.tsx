// Fluent KPI card: icon+label header, large metric value, and a trend pill with an up/down arrow.
// Usage: <KpiCard icon={IconGitCommit} label="Commit activity" value="38/wk" direction="down" deltaLabel="Down 60%" trend="bad" />
import { IconArrowDown, IconArrowUp, IconMinus } from "@tabler/icons-react";
import type { ComponentType } from "react";
import { Badge, type BadgeVariant } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { cn } from "@/lib/cn";

type IconComponent = ComponentType<{ className?: string; stroke?: number }>;
type TrendDirection = "up" | "down" | "flat";
type TrendTone = "good" | "caution" | "bad";

export interface KpiCardProps {
  icon: IconComponent;
  label: string;
  value: string;
  direction: TrendDirection;
  deltaLabel: string;
  trend: TrendTone;
  className?: string;
}

const TREND_BADGE_VARIANT: Record<TrendTone, BadgeVariant> = {
  good: "success",
  caution: "warning",
  bad: "error",
};

const DIRECTION_ICON: Record<TrendDirection, IconComponent> = {
  up: IconArrowUp,
  down: IconArrowDown,
  flat: IconMinus,
};

export function KpiCard({
  icon: Icon,
  label,
  value,
  direction,
  deltaLabel,
  trend,
  className,
}: KpiCardProps) {
  const DirectionIcon = DIRECTION_ICON[direction];

  return (
    <Card className={cn("p-4", className)}>
      <div className="flex items-center gap-1.5 text-neutral-secondary">
        <Icon className="size-4" stroke={1.75} aria-hidden="true" />
        <span className="text-xs font-medium">{label}</span>
      </div>
      <p className="mt-2 text-2xl font-semibold text-neutral-primary">
        {value}
      </p>
      <Badge variant={TREND_BADGE_VARIANT[trend]} className="mt-2">
        <DirectionIcon className="size-3" stroke={2.25} aria-hidden="true" />
        {deltaLabel}
      </Badge>
    </Card>
  );
}
