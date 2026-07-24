import { Icon } from "@/components/ui/Icon";
import { StatusPill } from "@/components/ui/StatusPill";
import type { TeamStatus } from "@/lib/types";

export interface TeamHeaderProps {
  name: string;
  status: TeamStatus;
  engineerCount: number;
  source: string;
  healthScore: number;
}

export function TeamHeader({
  name,
  status,
  engineerCount,
  source,
  healthScore,
}: TeamHeaderProps) {
  return (
    <section className="flex items-end justify-between">
      <div>
        <div className="mb-1 flex items-center gap-3">
          <h1 className="font-headline-md text-headline-md font-semibold">{name}</h1>
          <StatusPill status={status} size="md" />
        </div>
        <p className="text-body-md text-secondary">
          {engineerCount} engineers · {source} · health score{" "}
          <span className="font-bold text-tertiary">{healthScore}/100</span>
        </p>
      </div>

      <div className="flex gap-3">
        <button
          type="button"
          className="flex items-center gap-2 rounded border border-outline-variant bg-white px-4 py-1.5 text-body-sm font-semibold transition-all hover:bg-surface-container-low"
        >
          Last 30 days
          <Icon name="expand_more" />
        </button>
        <button
          type="button"
          className="flex items-center justify-center rounded border border-outline-variant bg-white px-3 py-1.5 transition-all hover:bg-surface-container-low"
          aria-label="Tune"
        >
          <Icon name="tune" />
        </button>
      </div>
    </section>
  );
}
