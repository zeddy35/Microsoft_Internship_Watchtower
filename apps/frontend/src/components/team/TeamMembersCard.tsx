"use client";

import { useState } from "react";
import { Avatar } from "@/components/ui/Avatar";
import { FluentCard } from "@/components/ui/FluentCard";
import { cn } from "@/lib/cn";
import type { TeamMember } from "@/lib/types";

export interface TeamMembersCardProps {
  members: TeamMember[];
  className?: string;
}

function onGoalTextClass(onGoalRate: number) {
  if (onGoalRate >= 70) return "text-emerald-600";
  if (onGoalRate >= 40) return "text-tertiary";
  return "text-error";
}

export function TeamMembersCard({ members, className }: TeamMembersCardProps) {
  const [showAll, setShowAll] = useState(false);
  const visibleMembers = showAll ? members : members.slice(0, 4);

  return (
    <FluentCard className={cn("overflow-hidden", className)}>
      <div className="flex items-center justify-between border-b border-outline-variant bg-surface-container-lowest p-6">
        <h3 className="font-title-sm text-title-sm">Team Members</h3>
        <div className="flex gap-2">
          <button
            type="button"
            className="rounded bg-surface-container-high px-3 py-1 text-body-sm font-semibold"
          >
            Active ({members.length})
          </button>
          <button
            type="button"
            className="rounded px-3 py-1 text-body-sm text-secondary hover:bg-surface-container-low"
          >
            All contributors
          </button>
        </div>
      </div>

      <table className="w-full text-left">
        <thead className="bg-surface font-label-uppercase text-label-uppercase text-secondary">
          <tr>
            <th className="px-6 py-3 font-semibold">Engineer</th>
            <th className="px-6 py-3 font-semibold">Role</th>
            <th className="px-6 py-3 text-right font-semibold">Commits/wk</th>
            <th className="px-6 py-3 text-right font-semibold">Reviews/wk</th>
            <th className="px-6 py-3 text-right font-semibold">On-goal %</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-outline-variant">
          {visibleMembers.map((member) => (
            <tr key={member.id} className="transition-colors hover:bg-surface-container-lowest">
              <td className="px-6 py-4">
                <div className="flex items-center gap-3">
                  <Avatar name={member.name} size={32} />
                  <span className="font-semibold">{member.name}</span>
                </div>
              </td>
              <td className="px-6 py-4 text-secondary">{member.role}</td>
              <td className="px-6 py-4 text-right">{member.commitsPerWeek}</td>
              <td className="px-6 py-4 text-right">{member.reviewsPerWeek}</td>
              <td className="px-6 py-4 text-right">
                <span className={cn("font-bold", onGoalTextClass(member.onGoalRate))}>
                  {member.onGoalRate}%
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {!showAll && members.length > visibleMembers.length && (
        <div className="flex justify-center border-t border-outline-variant bg-surface-container-lowest p-4">
          <button
            type="button"
            onClick={() => setShowAll(true)}
            className="text-body-sm font-semibold text-primary hover:underline"
          >
            View all {members.length} members
          </button>
        </div>
      )}
    </FluentCard>
  );
}
