"use client";

import {
  CategoryScale,
  Chart as ChartJS,
  Filler,
  LinearScale,
  LineElement,
  PointElement,
} from "chart.js";
import { Line } from "react-chartjs-2";
import type { TeamStatus } from "@/lib/types";

ChartJS.register(CategoryScale, LinearScale, LineElement, PointElement, Filler);

const STATUS_COLOR: Record<TeamStatus, string> = {
  critical: "#ba1a1a",
  "at-risk": "#bc5b00",
  healthy: "#0078d4",
};

type SparklineProps = {
  data: number[];
  status: TeamStatus;
  className?: string;
};

export function Sparkline({ data, status, className }: SparklineProps) {
  const color = STATUS_COLOR[status];

  return (
    <div className={className} style={{ height: 40 }}>
      <Line
        data={{
          labels: data.map((_, index) => index),
          datasets: [
            {
              data,
              borderColor: color,
              borderWidth: 1.5,
              pointRadius: 0,
              tension: 0.35,
              fill: false,
            },
          ],
        }}
        options={{
          responsive: true,
          maintainAspectRatio: false,
          animation: false,
          scales: {
            x: { display: false },
            y: { display: false },
          },
          plugins: {
            legend: { display: false },
            tooltip: { enabled: false },
          },
        }}
      />
    </div>
  );
}
