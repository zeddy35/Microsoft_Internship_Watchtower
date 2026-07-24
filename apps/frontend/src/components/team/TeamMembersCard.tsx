// "Team members" card: initials avatar, name and role, commit/review/on-goal stats, and activity status.
import { Card } from "@/components/ui/Card";
import { cn } from "@/lib/cn";
import type { MemberActivityStatus, TeamMember } from "@/lib/types";

export interface TeamMembersCardProps {
  members: TeamMember[];
  className?: string;
}

const ACTIVITY_DOT_CLASSES: Record<MemberActivityStatus, string> = {
  active: "bg-state-success",
  away: "bg-state-warning",
  offline: "bg-neutral-tertiary",
};

const ACTIVITY_LABEL: Record<MemberActivityStatus, string> = {
  active: "Active",
  away: "Away",
  offline: "Offline",
};

export function TeamMembersCard({ members, className }: TeamMembersCardProps) {
  return (
    <Card className={cn("p-4 sm:p-5", className)}>
      <h2 className="text-sm font-semibold text-neutral-primary">
        Team members
      </h2>
      <ul className="mt-4 flex flex-col divide-y divide-neutral-light">
        {members.map((member) => (
          <li
            key={member.id}
            className="flex flex-wrap items-center justify-between gap-3 py-3 first:pt-0 last:pb-0"
          >
            <div className="flex min-w-0 items-center gap-3">
              <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-brand-tint text-xs font-semibold text-brand">
                {member.initials}
              </span>
              <div className="min-w-0">
                <p className="truncate text-sm font-medium text-neutral-primary">
                  {member.name}
                </p>
                <p className="truncate text-xs text-neutral-tertiary">
                  {member.role}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-4 text-xs text-neutral-secondary">
              <span>{member.commitsPerWeek} commits/wk</span>
              <span>{member.avgReviewTimeDays}d review</span>
              <span>{member.onGoalRate}% on goal</span>
              <span className="inline-flex items-center gap-1.5">
                <span
                  aria-hidden="true"
                  className={cn(
                    "size-2 rounded-full",
                    ACTIVITY_DOT_CLASSES[member.activityStatus],
                  )}
                />
                {ACTIVITY_LABEL[member.activityStatus]}
              </span>
            </div>
          </li>
        ))}
      </ul>
    </Card>
  );
}
