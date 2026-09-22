"use client";

import { useMemo, useState } from "react";
import { KpiCards } from "@/components/dashboard/kpi-cards";
import { IndexChart } from "@/components/dashboard/index-chart";
import { WindowCards } from "@/components/dashboard/window-cards";
import { SectorTable } from "@/components/dashboard/sector-table";
import { FareBreakdown } from "@/components/dashboard/fare-breakdown";
import { DayOfWeekHeatmap } from "@/components/dashboard/day-of-week-heatmap";
import { ScraperStatusDashboard } from "@/components/dashboard/scraper-status";
import { BacktestChart } from "@/components/dashboard/backtest-chart";
import { DatePicker } from "@/components/dashboard/date-picker";
import { ExportButton } from "@/components/dashboard/export-button";
import { useDailyIndex, useHealth, useBacktest, useHeatmap } from "@/lib/hooks";

export default function DashboardPage() {
  const [selectedDate, setSelectedDate] = useState<string | undefined>();
  const { data: dailyIndex, isLoading: indexLoading, isError: indexError } = useDailyIndex(selectedDate);
  const { data: health } = useHealth();
  const { data: backtest } = useBacktest();
  const { data: heatmap } = useHeatmap(30, selectedDate);

  const headlineIndex = dailyIndex?.headline_index;
  const previousIndex = dailyIndex ? 100 : undefined; // vs base period (T-30 anchor = 100)

  const chartData = useMemo(() => {
    if (backtest?.dates?.length) {
      // Convert avg-fare series to Base=100 index (first day = 100)
      const baseFare = backtest.skymetric_index.find((v) => v > 0) ?? 1;
      return backtest.dates.map((date, i) => ({
        date: new Date(date).toLocaleDateString("en-IN", { month: "short", day: "numeric" }),
        index: Number(((backtest.skymetric_index[i] / baseFare) * 100).toFixed(2)),
      }));
    }
    if (headlineIndex === undefined) return [];
    return [
      {
        date: new Date().toLocaleDateString("en-IN", { month: "short", day: "numeric" }),
        index: headlineIndex,
      },
    ];
  }, [backtest, headlineIndex]);

  const exportData = useMemo(() => {
    if (!heatmap) return [];
    return heatmap.corridors.map((corridor, i) => {
      const row: Record<string, unknown> = { corridor };
      heatmap.dates.forEach((date, j) => {
        row[date] = heatmap.matrix[i]?.[j] ?? 0;
      });
      return row;
    });
  }, [heatmap]);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            National Airfare Price Index
          </h1>
          <p className="text-sm text-muted-foreground">
            DGCA Passenger-Weighted Basket · T+15 Anchor · Base: 100.00
          </p>
        </div>
        <div className="flex items-center gap-2">
          <DatePicker date={selectedDate} onDateChange={setSelectedDate} />
          {exportData.length > 0 && (
            <ExportButton data={exportData} filename="skymetric-heatmap.csv" />
          )}
        </div>
      </div>

      {indexError && (
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive">
          Failed to load index data. Is the backend running on port 8000?
        </div>
      )}

      <KpiCards
        headlineIndex={headlineIndex}
        previousIndex={previousIndex}
        totalCorridors={10}
        isHealthy={health?.status === "healthy"}
        liveFares={dailyIndex?.live_fares ?? heatmap?.live_fares ?? 0}
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

      <BacktestChart />

      <div className="grid gap-6 lg:grid-cols-2">
        <FareBreakdown />
        <DayOfWeekHeatmap />
      </div>

      <ScraperStatusDashboard />
    </div>
  );
}
