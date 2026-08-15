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
import { useThemeColors } from "@/lib/theme";
import type { TeamStatus } from "@/lib/types";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  LineController,
  Filler,
);

// Canvas cannot read Tailwind classes, so the sparkline reads the same CSS
// variables as the rest of the UI and follows the theme with it.
const STATUS_TOKEN: Record<TeamStatus, string> = {
  healthy: "--state-success",
  "at-risk": "--state-warning",
  critical: "--state-error",
};

export interface SparklineProps {
  /** Oldest value first. */
  data: number[];
  status: TeamStatus;
  className?: string;
}

/** Trend shape only: no axes, no legend, no tooltip, colored by team status. */
export function Sparkline({ data, status, className }: SparklineProps) {
  const color = useThemeColors();
  const token = STATUS_TOKEN[status];

  const chartData: ChartData<"line"> = {
    labels: data.map((_, index) => String(index)),
    datasets: [
      {
        data,
        borderColor: color(token),
        backgroundColor: color(token, 0.14),
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
