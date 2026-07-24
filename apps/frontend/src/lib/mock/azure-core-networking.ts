import { z } from "zod";
import {
  AnomalySchema,
  BusFactorAreaSchema,
  MetricSchema,
  TeamMemberSchema,
  TeamSchema,
  TeamSummarySchema,
  type Anomaly,
  type Metric,
  type Team,
  type TeamSummary,
} from "@/lib/types";

const TEAM_ID = "azure-core-networking";

const teamMembers = z.array(TeamMemberSchema).parse([
  {
    id: "sarah-kim",
    name: "Sarah Kim",
    role: "Principal Software Eng.",
    initials: "SK",
    commitsPerWeek: 12,
    reviewsPerWeek: 24,
    onGoalRate: 92,
    activityStatus: "active",
  },
  {
    id: "rahul-jha",
    name: "Rahul Jha",
    role: "Senior Engineer II",
    initials: "RJ",
    commitsPerWeek: 4,
    reviewsPerWeek: 3,
    onGoalRate: 45,
    activityStatus: "active",
  },
  {
    id: "alice-moreno",
    name: "Alice Moreno",
    role: "Software Engineer II",
    initials: "AM",
    commitsPerWeek: 8,
    reviewsPerWeek: 14,
    onGoalRate: 78,
    activityStatus: "active",
  },
  {
    id: "tim-yang",
    name: "Tim Yang",
    role: "Senior Engineer I",
    initials: "TY",
    commitsPerWeek: 2,
    reviewsPerWeek: 2,
    onGoalRate: 18,
    activityStatus: "away",
  },
  {
    id: "elena-petrova",
    name: "Elena Petrova",
    role: "Principal Software Engineer",
    initials: "EP",
    commitsPerWeek: 3,
    reviewsPerWeek: 5,
    onGoalRate: 55,
    activityStatus: "active",
  },
  {
    id: "wei-chen",
    name: "Wei Chen",
    role: "Senior Software Engineer",
    initials: "WC",
    commitsPerWeek: 4,
    reviewsPerWeek: 6,
    onGoalRate: 60,
    activityStatus: "active",
  },
  {
    id: "priya-nair",
    name: "Priya Nair",
    role: "Software Engineer II",
    initials: "PN",
    commitsPerWeek: 4,
    reviewsPerWeek: 9,
    onGoalRate: 74,
    activityStatus: "active",
  },
  {
    id: "marcus-johnson",
    name: "Marcus Johnson",
    role: "Software Engineer II",
    initials: "MJ",
    commitsPerWeek: 3,
    reviewsPerWeek: 6,
    onGoalRate: 62,
    activityStatus: "active",
  },
  {
    id: "sofia-ramirez",
    name: "Sofia Ramirez",
    role: "Senior Software Engineer",
    initials: "SR",
    commitsPerWeek: 5,
    reviewsPerWeek: 11,
    onGoalRate: 81,
    activityStatus: "active",
  },
  {
    id: "daniel-kim",
    name: "Daniel Kim",
    role: "Software Engineer",
    initials: "DK",
    commitsPerWeek: 2,
    reviewsPerWeek: 4,
    onGoalRate: 58,
    activityStatus: "away",
  },
  {
    id: "aisha-bello",
    name: "Aisha Bello",
    role: "Software Engineer II",
    initials: "AB",
    commitsPerWeek: 4,
    reviewsPerWeek: 8,
    onGoalRate: 70,
    activityStatus: "active",
  },
  {
    id: "tom-whitfield",
    name: "Tom Whitfield",
    role: "Engineering Manager",
    initials: "TW",
    commitsPerWeek: 1,
    reviewsPerWeek: 15,
    onGoalRate: 50,
    activityStatus: "active",
  },
]);

const busFactorAreas = z.array(BusFactorAreaSchema).parse([
  {
    id: "data-plane",
    area: "Data plane",
    topOwner: "Elena Petrova",
    coveragePercent: 45,
    riskLevel: "medium",
  },
  {
    id: "control-plane",
    area: "Control plane",
    topOwner: "Wei Chen",
    coveragePercent: 12,
    riskLevel: "high",
  },
  {
    id: "sdk",
    area: "SDK",
    topOwner: "Priya Nair",
    coveragePercent: 85,
    riskLevel: "low",
  },
]);

export const team: Team = TeamSchema.parse({
  id: TEAM_ID,
  name: "Azure Core Networking",
  status: "at-risk",
  healthScore: 47,
  engineerCount: teamMembers.length,
  source: "GitHub",
  members: teamMembers,
  busFactorAreas,
});

