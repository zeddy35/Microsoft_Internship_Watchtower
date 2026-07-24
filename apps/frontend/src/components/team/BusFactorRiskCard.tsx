import { SectionCard } from "@/components/ui/SectionCard";
import { Icon } from "@/components/ui/Icon";
import { cn } from "@/lib/cn";
import type { BusFactorArea, RiskLevel } from "@/lib/types";

export interface BusFactorRiskCardProps {
  areas: BusFactorArea[];
  className?: string;
}

const RISK_LABEL: Record<RiskLevel, string> = {
  low: "Low risk",
  medium: "Medium risk",
  high: "High risk",
};

const RISK_TEXT_CLASSES: Record<RiskLevel, string> = {
  low: "text-emerald-600",
  medium: "text-tertiary",
  high: "text-error",
};

const RISK_BAR_CLASSES: Record<RiskLevel, string> = {
  low: "bg-emerald-500",
  medium: "bg-tertiary",
  high: "bg-error",
};

export function BusFactorRiskCard({ areas, className }: BusFactorRiskCardProps) {
  return (
    <SectionCard
      title="Bus-factor Risk"
      action={<Icon name="info" className="text-outline" />}
      className={className}
    >
      <div className="space-y-5">
        {areas.map((area) => (
          <div key={area.id}>
            <div className="mb-2 flex justify-between">
              <span className="text-body-sm font-semibold">{area.area}</span>
              <span className={cn("text-body-sm", RISK_TEXT_CLASSES[area.riskLevel])}>
                {RISK_LABEL[area.riskLevel]}
              </span>
            </div>
            <div className="h-2 w-full rounded-full bg-surface-container">
              <div
                className={cn("h-2 rounded-full", RISK_BAR_CLASSES[area.riskLevel])}
                style={{ width: `${area.coveragePercent}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </SectionCard>
  );
}
