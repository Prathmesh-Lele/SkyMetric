"use client";

import { useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useHeatmap } from "@/lib/hooks";

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

export function DayOfWeekHeatmap() {
  const { data: heatmap, isLoading } = useHeatmap(30);

  const { corridorData, minVal, maxVal } = useMemo(() => {
    if (!heatmap) return { corridorData: [], minVal: 0, maxVal: 1 };

    const dayOfWeekFares: Record<string, Record<string, number[]>> = {};

    heatmap.corridors.forEach((corridor, rowIdx) => {
      dayOfWeekFares[corridor] = {};
      DAYS.forEach((d) => (dayOfWeekFares[corridor][d] = []));

      heatmap.dates.forEach((dateStr, colIdx) => {
        const fare = heatmap.matrix[rowIdx]?.[colIdx] ?? 0;
        if (fare <= 0) return;
        const dayIdx = new Date(dateStr).getDay();
        const dayName = DAYS[(dayIdx + 6) % 7]; // Mon=0
        dayOfWeekFares[corridor][dayName].push(fare);
      });
    });

    const result = heatmap.corridors
      .map((corridor) => {
        const avgs: Record<string, number> = {};
        DAYS.forEach((d) => {
          const fares = dayOfWeekFares[corridor][d];
          avgs[d] = fares.length
            ? Math.round(fares.reduce((s, v) => s + v, 0) / fares.length)
            : 0;
        });
        return { corridor, ...avgs };
      })
      .filter((row) => DAYS.some((d) => row[d] > 0));

    const allValues = result.flatMap((r) => DAYS.map((d) => r[d]).filter((v) => v > 0));
    return {
      corridorData: result,
      minVal: allValues.length ? Math.min(...allValues) : 0,
      maxVal: allValues.length ? Math.max(...allValues) : 1,
    };
  }, [heatmap]);

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Day-of-Week Fare Pattern</CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-[200px] w-full" />
        </CardContent>
      </Card>
    );
  }

  if (!corridorData.length) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Day-of-Week Fare Pattern</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">No fare data available.</p>
        </CardContent>
      </Card>
    );
  }

  const range = maxVal - minVal || 1;

  function getColor(value: number): string {
    if (value <= 0) return "bg-muted text-muted-foreground";
    const normalized = (value - minVal) / range;
    if (normalized < 0.25) return "bg-emerald-100 text-emerald-900 dark:bg-emerald-950/50 dark:text-emerald-300";
    if (normalized < 0.5) return "bg-yellow-100 text-yellow-900 dark:bg-yellow-950/50 dark:text-yellow-300";
    if (normalized < 0.75) return "bg-orange-100 text-orange-900 dark:bg-orange-950/50 dark:text-orange-300";
    return "bg-red-100 text-red-900 dark:bg-red-950/50 dark:text-red-300";
  }

  const isSeed = heatmap?.source === "seed";

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">
          Day-of-Week Fare Pattern
          {isSeed && (
            <span className="ml-2 text-xs font-normal text-muted-foreground">
              (seed data)
            </span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-xs text-muted-foreground mb-3">
          Average fare by day — midweek is cheapest, weekends peak
        </p>
        <div className="overflow-x-auto">
          <table className="w-full text-xs border-collapse">
            <thead>
              <tr>
                <th className="text-left p-2 font-medium text-muted-foreground border-b">
                  Route
                </th>
                {DAYS.map((day) => (
                  <th
                    key={day}
                    className="p-2 font-medium text-muted-foreground text-center border-b"
                  >
                    {day}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {corridorData.map((row) => (
                <tr key={row.corridor} className="group">
                  <td className="p-2 font-mono font-medium border-b group-hover:bg-accent/50">
                    {row.corridor}
                  </td>
                  {DAYS.map((day) => {
                    const value = row[day] ?? 0;
                    return (
                      <td
                        key={day}
                        className={`p-2 text-center font-mono rounded border ${getColor(value)} transition-transform hover:scale-105`}
                        title={`${row.corridor} ${day}: ₹${value.toLocaleString("en-IN")}`}
                        aria-label={`${row.corridor} ${day}: ₹${value.toLocaleString("en-IN")}`}
                      >
                        {value > 0 ? `₹${(value / 1000).toFixed(1)}k` : "—"}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="flex items-center justify-center gap-4 mt-3 text-xs text-muted-foreground">
          <span className="flex items-center gap-1">
            <span className="inline-block w-3 h-3 rounded bg-emerald-100 dark:bg-emerald-950/50" />
            Cheapest
          </span>
          <span className="flex items-center gap-1">
            <span className="inline-block w-3 h-3 rounded bg-red-100 dark:bg-red-950/50" />
            Most Expensive
          </span>
        </div>
      </CardContent>
    </Card>
  );
}
