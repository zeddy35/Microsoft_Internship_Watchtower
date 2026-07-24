import { Sparkline } from "@/components/charts/Sparkline";
import { FluentCard } from "@/components/ui/FluentCard";
import { Icon } from "@/components/ui/Icon";
import { StatusPill } from "@/components/ui/StatusPill";
import {
  criticalAnomalyRows,
  globalHealthAveragePercent,
  globalHealthTeamCount,
  historicalHealthTrend,
  teamHealthCards,
} from "@/lib/mock/teams";
import type { TeamStatus } from "@/lib/types";

const STATUS_ICON_BOX: Record<TeamStatus, string> = {
  critical: "bg-error-container/20 text-error",
  "at-risk": "bg-tertiary-fixed/20 text-tertiary",
  healthy: "bg-primary-fixed/20 text-primary",
};

const STATUS_HOVER_BORDER: Record<TeamStatus, string> = {
  critical: "hover:border-error/30",
  "at-risk": "hover:border-tertiary/30",
  healthy: "hover:border-primary/30",
};

const STATUS_ANOMALY_TEXT: Record<TeamStatus, string> = {
  critical: "text-error font-bold",
  "at-risk": "text-tertiary font-bold",
  healthy: "text-on-surface",
};

const STATUS_PRIORITY: Record<TeamStatus, number> = {
  critical: 0,
  "at-risk": 1,
  healthy: 2,
};

const ANOMALY_STATUS_STYLES: Record<"Active" | "Warning", string> = {
  Active: "bg-error-container text-on-error-container",
  Warning: "bg-tertiary-fixed text-on-tertiary-fixed-variant",
};

const DONUT_RADIUS = 58;
const DONUT_CIRCUMFERENCE = 2 * Math.PI * DONUT_RADIUS;

