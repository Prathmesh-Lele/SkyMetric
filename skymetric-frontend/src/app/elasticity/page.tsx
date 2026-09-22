"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useElasticity } from "@/lib/hooks";
import { Skeleton } from "@/components/ui/skeleton";
import { ChartTooltip } from "@/components/dashboard/chart-tooltip";

const ROUTE_COLORS = [
  "#3b82f6",
  "#ef4444",
  "#10b981",
  "#f59e0b",
  "#8b5cf6",
  "#ec4899",
  "#06b6d4",
  "#84cc16",
  "#f97316",
  "#6366f1",
];

export default function ElasticityPage() {
  const { data, isLoading, isError } = useElasticity();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-[400px] w-full" />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            Advance Purchase Elasticity
          </h1>
        </div>
        <Card>
          <CardContent className="p-8 text-center text-muted-foreground">
            Elasticity data unavailable. Is the backend running on port 8000?
          </CardContent>
        </Card>
      </div>
    );
  }

  const routes = Object.keys(data.curves);
  const windows = data.advance_windows;

  const chartData = windows.map((w) => {
    const point: Record<string, string | number> = { window: `T+${w}` };
    routes.forEach((route) => {
      point[route] = data.curves[route]?.[String(w)] ?? 0;
    });
    return point;
  });

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            Advance Purchase Elasticity
          </h1>
          <p className="text-sm text-muted-foreground">
            Price curves across T+1 to T+45 advance booking windows
          </p>
        </div>
        <Badge variant="outline" className="shrink-0">
          Modeled estimate
        </Badge>
      </div>

      {data.note && (
        <p className="text-xs text-muted-foreground border rounded-lg p-3 bg-muted/30">
          {data.note}
        </p>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">
            Lead-Time Price Curves by Corridor
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[400px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
                <XAxis
                  dataKey="window"
                  tick={{ fontSize: 11 }}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fontSize: 11 }}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(v) => `₹${(v / 1000).toFixed(1)}k`}
                />
                <Tooltip
                  content={<ChartTooltip />}
                  formatter={(value) => [
                    `₹${Number(value).toLocaleString("en-IN")}`,
                    undefined,
                  ]}
                />
                <Legend wrapperStyle={{ fontSize: "11px" }} />
                {routes.slice(0, 6).map((route, i) => (
                  <Line
                    key={route}
                    type="monotone"
                    dataKey={route}
                    stroke={ROUTE_COLORS[i % ROUTE_COLORS.length]}
                    strokeWidth={2}
                    dot={{ r: 3 }}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 grid-cols-2 sm:grid-cols-3 lg:grid-cols-5">
        {windows.map((w) => {
          const avgPrice =
            routes.reduce(
              (sum, r) => sum + (data.curves[r]?.[String(w)] ?? 0),
              0
            ) / routes.length;
          return (
            <Card key={w}>
              <CardContent className="p-4 text-center">
                <div className="text-xs text-muted-foreground font-mono">
                  T+{w}
                </div>
                <div className="text-xl font-bold mt-1">
                  ₹{Math.round(avgPrice).toLocaleString("en-IN")}
                </div>
                <div className="text-[10px] text-muted-foreground mt-1">
                  {w === 1
                    ? "Emergency"
                    : w === 7
                    ? "Short-Horizon"
                    : w === 15
                    ? "Anchor"
                    : w === 30
                    ? "Baseline"
                    : "Early Bird"}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
