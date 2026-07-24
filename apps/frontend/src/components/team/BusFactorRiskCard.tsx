// "Bus-factor risk" card: code areas with an ownership percentage, a colored progress bar, and a risk label.
import { Badge, type BadgeVariant } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { cn } from "@/lib/cn";
import type { BusFactorArea, RiskLevel } from "@/lib/types";

export interface BusFactorRiskCardProps {
  areas: BusFactorArea[];
  className?: string;
}

const RISK_BADGE_VARIANT: Record<RiskLevel, BadgeVariant> = {
  low: "success",
  medium: "warning",
  high: "error",
};

const RISK_LABEL: Record<RiskLevel, string> = {
  low: "Low risk",
  medium: "Medium risk",
  high: "High risk",
};

const RISK_BAR_CLASSES: Record<RiskLevel, string> = {
  low: "bg-state-success",
  medium: "bg-state-warning",
  high: "bg-state-error",
};

export function BusFactorRiskCard({
  areas,
  className,
}: BusFactorRiskCardProps) {
  return (
    <Card className={cn("p-4 sm:p-5", className)}>
      <h2 className="text-sm font-semibold text-neutral-primary">
        Bus-factor risk
      </h2>
      <ul className="mt-4 flex flex-col gap-4">
        {areas.map((area) => (
          <li key={area.id}>
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-sm font-medium text-neutral-primary">
                  {area.area}
                </p>
                <p className="text-xs text-neutral-tertiary">
                  {area.topOwner} owns {area.ownershipPercent}%
                </p>
              </div>
              <Badge variant={RISK_BADGE_VARIANT[area.riskLevel]}>
                {RISK_LABEL[area.riskLevel]}
              </Badge>
            </div>
            <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-neutral-lighter">
              <div
                className={cn(
                  "h-full rounded-full",
                  RISK_BAR_CLASSES[area.riskLevel],
                )}
                style={{ width: `${area.ownershipPercent}%` }}
              />
            </div>
          </li>
        ))}
      </ul>
    </Card>
  );
}
