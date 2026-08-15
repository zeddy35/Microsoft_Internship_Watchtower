"use client";

import {
  IconAlertTriangle,
  IconBrandGithub,
  IconCheck,
  IconDatabase,
  IconDeviceDesktop,
  IconDownload,
  IconMoon,
  IconRefresh,
  IconSun,
  IconTrash,
} from "@tabler/icons-react";
import { useEffect, useState, type ComponentType } from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { ErrorState, SkeletonCard } from "@/components/ui/States";
import { cn } from "@/lib/cn";
import {
  useAppSettings,
  useClearData,
  useSeedDemoData,
  useUpdateSettings,
} from "@/lib/queries";
import { useTheme, type Theme } from "@/lib/theme";
import type { DataSource } from "@/lib/types";

type IconComponent = ComponentType<{ className?: string; stroke?: number }>;

function Section({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <Card className="p-4 sm:p-5">
      <h2 className="text-sm font-semibold text-neutral-primary">{title}</h2>
      <p className="mt-1 text-sm text-neutral-secondary">{description}</p>
      <div className="mt-4">{children}</div>
    </Card>
  );
}

function OptionTile({
  icon: Icon,
  label,
  description,
  selected,
  onSelect,
}: {
  icon: IconComponent;
  label: string;
  description: string;
  selected: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onSelect}
      aria-pressed={selected}
      className={cn(
        "flex flex-1 flex-col items-start gap-1 rounded-control border p-3 text-left transition-colors",
        selected
          ? "border-brand bg-brand-tint"
          : "border-neutral-light bg-neutral-white hover:bg-neutral-lighter",
      )}
    >
      <span className="flex items-center gap-2">
        <Icon
          className={cn(
            "size-4",
            selected ? "text-brand" : "text-neutral-secondary",
          )}
          stroke={1.75}
          aria-hidden="true"
        />
        <span
          className={cn(
            "text-sm font-medium",
            selected ? "text-brand" : "text-neutral-primary",
          )}
        >
          {label}
        </span>
        {selected && (
          <IconCheck
            className="size-3.5 text-brand"
            stroke={2.25}
            aria-hidden="true"
          />
        )}
      </span>
      <span className="text-xs text-neutral-tertiary">{description}</span>
    </button>
  );
}

function StatusRow({
  label,
  value,
}: {
  label: string;
  value: React.ReactNode;
}) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-2 border-b border-neutral-light py-2 last:border-0">
      <span className="text-sm text-neutral-secondary">{label}</span>
      <span className="text-sm text-neutral-primary">{value}</span>
    </div>
  );
}

const THEME_OPTIONS: {
  value: Theme;
  label: string;
  description: string;
  icon: IconComponent;
}[] = [
  {
    value: "light",
    label: "Light",
    description: "Always the light palette",
    icon: IconSun,
  },
  {
    value: "dark",
    label: "Dark",
    description: "Always the dark palette",
    icon: IconMoon,
  },
  {
    value: "system",
    label: "System",
    description: "Follow the operating system",
    icon: IconDeviceDesktop,
  },
];

