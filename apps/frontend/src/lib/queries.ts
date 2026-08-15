"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseQueryOptions,
} from "@tanstack/react-query";
import { useCallback, useRef, useState } from "react";
import {
  ApiError,
  askTeam,
  clearAllData,
  getAnomalies,
  getDigest,
  getSettings,
  getTeam,
  getTeamAnomalies,
  getTeamMetrics,
  getTeams,
  getTeamSummary,
  refreshNow,
  seedDemoData,
  sendDigest,
  updateSettings,
} from "@/lib/api";
import type {
  Anomaly,
  AnomalySeverity,
  Team,
  TeamMetrics,
  TeamSummary,
} from "@/lib/types";

/**
 * TanStack hooks over the Watchtower API.
 *
 * Watchtower's data changes on a scheduler tick, not on every keystroke, so
 * queries stay fresh for a minute rather than refetching on every focus
 * change. A 4xx is never retried: an unknown team will not become known.
 */

const STALE_TIME_MS = 60_000;

export const queryKeys = {
  teams: ["teams"] as const,
  team: (teamId: string) => ["teams", teamId] as const,
  teamMetrics: (teamId: string) => ["teams", teamId, "metrics"] as const,
  teamAnomalies: (teamId: string) => ["teams", teamId, "anomalies"] as const,
  teamSummary: (teamId: string) => ["teams", teamId, "summary"] as const,
  anomalies: (severity?: AnomalySeverity) =>
    ["anomalies", severity ?? "all"] as const,
};

function retryUnlessClientError(failureCount: number, error: unknown) {
  if (error instanceof ApiError && error.status >= 400 && error.status < 500) {
    return false;
  }
  return failureCount < 2;
}

type QueryTuning<T> = Pick<UseQueryOptions<T>, "enabled" | "refetchInterval">;

export function useTeams(options?: QueryTuning<Team[]>) {
  return useQuery({
    queryKey: queryKeys.teams,
    queryFn: getTeams,
    staleTime: STALE_TIME_MS,
    retry: retryUnlessClientError,
    ...options,
  });
}

export function useTeam(teamId: string, options?: QueryTuning<Team>) {
  return useQuery({
    queryKey: queryKeys.team(teamId),
    queryFn: () => getTeam(teamId),
    staleTime: STALE_TIME_MS,
    retry: retryUnlessClientError,
    enabled: Boolean(teamId),
    ...options,
  });
}

export function useTeamMetrics(
  teamId: string,
  options?: QueryTuning<TeamMetrics>,
) {
  return useQuery({
    queryKey: queryKeys.teamMetrics(teamId),
    queryFn: () => getTeamMetrics(teamId),
    staleTime: STALE_TIME_MS,
    retry: retryUnlessClientError,
    enabled: Boolean(teamId),
    ...options,
  });
}

export function useTeamAnomalies(
  teamId: string,
  options?: QueryTuning<Anomaly[]>,
) {
  return useQuery({
    queryKey: queryKeys.teamAnomalies(teamId),
    queryFn: () => getTeamAnomalies(teamId),
    staleTime: STALE_TIME_MS,
    retry: retryUnlessClientError,
    enabled: Boolean(teamId),
    ...options,
  });
}

export function useAnomalies(
  severity?: AnomalySeverity,
  options?: QueryTuning<Anomaly[]>,
) {
  return useQuery({
    queryKey: queryKeys.anomalies(severity),
    queryFn: () => getAnomalies(severity),
    staleTime: STALE_TIME_MS,
    retry: retryUnlessClientError,
    ...options,
  });
}

export function useTeamSummary(
  teamId: string,
  options?: QueryTuning<TeamSummary | null>,
) {
  return useQuery({
    queryKey: queryKeys.teamSummary(teamId),
    queryFn: () => getTeamSummary(teamId),
    staleTime: STALE_TIME_MS,
    retry: retryUnlessClientError,
    enabled: Boolean(teamId),
    ...options,
  });
}

/** Force a collect/detect/resolve cycle, then invalidate everything on screen. */
export function useRefreshNow() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: refreshNow,
    onSuccess: () => queryClient.invalidateQueries(),
  });
}

export interface AskState {
  answer: string;
  isStreaming: boolean;
  error: string | null;
  ask: (question: string) => Promise<void>;
  reset: () => void;
}

/**
 * Streaming question box state for the Phi-4 card.
 *
 * A new question aborts the one in flight rather than interleaving two token
 * streams into the same answer.
 */
export function useAskTeam(teamId: string): AskState {
  const [answer, setAnswer] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    setAnswer("");
    setError(null);
    setIsStreaming(false);
  }, []);

  const ask = useCallback(
    async (question: string) => {
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      setAnswer("");
      setError(null);
      setIsStreaming(true);

      try {
        await askTeam(teamId, question, {
          signal: controller.signal,
          onToken: (chunk) => setAnswer((previous) => previous + chunk),
        });
      } catch (caught) {
        if (controller.signal.aborted) return;
        setError(
          caught instanceof Error ? caught.message : "Something went wrong",
        );
      } finally {
        if (!controller.signal.aborted) setIsStreaming(false);
      }
    },
    [teamId],
  );

  return { answer, isStreaming, error, ask, reset };
}

// --- settings and demo data -------------------------------------------------

export const settingsKey = ["settings"] as const;

export function useAppSettings() {
  return useQuery({
    queryKey: settingsKey,
    queryFn: getSettings,
    staleTime: STALE_TIME_MS,
    retry: retryUnlessClientError,
  });
}

export function useUpdateSettings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: updateSettings,
    onSuccess: (settings) => {
      queryClient.setQueryData(settingsKey, settings);
      queryClient.invalidateQueries();
    },
  });
}

/** Seeding rewrites every table, so everything on screen is invalidated. */
export function useSeedDemoData() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: seedDemoData,
    onSuccess: () => queryClient.invalidateQueries(),
  });
}

export function useClearData() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: clearAllData,
    onSuccess: () => queryClient.invalidateQueries(),
  });
}

// --- weekly digest ----------------------------------------------------------

export const digestKey = ["digest"] as const;

export function useDigest() {
  return useQuery({
    queryKey: digestKey,
    queryFn: getDigest,
    staleTime: STALE_TIME_MS,
    retry: retryUnlessClientError,
  });
}

/** Sending changes nothing on the server, so nothing is invalidated. */
export function useSendDigest() {
  return useMutation({ mutationFn: sendDigest });
}
