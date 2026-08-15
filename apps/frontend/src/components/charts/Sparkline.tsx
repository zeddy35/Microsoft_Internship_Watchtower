"use client";

import {
  CategoryScale,
  Chart as ChartJS,
  Filler,
  LinearScale,
  LineController,
  LineElement,
  PointElement,
  type ChartData,
  type ChartOptions,
} from "chart.js";
import { Line } from "react-chartjs-2";
import { cn } from "@/lib/cn";
import type { TeamStatus } from "@/lib/types";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  LineController,
  Filler,
);

// Canvas can't read Tailwind classes, so these mirror the state tokens in
// tailwind.config.ts as literal colors.
const STATUS_LINE_COLOR: Record<TeamStatus, string> = {
  healthy: "#107c10",
  "at-risk": "#ffb900",
  critical: "#d13438",
};

const STATUS_FILL_COLOR: Record<TeamStatus, string> = {
  healthy: "rgba(16, 124, 16, 0.12)",
  "at-risk": "rgba(255, 185, 0, 0.16)",
  critical: "rgba(209, 52, 56, 0.12)",
};

export interface SparklineProps {
  /** Oldest value first. */
  data: number[];
  status: TeamStatus;
  className?: string;
}

/** Trend shape only: no axes, no legend, no tooltip, colored by team status. */
export function Sparkline({ data, status, className }: SparklineProps) {
  const chartData: ChartData<"line"> = {
    labels: data.map((_, index) => String(index)),
    datasets: [
      {
        data,
        borderColor: STATUS_LINE_COLOR[status],
        backgroundColor: STATUS_FILL_COLOR[status],
        borderWidth: 1.75,
        pointRadius: 0,
        pointHoverRadius: 0,
        fill: "origin",
        tension: 0.35,
        cubicInterpolationMode: "monotone",
      },
    ],
  };

  const options: ChartOptions<"line"> = {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    events: [],
    plugins: { legend: { display: false }, tooltip: { enabled: false } },
    scales: {
      x: { display: false },
      // Anchoring at zero keeps "the team went quiet" visually honest: without
      // it, a drop from 9 to 7 looks identical to a drop from 9 to 0.
      y: { display: false, min: 0 },
    },
  };

  return (
    <div className={cn("h-10 w-full", className)} aria-hidden="true">
      <Line data={chartData} options={options} />
    </div>
  );
}
