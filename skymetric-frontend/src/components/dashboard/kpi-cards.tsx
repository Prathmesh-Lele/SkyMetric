"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TrendingUp, TrendingDown, Activity, Plane, Radio } from "lucide-react";
import { useMounted } from "@/lib/hooks";

interface KpiCardsProps {
  headlineIndex?: number;
  previousIndex?: number;
  totalCorridors: number;
  /** undefined = health unknown (SSR/loading) → show Checking…, never Degraded */
  isHealthy?: boolean;
  liveFares?: number;
  /** ISO time of newest fare row (when National SkyMetric last recomputed from data) */
  lastDataUpdate?: string | null;
  /** ISO time of next scheduled 06:00 scrape */
  nextScheduledScrape?: string | null;
  /** Frontend poll interval (seconds) */
  refreshIntervalSeconds?: number;
}

export function KpiCards({
  headlineIndex,
  previousIndex = 100,
  totalCorridors,
  isHealthy,
  liveFares = 0,
  lastDataUpdate,
  nextScheduledScrape,
  refreshIntervalSeconds,
}: KpiCardsProps) {
  const mounted = useMounted();
  const hasIndex = headlineIndex !== undefined;
  const delta = hasIndex ? headlineIndex - previousIndex : 0;
  const deltaPct = previousIndex > 0 ? (delta / previousIndex) * 100 : 0;
  const isUp = delta >= 0;
  const showLive = mounted && liveFares > 0;
  const healthy = mounted && isHealthy === true;
  const unhealthy = mounted && isHealthy === false;

  const updatedLabel = mounted && lastDataUpdate
    ? new Date(lastDataUpdate).toLocaleString("en-IN")
    : null;
  const nextLabel = mounted && nextScheduledScrape
    ? new Date(nextScheduledScrape).toLocaleString("en-IN")
    : null;
  const refreshLabel = refreshIntervalSeconds
    ? `every ${Math.round(refreshIntervalSeconds / 60)}m`
    : "every 60s";

  return (
    <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            National SkyMetric
          </CardTitle>
          <Activity className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-3xl font-bold">
            {hasIndex ? headlineIndex.toFixed(2) : "—"}
          </div>
          <div className="flex items-center gap-2 mt-1">
            <p className="text-xs text-muted-foreground">
              T+15 Anchor · Base = 100
            </p>
            {showLive && (
              <Badge className="gap-1 text-[9px] px-1.5 py-0">
                <Radio className="h-2.5 w-2.5 animate-pulse" />
                {liveFares.toLocaleString("en-IN")} live
              </Badge>
            )}
          </div>
          <p className="text-[11px] text-muted-foreground mt-2">
            {`Updated: ${updatedLabel ?? "—"}`} · auto 06:00
            {nextLabel ? ` · next ${nextLabel}` : ""}
          </p>
          <p className="text-[11px] text-muted-foreground">
            UI refresh: {refreshLabel}
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Vs Base Period
          </CardTitle>
          {isUp ? (
            <TrendingUp className="h-4 w-4 text-destructive" />
          ) : (
            <TrendingDown className="h-4 w-4 text-emerald-500" />
          )}
        </CardHeader>
        <CardContent>
          <div
            className={`text-3xl font-bold ${
              isUp ? "text-destructive" : "text-emerald-500"
            }`}
          >
            {hasIndex ? `${isUp ? "+" : ""}${deltaPct.toFixed(2)}%` : "—"}
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            {hasIndex
              ? isUp
                ? "Prices rising vs base"
                : "Prices falling vs base"
              : "Awaiting index data"}
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Monitored Corridors
          </CardTitle>
          <Plane className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-3xl font-bold">{totalCorridors}</div>
          <p className="text-xs text-muted-foreground mt-1">
            8 Metro Trunk + 2 Regional
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Pipeline Status
          </CardTitle>
          <div
            className={`h-2 w-2 rounded-full ${
              healthy
                ? "bg-emerald-500"
                : unhealthy
                  ? "bg-destructive"
                  : "bg-muted-foreground/40"
            }`}
          />
        </CardHeader>
        <CardContent>
          <Badge
            variant={
              healthy ? "default" : unhealthy ? "destructive" : "secondary"
            }
          >
            {healthy ? "Operational" : unhealthy ? "Degraded" : "Checking…"}
          </Badge>
          <p className="text-xs text-muted-foreground mt-2">
            {showLive
              ? `${liveFares.toLocaleString("en-IN")} live SerpApi fares`
              : "DGCA Weighted Basket"}
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