export default function TeamsOverviewPage() {
  const sortedCards = [...teamHealthCards].sort(
    (a, b) => STATUS_PRIORITY[a.status] - STATUS_PRIORITY[b.status],
  );
  const donutOffset =
    DONUT_CIRCUMFERENCE * (1 - globalHealthAveragePercent / 100);

  return (
    <div className="mx-auto max-w-[1400px] p-margin_page">
      <div className="mb-8 flex items-end justify-between">
        <div>
          <h2 className="font-headline-lg text-headline-lg font-semibold text-on-surface">
            Team health
          </h2>
          <p className="mt-1 text-secondary">
            Operational performance and stability metrics across organizational
            clusters.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 rounded-lg border border-outline-variant bg-surface-container-low px-3 py-1.5">
            <Icon name="calendar_today" size={20} className="text-secondary" />
            <span className="text-body-md font-medium">Last 30 days</span>
            <Icon name="expand_more" size={18} className="text-secondary" />
          </div>
          <button
            type="button"
            className="rounded-lg border border-outline-variant p-1.5 text-secondary hover:bg-surface-container-high"
            aria-label="Filter"
          >
            <Icon name="filter_list" size={20} />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-gutter md:grid-cols-2 xl:grid-cols-4">
        {sortedCards.map((card) => (
          <FluentCard
            key={card.id}
            className={`flex h-full flex-col p-card_padding transition-all ${STATUS_HOVER_BORDER[card.status]}`}
          >
            <div className="mb-4 flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div
                  className={`flex size-10 items-center justify-center rounded-lg ${STATUS_ICON_BOX[card.status]}`}
                >
                  <Icon name={card.icon} size={24} />
                </div>
                <h3 className="font-headline-sm text-headline-sm">{card.name}</h3>
              </div>
              <StatusPill status={card.status} />
            </div>

            <div className="mb-6 mt-2">
              <div className="flex items-end gap-2">
                <span className="text-4xl font-bold text-on-surface">
                  {card.healthScore}
                </span>
                <span className="pb-1.5 font-medium text-secondary">/ 100</span>
              </div>
              <p className="mt-1 text-body-sm text-secondary">Performance Index</p>
            </div>

            <Sparkline data={card.sparkline} status={card.status} className="mb-6" />

            <div className="mt-auto grid grid-cols-3 gap-2 border-t border-secondary-container pt-4">
              <div className="text-center">
                <p className="text-[10px] font-bold uppercase text-secondary">
                  Open PRs
                </p>
                <p className="mt-1 text-headline-sm">{card.openPrs}</p>
              </div>
              <div className="text-center">
                <p className="text-[10px] font-bold uppercase text-secondary">
                  Avg Review
                </p>
                <p className="mt-1 text-headline-sm">{card.avgReviewTimeDays}d</p>
              </div>
              <div className="text-center">
                <p className="text-[10px] font-bold uppercase text-secondary">
                  Anomalies
                </p>
                <p className={`mt-1 text-headline-sm ${STATUS_ANOMALY_TEXT[card.status]}`}>
                  {card.anomalyCount}
                </p>
              </div>
            </div>
          </FluentCard>
        ))}
      </div>

      <div className="mt-12 grid grid-cols-1 gap-gutter md:grid-cols-3">
        <FluentCard className="p-card_padding md:col-span-2">
          <h3 className="mb-4 font-headline-sm text-headline-sm">
            Historical Health Trend
          </h3>
          <div className="relative h-48 w-full">
            <div className="absolute inset-0 flex items-end justify-between px-2">
              {historicalHealthTrend.map((bar, index) => (
                <div
                  key={index}
                  className={`w-[8%] rounded-t-sm ${bar.colorClassName}`}
                  style={{ height: `${bar.heightPercent}%` }}
                />
              ))}
            </div>
          </div>
          <div className="mt-4 flex justify-between text-[10px] font-bold uppercase text-secondary">
            <span>30 Days Ago</span>
            <span>Today</span>
          </div>
        </FluentCard>

        <FluentCard className="flex flex-col justify-between bg-surface-container-lowest p-card_padding">
          <div>
            <h3 className="mb-1 font-headline-sm text-headline-sm">
              Global Health Avg
            </h3>
            <p className="text-body-sm text-secondary">
              Averaged across {globalHealthTeamCount} teams
            </p>
          </div>
          <div className="my-6 text-center">
            <div className="relative inline-flex items-center justify-center">
              <svg className="size-32 -rotate-90 transform">
                <circle
                  className="text-secondary-container"
                  cx="64"
                  cy="64"
                  r={DONUT_RADIUS}
                  fill="transparent"
                  stroke="currentColor"
                  strokeWidth="12"
                />
                <circle
                  className="text-primary"
                  cx="64"
                  cy="64"
                  r={DONUT_RADIUS}
                  fill="transparent"
                  stroke="currentColor"
                  strokeWidth="12"
                  strokeDasharray={DONUT_CIRCUMFERENCE}
                  strokeDashoffset={donutOffset}
                />
              </svg>
              <span className="absolute text-3xl font-bold text-on-surface">
                {globalHealthAveragePercent}%
              </span>
            </div>
          </div>
          <button
            type="button"
            className="w-full rounded border border-outline-variant bg-surface py-2 text-body-sm font-medium transition-all hover:bg-secondary-container/20"
          >
            View Aggregated Metrics
          </button>
        </FluentCard>
      </div>

      <div className="mt-12">
        <h3 className="mb-4 font-headline-sm text-headline-sm">Critical Anomalies</h3>
        <FluentCard className="overflow-hidden">
          <table className="w-full border-collapse text-left">
            <thead>
              <tr className="border-b border-secondary-container bg-surface-container-low">
                <th className="px-4 py-3 text-[11px] font-bold uppercase tracking-wider text-secondary">
                  Team
                </th>
                <th className="px-4 py-3 text-[11px] font-bold uppercase tracking-wider text-secondary">
                  Issue
                </th>
                <th className="px-4 py-3 text-[11px] font-bold uppercase tracking-wider text-secondary">
                  Duration
                </th>
                <th className="px-4 py-3 text-[11px] font-bold uppercase tracking-wider text-secondary">
                  Status
                </th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-secondary-container">
              {criticalAnomalyRows.map((row) => (
                <tr key={row.id} className="transition-all hover:bg-surface-container-lowest">
                  <td className="px-4 py-4">
                    <span className="font-medium text-on-surface">{row.team}</span>
                  </td>
                  <td className="px-4 py-4 text-body-md">{row.issue}</td>
                  <td className="px-4 py-4 font-code text-body-sm text-secondary">
                    {row.duration}
                  </td>
                  <td className="px-4 py-4">
                    <span
                      className={`rounded px-2 py-0.5 text-[11px] font-semibold ${ANOMALY_STATUS_STYLES[row.status]}`}
                    >
                      {row.status}
                    </span>
                  </td>
                  <td className="px-4 py-4 text-right">
                    <button
                      type="button"
                      className="text-body-sm font-semibold text-primary hover:underline"
                    >
                      Investigate
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </FluentCard>
      </div>
    </div>
  );
}
