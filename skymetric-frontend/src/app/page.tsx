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

  const headlineIndex = dailyIndex?.headline_index ?? 108.42;

  const chartData = useMemo(() => {
    if (backtest?.dates?.length) {
      return backtest.dates.map((date, i) => ({
        date: new Date(date).toLocaleDateString("en-IN", { month: "short", day: "numeric" }),
        index: backtest.skymetric_index[i] ?? 0,
      }));
    }
    return Array.from({ length: 30 }, (_, i) => {
      const d = new Date();
      d.setDate(d.getDate() - (29 - i));
      return {
        date: d.toLocaleDateString("en-IN", { month: "short", day: "numeric" }),
        index: headlineIndex,
      };
    });
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

      <BacktestChart />

      <div className="grid gap-6 lg:grid-cols-2">
        <FareBreakdown />
        <DayOfWeekHeatmap />
      </div>

      <ScraperStatusDashboard />
    </div>
  );
}
