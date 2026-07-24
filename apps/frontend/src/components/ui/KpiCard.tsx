import { Icon } from "@/components/ui/Icon";
import { cn } from "@/lib/cn";

export type KpiTrend = "good" | "caution" | "bad";
export type KpiDirection = "up" | "down" | "flat";

const TREND_STYLES: Record<KpiTrend, string> = {
  bad: "bg-error-container text-on-error-container",
  caution: "bg-tertiary-fixed text-on-tertiary-fixed-variant",
  good: "bg-green-100 text-green-800",
};

const DIRECTION_ICON: Record<KpiDirection, string | null> = {
  up: "arrow_upward",
  down: "arrow_downward",
  flat: null,
};

type KpiCardProps = {
  label: string;
  value: string;
  trend: KpiTrend;
  direction?: KpiDirection;
  trendLabel: string;
  className?: string;
};

export function KpiCard({
  label,
  value,
  trend,
  direction = "flat",
  trendLabel,
  className,
}: KpiCardProps) {
  const icon = DIRECTION_ICON[direction];

  return (
    <div
      className={cn(
        "group rounded border border-outline-variant bg-surface-container-lowest p-5 transition-colors hover:border-primary",
        className,
      )}
    >
      <p className="mb-1 text-body-sm text-secondary">{label}</p>
      <div className="flex items-end justify-between">
        <span className="font-display-lg text-display-lg">{value}</span>
        <span
          className={cn(
            "flex items-center gap-0.5 rounded px-2 py-0.5 text-xs font-bold",
            TREND_STYLES[trend],
          )}
        >
          {icon && <Icon name={icon} size={14} />}
          {trendLabel}
        </span>
      </div>
    </div>
  );
}