export const metrics: Metric[] = z.array(MetricSchema).parse([
  {
    id: "commit-activity",
    label: "Commit activity",
    unit: "/wk",
    value: 38,
    baseline: 95,
    delta: -60,
    direction: "down",
    trend: "bad",
  },
  {
    id: "push-frequency",
    label: "Push frequency",
    unit: "/wk",
    value: 9,
    baseline: 13.8,
    delta: -35,
    direction: "down",
    trend: "caution",
  },
  {
    id: "pr-review-time",
    label: "PR review time",
    unit: "d",
    value: 4.2,
    baseline: 1.1,
    delta: 280,
    direction: "up",
    trend: "bad",
  },
  {
    id: "on-goal-commits",
    label: "On-goal commits",
    unit: "%",
    value: 64,
    baseline: 80,
    delta: -16,
    direction: "down",
    trend: "caution",
  },
]);

interface ReviewTimeHistoryPoint {
  date: string;
  reviewTimeDays: number;
  baselineDays: number;
}

const reviewTimeMetric = metrics.find(
  (metric) => metric.id === "pr-review-time",
)!;

const REVIEW_TIME_START_DATE = "2026-06-25";

// Deterministic day-to-day wobble so the trend line looks like real data
// instead of a straight ramp, without relying on Math.random() (which would
// differ between server and client render and break hydration).
const REVIEW_TIME_JITTER = [
  0, 0.1, -0.1, 0.1, 0.1, -0.1, 0.1, 0.1, -0.1, 0.1, 0.1, -0.1, 0.1, 0.1, -0.1,
  0.1, 0.1, -0.1, 0.1, 0.1, -0.1, 0.1, 0.1, -0.1, 0.1, 0, 0, 0, 0, 0,
];

export const reviewTimeHistory: ReviewTimeHistoryPoint[] = Array.from(
  { length: 30 },
  (_, index) => {
    const progress = index / 29;
    const trend =
      reviewTimeMetric.baseline +
      progress * (reviewTimeMetric.value - reviewTimeMetric.baseline);
    const reviewTimeDays =
      index === 29
        ? reviewTimeMetric.value
        : Math.max(
            0,
            Math.round((trend + REVIEW_TIME_JITTER[index]) * 10) / 10,
          );

    const date = new Date(REVIEW_TIME_START_DATE);
    date.setUTCDate(date.getUTCDate() + index);

    return {
      date: date.toISOString().slice(0, 10),
      reviewTimeDays,
      baselineDays: reviewTimeMetric.baseline,
    };
  },
);

export const anomalies: Anomaly[] = z.array(AnomalySchema).parse([
  {
    id: "azure-core-networking-critical-pr-latency",
    teamId: TEAM_ID,
    severity: "critical",
    title: "Critical PR latency",
    description:
      "15+ PRs waiting more than 5 days. Average response time increased from 1.2d to 4.2d.",
    detectedAt: "2026-07-23T12:30:00Z",
  },
  {
    id: "azure-core-networking-velocity-drop",
    teamId: TEAM_ID,
    severity: "warning",
    title: "Velocity drop",
    description:
      "40% decrease in merge rate. PR inflow remains constant while merge rate stalls.",
    detectedAt: "2026-07-23T09:30:00Z",
  },
  {
    id: "azure-core-networking-bus-factor-control-plane",
    teamId: TEAM_ID,
    severity: "warning",
    title: "Single-owner risk on the control plane",
    description:
      "Control plane changes have only 12% redundant coverage, with Wei Chen as the sole reviewer able to approve most changes.",
    detectedAt: "2026-07-18T16:45:00Z",
  },
  {
    id: "azure-core-networking-push-frequency-decline",
    teamId: TEAM_ID,
    severity: "info",
    title: "Push frequency trending below team baseline",
    description:
      "Pushes per week have dropped 35% versus the prior period, from 13.8/wk to 9/wk, tracking below the team's usual cadence.",
    detectedAt: "2026-07-14T11:05:00Z",
  },
]);

export const teamSummary: TeamSummary = TeamSummarySchema.parse({
  id: "azure-core-networking-summary-2026-07-23",
  teamId: TEAM_ID,
  model: "Phi-4",
  summary:
    "Team health has declined significantly this month due to a spike in PR review times and a decrease in commit frequency. Focus on unblocking the code review pipeline.",
  suggestions: ["Review bottlenecks", "Team velocity", "Anomaly details"],
  generatedAt: "2026-07-23T08:15:00Z",
});
