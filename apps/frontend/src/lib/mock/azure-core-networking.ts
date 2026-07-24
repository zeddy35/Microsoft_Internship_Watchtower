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
    id: "elena-petrova",
    name: "Elena Petrova",
    role: "Principal Software Engineer",
    initials: "EP",
    commitsPerWeek: 3,
    avgReviewTimeDays: 6.5,
    onGoalRate: 55,
    activityStatus: "active",
  },
  {
    id: "raj-malhotra",
    name: "Raj Malhotra",
    role: "Senior Software Engineer",
    initials: "RM",
    commitsPerWeek: 5,
    avgReviewTimeDays: 3.8,
    onGoalRate: 68,
    activityStatus: "active",
  },
  {
    id: "wei-chen",
    name: "Wei Chen",
    role: "Senior Software Engineer",
    initials: "WC",
    commitsPerWeek: 4,
    avgReviewTimeDays: 5.1,
    onGoalRate: 60,
    activityStatus: "active",
  },
  {
    id: "priya-nair",
    name: "Priya Nair",
    role: "Software Engineer II",
    initials: "PN",
    commitsPerWeek: 4,
    avgReviewTimeDays: 3.2,
    onGoalRate: 74,
    activityStatus: "active",
  },
  {
    id: "marcus-johnson",
    name: "Marcus Johnson",
    role: "Software Engineer II",
    initials: "MJ",
    commitsPerWeek: 3,
    avgReviewTimeDays: 4.0,
    onGoalRate: 62,
    activityStatus: "active",
  },
  {
    id: "sofia-ramirez",
    name: "Sofia Ramirez",
    role: "Senior Software Engineer",
    initials: "SR",
    commitsPerWeek: 5,
    avgReviewTimeDays: 2.9,
    onGoalRate: 81,
    activityStatus: "active",
  },
  {
    id: "daniel-kim",
    name: "Daniel Kim",
    role: "Software Engineer",
    initials: "DK",
    commitsPerWeek: 2,
    avgReviewTimeDays: 4.6,
    onGoalRate: 58,
    activityStatus: "away",
  },
  {
    id: "aisha-bello",
    name: "Aisha Bello",
    role: "Software Engineer II",
    initials: "AB",
    commitsPerWeek: 4,
    avgReviewTimeDays: 3.5,
    onGoalRate: 70,
    activityStatus: "active",
  },
  {
    id: "tom-whitfield",
    name: "Tom Whitfield",
    role: "Engineering Manager",
    initials: "TW",
    commitsPerWeek: 1,
    avgReviewTimeDays: 5.8,
    onGoalRate: 50,
    activityStatus: "active",
  },
  {
    id: "noah-andersen",
    name: "Noah Andersen",
    role: "Software Engineer",
    initials: "NA",
    commitsPerWeek: 2,
    avgReviewTimeDays: 4.9,
    onGoalRate: 55,
    activityStatus: "offline",
  },
  {
    id: "yuki-tanaka",
    name: "Yuki Tanaka",
    role: "Senior Software Engineer",
    initials: "YT",
    commitsPerWeek: 3,
    avgReviewTimeDays: 3.1,
    onGoalRate: 77,
    activityStatus: "active",
  },
  {
    id: "grace-osullivan",
    name: "Grace O'Sullivan",
    role: "Software Engineer II",
    initials: "GO",
    commitsPerWeek: 2,
    avgReviewTimeDays: 4.4,
    onGoalRate: 63,
    activityStatus: "active",
  },
]);

const busFactorAreas = z.array(BusFactorAreaSchema).parse([
  {
    id: "bgp-peering-configuration",
    area: "BGP peering configuration",
    topOwner: "Elena Petrova",
    ownershipPercent: 82,
    riskLevel: "high",
  },
  {
    id: "load-balancer-control-plane",
    area: "Load balancer control plane",
    topOwner: "Raj Malhotra",
    ownershipPercent: 61,
    riskLevel: "medium",
  },
  {
    id: "network-telemetry-pipeline",
    area: "Network telemetry pipeline",
    topOwner: "Wei Chen",
    ownershipPercent: 34,
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
    baseline: 76,
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
    id: "azure-core-networking-review-time-spike",
    teamId: TEAM_ID,
    severity: "critical",
    title: "PR review time has nearly quadrupled",
    description:
      "Average time to review is up 280% over the last 30 days, from 1.1 days to 4.2 days, with most of the backlog sitting on two reviewers.",
    detectedAt: "2026-07-22T14:32:00Z",
  },
  {
    id: "azure-core-networking-commit-activity-drop",
    teamId: TEAM_ID,
    severity: "warning",
    title: "Commit activity down sharply this month",
    description:
      "Weekly commit activity fell 60%, from roughly 95/wk to 38/wk, with no corresponding drop in open work items.",
    detectedAt: "2026-07-20T09:10:00Z",
  },
  {
    id: "azure-core-networking-bus-factor-bgp",
    teamId: TEAM_ID,
    severity: "warning",
    title: "Single-owner risk on BGP peering configuration",
    description:
      "Elena Petrova authored 82% of recent changes to the BGP peering configuration, leaving limited coverage if she is unavailable.",
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
    "Azure Core Networking's commit and push cadence has fallen sharply over the past month while PR review times have nearly quadrupled, pointing to a reviewer bottleneck rather than a drop in workload. Ownership of the BGP peering configuration remains concentrated in a single engineer, adding delivery risk if they're unavailable. Rebalancing review load and spreading ownership would likely help the team's on-goal commit rate recover toward its prior level.",
  suggestions: [
    "Rebalance PR review load across the team",
    "Pair Elena Petrova with a backup owner on BGP peering",
    "Investigate the drop in push frequency since early July",
  ],
  generatedAt: "2026-07-23T08:15:00Z",
});
