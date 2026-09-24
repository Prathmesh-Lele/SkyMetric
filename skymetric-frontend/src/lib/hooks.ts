import { useEffect, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "./api";

/** True only after client mount — keeps SSR HTML identical to first client render. */
export function useMounted() {
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);
  return mounted;
}

export function useDailyIndex(date?: string) {
  return useQuery({
    queryKey: ["dailyIndex", date],
    queryFn: () => api.dailyIndex(date),
    staleTime: 30_000,
    retry: 2,
    refetchInterval: 60_000,
  });
}

export function useSectorIndices(date?: string) {
  return useQuery({
    queryKey: ["sectorIndices", date],
    queryFn: () => api.sectorIndices(date),
    staleTime: 30_000,
    retry: 2,
    refetchInterval: 60_000,
  });
}

export function useHeatmap(days = 30, date?: string) {
  return useQuery({
    queryKey: ["heatmap", days, date],
    queryFn: () => api.heatmap(days, date),
    staleTime: 60_000,
    retry: 2,
    refetchInterval: 60_000,
  });
}

export function useCarriers() {
  return useQuery({
    queryKey: ["carriers"],
    queryFn: () => api.carriers(),
    staleTime: 600_000,
    retry: 2,
  });
}

export function useElasticity(date?: string) {
  return useQuery({
    queryKey: ["elasticity", date],
    queryFn: () => api.elasticity(date),
    staleTime: 60_000,
    retry: 2,
    refetchInterval: 120_000,
  });
}

export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: () => api.health(),
    staleTime: 15_000,
    retry: 3,
    refetchInterval: 30_000,
  });
}

export function useScraperStatus() {
  return useQuery({
    queryKey: ["scraperStatus"],
    queryFn: () => api.scraperStatus(),
    staleTime: 5_000,
    retry: 2,
    refetchInterval: (query) => {
      const status = query.state.data;
      return status?.is_running ? 2_000 : 15_000;
    },
  });
}

export function useScraperRun() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (params: { origin?: string; destination?: string; date?: string }) =>
      api.scraperRun(params.origin, params.destination, params.date),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["scraperStatus"] });
      queryClient.invalidateQueries({ queryKey: ["dailyIndex"] });
      queryClient.invalidateQueries({ queryKey: ["heatmap"] });
      queryClient.invalidateQueries({ queryKey: ["sectorIndices"] });
    },
  });
}

export function useLiveRefresh() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (force?: boolean) => api.liveRefresh(force ?? false),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["scraperStatus"] });
      queryClient.invalidateQueries({ queryKey: ["dailyIndex"] });
      queryClient.invalidateQueries({ queryKey: ["heatmap"] });
      queryClient.invalidateQueries({ queryKey: ["sectorIndices"] });
      queryClient.invalidateQueries({ queryKey: ["dataTrust"] });
    },
  });
}

export function useBacktest() {
  return useQuery({
    queryKey: ["backtest"],
    queryFn: () => api.backtest(),
    staleTime: 300_000,
    retry: 2,
  });
}

export function useCpi() {
  return useQuery({
    queryKey: ["cpi"],
    queryFn: () => api.cpiAll(),
    staleTime: 600_000,
    retry: 2,
  });
}

export function useSuperlative(date?: string) {
  return useQuery({
    queryKey: ["superlative", date],
    queryFn: () => api.superlative(date),
    staleTime: 60_000,
    retry: 2,
    refetchInterval: 120_000,
  });
}

export function useAnomalies(date?: string, threshold?: number) {
  return useQuery({
    queryKey: ["anomalies", date, threshold],
    queryFn: () => api.anomalies(date, threshold),
    staleTime: 60_000,
    retry: 2,
    refetchInterval: 120_000,
  });
}

export function useDataTrust(date?: string) {
  return useQuery({
    queryKey: ["dataTrust", date],
    queryFn: () => api.dataTrust(date),
    staleTime: 60_000,
    retry: 2,
    refetchInterval: 120_000,
  });
}
