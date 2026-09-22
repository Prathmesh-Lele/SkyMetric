"use client";

import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ChartTooltip } from "@/components/dashboard/chart-tooltip";
import { Skeleton } from "@/components/ui/skeleton";
import { useHeatmap } from "@/lib/hooks";

export function FareBreakdown() {
  const { data: heatmap, isLoading } = useHeatmap(30);

  const breakdown = heatmap
    ? (() => {
        const allFares = heatmap.matrix.flat().filter((v) => v > 0);
        if (!allFares.length) return null;
        const avg = allFares.reduce((s, v) => s + v, 0) / allFares.length;
        return [
          { name: "Base Fare", value: Math.round(avg * 0.70), color: "var(--chart-1)" },
          { name: "Taxes & Fees", value: Math.round(avg * 0.12), color: "var(--chart-2)" },
          { name: "Convenience", value: Math.round(avg * 0.10), color: "var(--chart-3)" },
          { name: "UDF", value: Math.round(avg * 0.08), color: "var(--chart-4)" },
        ];
      })()
    : null;

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Average Fare Breakdown</CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-[250px] w-full" />
        </CardContent>
      </Card>
    );
  }

  if (!breakdown) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Average Fare Breakdown</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">No fare data available.</p>
        </CardContent>
      </Card>
    );
  }

  const total = breakdown.reduce((sum, d) => sum + d.value, 0);
  const isSeed = heatmap?.source === "seed";

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">
          Average Fare Breakdown
          {isSeed && (
            <span className="ml-2 text-xs font-normal text-muted-foreground">
              (seed data)
            </span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[250px]">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={breakdown}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={90}
                paddingAngle={3}
                dataKey="value"
              >
                {breakdown.map((entry, i) => (
                  <Cell key={i} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                content={<ChartTooltip />}
                formatter={(value) => [
                  `₹${Number(value).toLocaleString("en-IN")} (${((Number(value) / total) * 100).toFixed(1)}%)`,
                  undefined,
                ]}
              />
              <Legend
                wrapperStyle={{ fontSize: "11px" }}
                formatter={(value) => (
                  <span className="text-muted-foreground">{value}</span>
                )}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="text-center mt-2">
          <div className="text-2xl font-bold font-mono">
            ₹{total.toLocaleString("en-IN")}
          </div>
          <div className="text-xs text-muted-foreground">
            Total Average Fare
            {heatmap?.source && ` · source: ${heatmap.source}`}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
