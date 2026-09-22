"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TrendingUp, TrendingDown, Activity, Plane, Radio } from "lucide-react";

interface KpiCardsProps {
  headlineIndex?: number;
  previousIndex?: number;
  totalCorridors: number;
  isHealthy: boolean;
  liveFares?: number;
}

export function KpiCards({
  headlineIndex,
  previousIndex = 100,
  totalCorridors,
  isHealthy,
  liveFares = 0,
}: KpiCardsProps) {
  const hasIndex = headlineIndex !== undefined;
  const delta = hasIndex ? headlineIndex - previousIndex : 0;
  const deltaPct = previousIndex > 0 ? (delta / previousIndex) * 100 : 0;
  const isUp = delta >= 0;

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
            {liveFares > 0 && (
              <Badge className="gap-1 text-[9px] px-1.5 py-0">
                <Radio className="h-2.5 w-2.5 animate-pulse" />
                {liveFares.toLocaleString("en-IN")} live
              </Badge>
            )}
          </div>
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
              isHealthy ? "bg-emerald-500" : "bg-destructive"
            }`}
          />
        </CardHeader>
        <CardContent>
          <Badge variant={isHealthy ? "default" : "destructive"}>
            {isHealthy ? "Operational" : "Degraded"}
          </Badge>
          <p className="text-xs text-muted-foreground mt-2">
            {liveFares > 0
              ? `${liveFares.toLocaleString("en-IN")} live SerpApi fares`
              : "DGCA Weighted Basket"}
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
