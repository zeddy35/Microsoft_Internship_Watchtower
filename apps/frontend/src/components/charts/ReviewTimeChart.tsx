"use client";

import {
  CategoryScale,
  Chart as ChartJS,
  Filler,
  LinearScale,
  LineController,
  LineElement,
  PointElement,
  Tooltip,
  type ChartData,
  type ChartOptions,
} from "chart.js";
import { Line } from "react-chartjs-2";
import { cn } from "@/lib/cn";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  LineController,
  Filler,
  Tooltip,
);

// Canvas rendering can't consume Tailwind classes, so these mirror the
// brand / state / neutral tokens in tailwind.config.ts as literal colors.
const LINE_COLOR = "#0078d4";
const LINE_FILL_COLOR = "rgba(0, 120, 212, 0.12)";
const ANOMALY_COLOR = "#d13438";
const BASELINE_COLOR = "#a19f9d";
const AXIS_TEXT_COLOR = "#605e5c";
const GRID_COLOR = "#edebe9";

export interface ReviewTimeDataPoint {
  /** ISO date string, e.g. "2026-06-24" */
  date: string;
  reviewTimeDays: number;
  baselineDays: number;
}

export interface ReviewTimeChartProps {
  data: ReviewTimeDataPoint[];
  className?: string;
}

function formatDateLabel(date: string) {
  return new Date(date).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
}

function formatDays(value: number | string | null) {
  const numeric = typeof value === "number" ? value : Number(value ?? 0);
  return `${numeric}d`;
}

export function ReviewTimeChart({ data, className }: ReviewTimeChartProps) {
  const lastIndex = data.length - 1;

  const pointRadius = data.map((_, index) => (index === lastIndex ? 6 : 0));
  const pointHoverRadius = data.map((_, index) =>
    index === lastIndex ? 8 : 4,
  );
  const pointColor = data.map((_, index) =>
    index === lastIndex ? ANOMALY_COLOR : LINE_COLOR,
  );

  const chartData: ChartData<"line"> = {
    labels: data.map((point) => formatDateLabel(point.date)),
    datasets: [
      {
        label: "Baseline",
        data: data.map((point) => point.baselineDays),
        borderColor: BASELINE_COLOR,
        borderDash: [6, 4],
        borderWidth: 1.5,
        pointRadius: 0,
        pointHoverRadius: 0,
        fill: false,
        tension: 0,
      },
      {
        label: "PR review time",
        data: data.map((point) => point.reviewTimeDays),
        borderColor: LINE_COLOR,
        backgroundColor: LINE_FILL_COLOR,
        borderWidth: 2,
        pointRadius,
        pointHoverRadius,
        pointBackgroundColor: pointColor,
        pointBorderColor: pointColor,
        pointBorderWidth: 0,
        fill: "origin",
        tension: 0.35,
        cubicInterpolationMode: "monotone",
      },
    ],
  };

  const options: ChartOptions<"line"> = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: "index", intersect: false },
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: (context) =>
            `${context.dataset.label}: ${formatDays(context.parsed.y)}`,
        },
      },
    },
    scales: {
      x: {
        grid: { display: false },
        border: { display: false },
        ticks: { color: AXIS_TEXT_COLOR, maxTicksLimit: 6 },
      },
      y: {
        min: 0,
        grid: { color: GRID_COLOR },
        border: { display: false },
        ticks: {
          color: AXIS_TEXT_COLOR,
          callback: formatDays,
        },
      },
    },
  };

  return (
    <div className={cn("h-64 w-full", className)}>
      <Line data={chartData} options={options} />
    </div>
  );
}
