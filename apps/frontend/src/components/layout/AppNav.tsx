"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { Icon } from "@/components/ui/Icon";
import { cn } from "@/lib/cn";

type NavItem = {
  label: string;
  href: string;
  icon: string;
  isActive: (pathname: string) => boolean;
};

const NAV_ITEMS: NavItem[] = [
  {
    label: "Overview",
    href: "/overview",
    icon: "dashboard",
    isActive: (pathname) => pathname === "/overview",
  },
  {
    label: "Teams",
    href: "/",
    icon: "groups",
    isActive: (pathname) => pathname === "/" || pathname.startsWith("/teams"),
  },
  {
    label: "Anomalies",
    href: "/anomalies",
    icon: "warning",
    isActive: (pathname) => pathname === "/anomalies",
  },
  {
    label: "Weekly digest",
    href: "/digest",
    icon: "summarize",
    isActive: (pathname) => pathname === "/digest",
  },
  {
    label: "Settings",
    href: "/settings",
    icon: "settings",
    isActive: (pathname) => pathname === "/settings",
  },
];

type FavoriteTeam = {
  id: string;
  name: string;
  dotClassName: string;
};

const FAVORITE_TEAMS: FavoriteTeam[] = [
  { id: "azure-core-networking", name: "Azure Core Networking", dotClassName: "bg-tertiary" },
  { id: "global-wan", name: "Global WAN", dotClassName: "bg-emerald-500" },
  { id: "edge-services", name: "Edge Services", dotClassName: "bg-error" },
];

export function AppNav() {
  const [collapsed, setCollapsed] = useState(false);
  const pathname = usePathname();

  return (
    <nav
      aria-label="Primary"
      className={cn(
        "flex h-screen shrink-0 flex-col border-r border-outline-variant bg-surface transition-[width] duration-200",
        collapsed ? "w-14" : "w-nav_rail_width",
      )}
    >
      <div className={cn("flex items-center gap-3 p-6", collapsed && "justify-center px-2")}>
        <Link href="/" className="flex items-center gap-3 overflow-hidden">
          <div className="flex size-8 shrink-0 items-center justify-center rounded bg-primary text-white">
            <Icon name="castle" filled size={20} />
          </div>
          {!collapsed && (
            <span className="truncate font-headline-md text-headline-md font-bold text-primary">
              Watchtower
            </span>
          )}
        </Link>
      </div>

      {!collapsed && (
        <div className="flex justify-end px-4">
          <button
            type="button"
            onClick={() => setCollapsed(true)}
            aria-label="Collapse navigation"
            aria-pressed={false}
            className="flex size-6 items-center justify-center rounded text-secondary hover:bg-surface-container-low hover:text-primary"
          >
            <Icon name="chevron_left" size={18} />
          </button>
        </div>
      )}
      {collapsed && (
        <div className="flex justify-center px-2">
          <button
            type="button"
            onClick={() => setCollapsed(false)}
            aria-label="Expand navigation"
            aria-pressed={true}
            className="flex size-6 items-center justify-center rounded text-secondary hover:bg-surface-container-low hover:text-primary"
          >
            <Icon name="chevron_right" size={18} />
          </button>
        </div>
      )}

      <div className="mt-4 flex-1 space-y-1 px-3">
        {NAV_ITEMS.map((item) => {
          const active = item.isActive(pathname);

          return (
            <Link
              key={item.href}
              href={item.href}
              title={collapsed ? item.label : undefined}
              aria-current={active ? "page" : undefined}
              className={cn(
                "flex items-center gap-3 px-4 py-2 text-secondary transition-colors duration-150",
                collapsed && "justify-center px-0",
                active
                  ? "border-l-4 border-primary bg-secondary-container/30 font-semibold text-primary"
                  : "hover:bg-secondary-container/10",
              )}
            >
              <Icon name={item.icon} filled={active} />
              {!collapsed && <span className="font-body-md">{item.label}</span>}
            </Link>
          );
        })}

        {!collapsed && (
          <div className="px-4 pt-8">
            <p className="mb-4 font-label-uppercase text-label-uppercase text-outline">
              Favorite teams
            </p>
            <div className="space-y-3">
              {FAVORITE_TEAMS.map((team) => (
                <div
                  key={team.id}
                  className="group flex cursor-pointer items-center gap-3 opacity-60 hover:opacity-100"
                >
                  <div className={cn("size-2 shrink-0 rounded-full", team.dotClassName)} />
                  <span className="truncate text-body-sm">{team.name}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="space-y-1 border-t border-outline-variant p-4">
        <Link
          href="#"
          title={collapsed ? "Support" : undefined}
          className={cn(
            "group flex items-center gap-3 px-4 py-2 text-secondary transition-colors duration-150 hover:bg-secondary-container/10",
            collapsed && "justify-center px-0",
          )}
        >
          <Icon name="help" />
          {!collapsed && <span className="font-body-md">Support</span>}
        </Link>
        <Link
          href="#"
          title={collapsed ? "Account" : undefined}
          className={cn(
            "group flex items-center gap-3 px-4 py-2 text-secondary transition-colors duration-150 hover:bg-secondary-container/10",
            collapsed && "justify-center px-0",
          )}
        >
          <Icon name="account_circle" filled />
          {!collapsed && <span className="font-body-md">Account</span>}
        </Link>
      </div>
    </nav>
  );
}
