import { z } from "zod";
import { TeamHealthCardSchema, type TeamHealthCard } from "@/lib/types";

export const teamHealthCards: TeamHealthCard[] = z.array(TeamHealthCardSchema).parse([
  {
    id: "azure-core-networking",
    name: "Azure Core Networking",
    icon: "hub",
    status: "critical",
    healthScore: 47,
    sparkline: [72, 68, 64, 60, 58, 55, 52, 50, 48, 47],
    openPrs: 42,
    avgReviewTimeDays: 3.1,
    anomalyCount: 12,
  },
  {
    id: "storage-compute",
    name: "Storage & Compute",
    icon: "database",
    status: "at-risk",
    healthScore: 62,
    sparkline: [70, 69, 71, 68, 66, 65, 63, 64, 62, 62],
    openPrs: 28,
    avgReviewTimeDays: 1.8,
    anomalyCount: 5,
  },
  {
    id: "identity-service",
    name: "Identity Service",
    icon: "fingerprint",
    status: "healthy",
    healthScore: 94,
    sparkline: [88, 89, 90, 91, 92, 93, 93, 94, 94, 94],
    openPrs: 12,
    avgReviewTimeDays: 0.6,
    anomalyCount: 0,
  },
  {
    id: "security",
    name: "Security",
    icon: "verified_user",
    status: "healthy",
    healthScore: 88,
    sparkline: [85, 84, 86, 85, 87, 86, 88, 87, 88, 88],
    openPrs: 15,
    avgReviewTimeDays: 1.2,
    anomalyCount: 1,
  },
]);

export interface TrendBar {
  heightPercent: number;
  colorClassName: string;
}

export const historicalHealthTrend: TrendBar[] = [
  { heightPercent: 40, colorClassName: "bg-secondary-container" },
  { heightPercent: 45, colorClassName: "bg-secondary-container" },
  { heightPercent: 30, colorClassName: "bg-secondary-container" },
  { heightPercent: 55, colorClassName: "bg-primary-container" },
  { heightPercent: 65, colorClassName: "bg-primary-container" },
  { heightPercent: 60, colorClassName: "bg-primary-container" },
  { heightPercent: 25, colorClassName: "bg-error/40" },
  { heightPercent: 20, colorClassName: "bg-error/60" },
  { heightPercent: 35, colorClassName: "bg-tertiary-container/50" },
  { heightPercent: 75, colorClassName: "bg-primary-container" },
];

export const globalHealthAveragePercent = 75;
export const globalHealthTeamCount = 24;

export interface CriticalAnomalyRow {
  id: string;
  team: string;
  issue: string;
  duration: string;
  status: "Active" | "Warning";
}

export const criticalAnomalyRows: CriticalAnomalyRow[] = [
  {
    id: "core-networking-gateway-timeouts",
    team: "Core Networking",
    issue: "504 Gateway Timeouts in West Europe",
    duration: "2h 14m",
    status: "Active",
  },
  {
    id: "storage-cluster-latency-spike",
    team: "Storage Cluster",
    issue: "P99 Latency Spike > 450ms",
    duration: "45m",
    status: "Warning",
  },
];
