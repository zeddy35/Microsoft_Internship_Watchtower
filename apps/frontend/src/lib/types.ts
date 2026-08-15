import { z } from "zod";

// Shared enums -------------------------------------------------------------

export const TeamStatusSchema = z.enum(["healthy", "at-risk", "critical"]);
export type TeamStatus = z.infer<typeof TeamStatusSchema>;

export const MemberActivityStatusSchema = z.enum(["active", "away", "offline"]);
export type MemberActivityStatus = z.infer<typeof MemberActivityStatusSchema>;

export const MetricDirectionSchema = z.enum(["up", "down", "flat"]);
export type MetricDirection = z.infer<typeof MetricDirectionSchema>;

export const MetricTrendSchema = z.enum(["good", "caution", "bad"]);
export type MetricTrend = z.infer<typeof MetricTrendSchema>;

export const RiskLevelSchema = z.enum(["low", "medium", "high"]);
export type RiskLevel = z.infer<typeof RiskLevelSchema>;

export const AnomalySeveritySchema = z.enum(["info", "warning", "critical"]);
export type AnomalySeverity = z.infer<typeof AnomalySeveritySchema>;

// Team member ----------------------------------------------------------

export const TeamMemberSchema = z.object({
  id: z.string(),
  name: z.string(),
  role: z.string(),
  initials: z.string().min(1).max(3),
  commitsPerWeek: z.number().nonnegative(),
  avgReviewTimeDays: z.number().nonnegative(),
  onGoalRate: z.number().min(0).max(100),
  activityStatus: MemberActivityStatusSchema,
});
export type TeamMember = z.infer<typeof TeamMemberSchema>;

// Metric -----------------------------------------------------------------

export const MetricSchema = z.object({
  id: z.string(),
  label: z.string(),
  unit: z.string(),
  value: z.number(),
  baseline: z.number(),
  delta: z.number(),
  direction: MetricDirectionSchema,
  trend: MetricTrendSchema,
});
export type Metric = z.infer<typeof MetricSchema>;

// Bus-factor area ----------------------------------------------------------

export const BusFactorAreaSchema = z.object({
  id: z.string(),
  area: z.string(),
  topOwner: z.string(),
  ownershipPercent: z.number().min(0).max(100),
  riskLevel: RiskLevelSchema,
});
export type BusFactorArea = z.infer<typeof BusFactorAreaSchema>;

// Anomaly ------------------------------------------------------------------

export const AnomalySchema = z.object({
  id: z.string(),
  teamId: z.string(),
  severity: AnomalySeveritySchema,
  title: z.string(),
  description: z.string(),
  detectedAt: z.iso.datetime(),
});
export type Anomaly = z.infer<typeof AnomalySchema>;

// Phi-4 team summary ---------------------------------------------------

export const TeamSummarySchema = z.object({
  id: z.string(),
  teamId: z.string(),
  model: z.literal("Phi-4"),
  summary: z.string(),
  suggestions: z.array(z.string()).min(1),
  generatedAt: z.iso.datetime(),
});
export type TeamSummary = z.infer<typeof TeamSummarySchema>;

// Review-time trend point --------------------------------------------------

export const ReviewTimePointSchema = z.object({
  date: z.string(),
  reviewTimeDays: z.number(),
  baselineDays: z.number(),
});
export type ReviewTimePoint = z.infer<typeof ReviewTimePointSchema>;

// Drill-down metrics payload -----------------------------------------------

export const TeamMetricsSchema = z.object({
  metrics: z.array(MetricSchema),
  reviewTimeHistory: z.array(ReviewTimePointSchema),
});
export type TeamMetrics = z.infer<typeof TeamMetricsSchema>;

// Team -----------------------------------------------------------------

export const TeamSchema = z.object({
  id: z.string(),
  name: z.string(),
  status: TeamStatusSchema,
  healthScore: z.number().min(0).max(100),
  engineerCount: z.number().int().nonnegative(),
  source: z.string(),
  members: z.array(TeamMemberSchema),
  busFactorAreas: z.array(BusFactorAreaSchema),
  // Commits per day over the trailing fortnight, oldest first.
  activity: z.array(z.number()).default([]),
});
export type Team = z.infer<typeof TeamSchema>;
