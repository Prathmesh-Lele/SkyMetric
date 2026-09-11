"use client";

import { useMemo } from "react";
import { KpiCards } from "@/components/dashboard/kpi-cards";
import { IndexChart } from "@/components/dashboard/index-chart";
import { WindowCards } from "@/components/dashboard/window-cards";
import { SectorTable } from "@/components/dashboard/sector-table";
import { FareBreakdown } from "@/components/dashboard/fare-breakdown";
import { DayOfWeekHeatmap } from "@/components/dashboard/day-of-week-heatmap";
import { ScraperStatusDashboard } from "@/components/dashboard/scraper-status";
import { useDailyIndex, useHealth } from "@/lib/hooks";

function seededRandom(seed: number): number {
  const x = Math.sin(seed * 12.9898 + seed * 78.233) * 43758.5453;
  return x - Math.floor(x);
}

export default function DashboardPage() {
  const { data: dailyIndex, isLoading: indexLoading } = useDailyIndex();
  const { data: health } = useHealth();

  const headlineIndex = dailyIndex?.headline_index ?? 108.42;

  const chartData = useMemo(() => {
    return Array.from({ length: 30 }, (_, i) => {
      const d = new Date();
      d.setDate(d.getDate() - (29 - i));
      const noise = 0.95 + seededRandom(i + 1) * 0.1;
      return {
        date: d.toLocaleDateString("en-IN", {
          month: "short",
          day: "numeric",
        }),
        index: Math.round(headlineIndex * noise * 100) / 100,
      };
    });
  }, [headlineIndex]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">
          National Airfare Price Index
        </h1>
        <p className="text-sm text-muted-foreground">
          DGCA Passenger-Weighted Basket · T+15 Anchor · Base: 100.00
        </p>
      </div>

      <KpiCards
        headlineIndex={headlineIndex}
        previousIndex={97.5}
        totalCorridors={10}
        isHealthy={health?.status === "healthy"}
      />

      <IndexChart data={chartData} isLoading={indexLoading} />

      <WindowCards
        windows={dailyIndex?.window_indices ?? {}}
        isLoading={indexLoading}
      />

      <SectorTable
        sectors={dailyIndex?.sector_indices ?? {}}
        isLoading={indexLoading}
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <FareBreakdown />
        <DayOfWeekHeatmap />
      </div>

      <ScraperStatusDashboard />
    </div>
  );
}