export default function SettingsPage() {
  const settingsQuery = useAppSettings();
  const updateSettings = useUpdateSettings();
  const seedDemo = useSeedDemoData();
  const clearData = useClearData();
  const { theme, setTheme } = useTheme();

  const settings = settingsQuery.data;
  const [repoInput, setRepoInput] = useState("");

  // Keep the editable field in step with the server until the user types.
  useEffect(() => {
    if (settings && !updateSettings.isPending) {
      setRepoInput(settings.githubRepos.join(", "));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [settings?.githubRepos.join(",")]);

  function selectDataSource(dataSource: DataSource) {
    updateSettings.mutate({ dataSource });
  }

  function saveRepos() {
    updateSettings.mutate({
      githubRepos: repoInput
        .split(",")
        .map((repo) => repo.trim())
        .filter(Boolean),
    });
  }

  return (
    <div className="flex w-full flex-col gap-6 p-6">
      <div>
        <h1 className="text-2xl font-semibold text-neutral-primary">
          Settings
        </h1>
        <p className="mt-1 text-sm text-neutral-secondary">
          Appearance, where the data comes from, and what this instance is
          connected to.
        </p>
      </div>

      {updateSettings.isError && (
        <ErrorState
          error={updateSettings.error}
          onRetry={() => updateSettings.reset()}
        />
      )}

      <Section
        title="Appearance"
        description="The theme applies immediately and is remembered on this device."
      >
        <div className="flex flex-col gap-2 sm:flex-row">
          {THEME_OPTIONS.map((option) => (
            <OptionTile
              key={option.value}
              icon={option.icon}
              label={option.label}
              description={option.description}
              selected={theme === option.value}
              onSelect={() => setTheme(option.value)}
            />
          ))}
        </div>
      </Section>

      {settingsQuery.isPending ? (
        <SkeletonCard lines={5} />
      ) : settingsQuery.isError ? (
        <ErrorState
          error={settingsQuery.error}
          onRetry={() => settingsQuery.refetch()}
        />
      ) : settings ? (
        <>
          <Section
            title="Data source"
            description="Demo data is fabricated but runs through the real rollup and the real anomaly engine, so what you see is what Watchtower detects."
          >
            <div className="flex flex-col gap-2 sm:flex-row">
              <OptionTile
                icon={IconDatabase}
                label="Demo data"
                description="Three fabricated teams, no token needed"
                selected={settings.dataSource === "demo"}
                onSelect={() => selectDataSource("demo")}
              />
              <OptionTile
                icon={IconBrandGithub}
                label="Real teams"
                description="Collect from the repos below"
                selected={settings.dataSource === "github"}
                onSelect={() => selectDataSource("github")}
              />
            </div>

            {settings.dataSource === "demo" ? (
              <div className="mt-4 flex flex-wrap items-center gap-3">
                <Button
                  onClick={() => seedDemo.mutate()}
                  disabled={seedDemo.isPending}
                >
                  <IconDownload
                    className="size-4"
                    stroke={1.75}
                    aria-hidden="true"
                  />
                  {seedDemo.isPending ? "Loading" : "Load demo data"}
                </Button>
                {seedDemo.isSuccess && (
                  <span className="text-xs text-neutral-secondary">
                    {seedDemo.data.teams} teams · {seedDemo.data.commits}{" "}
                    commits · {seedDemo.data.anomaliesOpen} open anomalies ·{" "}
                    {seedDemo.data.resolutions} resolved
                  </span>
                )}
                {seedDemo.isError && (
                  <span className="text-xs text-state-error-fg">
                    {(seedDemo.error as Error).message}
                  </span>
                )}
              </div>
            ) : (
              <div className="mt-4 flex flex-col gap-3">
                <label
                  htmlFor="repos"
                  className="text-xs font-medium text-neutral-secondary"
                >
                  Repositories to watch
                </label>
                <input
                  id="repos"
                  value={repoInput}
                  onChange={(event) => setRepoInput(event.target.value)}
                  placeholder="microsoft/vscode, microsoft/TypeScript"
                  className="w-full rounded-control border border-neutral-light bg-neutral-white px-3 py-2 text-sm text-neutral-primary placeholder:text-neutral-tertiary focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand"
                />
                <p className="text-xs text-neutral-tertiary">
                  Comma separated, in owner/name form. One team is derived per
                  repository.
                </p>
                <div className="flex flex-wrap items-center gap-3">
                  <Button
                    onClick={saveRepos}
                    disabled={updateSettings.isPending}
                  >
                    <IconCheck
                      className="size-4"
                      stroke={1.75}
                      aria-hidden="true"
                    />
                    Save repositories
                  </Button>
                  {!settings.githubTokenConfigured && (
                    <span className="inline-flex items-center gap-1.5 text-xs text-state-warning-fg">
                      <IconAlertTriangle
                        className="size-3.5"
                        stroke={1.75}
                        aria-hidden="true"
                      />
                      No GitHub token in .env: collection is limited to 60
                      requests per hour
                    </span>
                  )}
                </div>
              </div>
            )}

            <div className="mt-5 flex flex-wrap items-center gap-3 border-t border-neutral-light pt-4">
              <Button
                variant="secondary"
                onClick={() => clearData.mutate()}
                disabled={clearData.isPending}
              >
                <IconTrash
                  className="size-4"
                  stroke={1.75}
                  aria-hidden="true"
                />
                Clear all data
              </Button>
              <span className="text-xs text-neutral-tertiary">
                Empties every table. Configuration is kept.
              </span>
            </div>
          </Section>

          <Section
            title="Connections"
            description="Read-only. Secrets live in the backend's .env file and are never sent to the browser."
          >
            <div className="flex flex-col">
              <StatusRow
                label="GitHub token"
                value={
                  <Badge
                    variant={
                      settings.githubTokenConfigured ? "success" : "neutral"
                    }
                  >
                    {settings.githubTokenConfigured ? "Configured" : "Not set"}
                  </Badge>
                }
              />
              <StatusRow
                label="Teams webhook"
                value={
                  <Badge
                    variant={
                      settings.teamsWebhookConfigured ? "success" : "neutral"
                    }
                  >
                    {settings.teamsWebhookConfigured ? "Configured" : "Not set"}
                  </Badge>
                }
              />
              <StatusRow label="Local model" value={settings.llmModel} />
              <StatusRow label="Model endpoint" value={settings.llmBaseUrl} />
              <StatusRow
                label="Background refresh"
                value={
                  settings.schedulerEnabled
                    ? `Every ${settings.refreshIntervalMinutes} min`
                    : "Disabled"
                }
              />
              <StatusRow label="Database" value={settings.duckdbPath} />
            </div>
          </Section>
        </>
      ) : null}

      <p className="flex items-center gap-1.5 text-xs text-neutral-tertiary">
        <IconRefresh className="size-3.5" stroke={1.75} aria-hidden="true" />
        Changes apply immediately. Loading demo data replaces everything
        currently stored.
      </p>
    </div>
  );
}
