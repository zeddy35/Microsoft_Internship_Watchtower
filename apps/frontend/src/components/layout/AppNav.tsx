"use client";

import {
  IconAlertTriangle,
  IconChevronsLeft,
  IconChevronsRight,
  IconLayoutDashboard,
  IconMail,
  IconSettings,
  IconTower,
  IconUsersGroup,
} from "@tabler/icons-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, type ComponentType } from "react";
import { cn } from "@/lib/cn";
import { useTeams } from "@/lib/queries";
import type { TeamStatus } from "@/lib/types";

type NavItem = {
  label: string;
  href: string;
  icon: ComponentType<{ className?: string; stroke?: number }>;
};

const NAV_ITEMS: NavItem[] = [
  { label: "Overview", href: "/", icon: IconLayoutDashboard },
  { label: "Teams", href: "/teams", icon: IconUsersGroup },
  { label: "Anomalies", href: "/anomalies", icon: IconAlertTriangle },
  { label: "Weekly digest", href: "/digest", icon: IconMail },
  { label: "Settings", href: "/settings", icon: IconSettings },
];

const STATUS_DOT_CLASSES: Record<TeamStatus, string> = {
  healthy: "bg-state-success",
  "at-risk": "bg-state-warning",
  critical: "bg-state-error",
};

// The rail lists the teams that need attention first and stops well short of
// the fold; the Teams page is where the full list lives.
const RAIL_TEAM_LIMIT = 6;

export function AppNav() {
  const [collapsed, setCollapsed] = useState(false);
  const pathname = usePathname();
  const { data: teams = [] } = useTeams();
  const railTeams = teams.slice(0, RAIL_TEAM_LIMIT);

  return (
    <nav
      aria-label="Primary"
      className={cn(
        "flex h-full shrink-0 flex-col border-r border-neutral-light bg-neutral-white transition-[width] duration-200",
        collapsed ? "w-[52px]" : "w-[200px]",
      )}
    >
      <div
        className={cn(
          "flex items-center gap-2 border-b border-neutral-light px-3 py-3",
          collapsed ? "flex-col justify-center" : "justify-between",
        )}
      >
        <Link
          href="/"
          className={cn(
            "flex items-center gap-2 overflow-hidden",
            collapsed && "justify-center",
          )}
        >
          <IconTower
            className="size-5 shrink-0 text-brand"
            stroke={1.75}
            aria-hidden="true"
          />
          {!collapsed && (
            <span className="truncate text-sm font-semibold text-neutral-primary">
              Watchtower
            </span>
          )}
        </Link>

        <button
          type="button"
          onClick={() => setCollapsed((prev) => !prev)}
          aria-label={collapsed ? "Expand navigation" : "Collapse navigation"}
          aria-pressed={collapsed}
          className="flex size-6 shrink-0 items-center justify-center rounded-control text-neutral-secondary transition-colors hover:bg-neutral-lighter hover:text-neutral-primary"
        >
          {collapsed ? (
            <IconChevronsRight className="size-4" stroke={1.75} />
          ) : (
            <IconChevronsLeft className="size-4" stroke={1.75} />
          )}
        </button>
      </div>

      <ul className="flex flex-1 flex-col gap-0.5 overflow-y-auto px-2 py-3">
        {NAV_ITEMS.map((item) => {
          const active = pathname === item.href;
          const Icon = item.icon;

          return (
            <li key={item.href}>
              <Link
                href={item.href}
                title={collapsed ? item.label : undefined}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "flex items-center gap-2.5 rounded-control px-2.5 py-2 text-sm transition-colors",
                  collapsed && "justify-center px-0",
                  active
                    ? "bg-brand-tint font-medium text-brand"
                    : "text-neutral-secondary hover:bg-neutral-lighter hover:text-neutral-primary",
                )}
              >
                <Icon className="size-[18px] shrink-0" stroke={1.75} />
                {!collapsed && <span className="truncate">{item.label}</span>}
              </Link>
            </li>
          );
        })}
      </ul>

      {railTeams.length > 0 && (
        <div className="border-t border-neutral-light px-2 py-3">
          {!collapsed && (
            <p className="px-2.5 pb-2 text-xs font-medium text-neutral-tertiary">
              Teams
            </p>
          )}
          <ul className="flex flex-col gap-0.5">
            {railTeams.map((team) => (
              <li key={team.id}>
                <Link
                  href={`/teams/${team.id}`}
                  title={collapsed ? team.name : undefined}
                  className={cn(
                    "flex items-center gap-2.5 rounded-control px-2.5 py-1.5 text-sm text-neutral-secondary transition-colors hover:bg-neutral-lighter hover:text-neutral-primary",
                    collapsed && "justify-center px-0",
                  )}
                >
                  <span
                    aria-hidden="true"
                    className={cn(
                      "size-2 shrink-0 rounded-full",
                      STATUS_DOT_CLASSES[team.status],
                    )}
                  />
                  {!collapsed && <span className="truncate">{team.name}</span>}
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}
    </nav>
  );
}
