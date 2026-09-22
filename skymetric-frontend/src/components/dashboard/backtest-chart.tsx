"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useBacktest } from "@/lib/hooks";
import { ChartTooltip } from "@/components/dashboard/chart-tooltip";

export function BacktestChart() {
  const { data, isLoading, isError } = useBacktest();

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Back-Test vs DGCA Benchmark</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[300px] flex items-center justify-center text-muted-foreground">
            Loading back-test data...
          </div>
        </CardContent>
      </Card>
    );
  }

  if (isError || !data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Back-Test vs DGCA Benchmark</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[300px] flex items-center justify-center text-muted-foreground">
            Back-test unavailable. Is the backend running on port 8000?
          </div>
        </CardContent>
      </Card>
    );
  }

  // CPI Air Transport data from MoSPI e-Sankhyiki
  const cpiAirTransport = data.cpi?.cpi_air_transport || [];
  const cpiGeneral = data.cpi?.cpi_general || [];

  const chartData = data.dates.map((date, i) => ({
    date: new Date(date).toLocaleDateString("en-IN", { month: "short", day: "numeric" }),
    SkyMetric: data.skymetric_index[i],
    "DGCA Benchmark": data.dgca_benchmark[i],
  }));

  // CPI summary
  const latestCpiAir = cpiAirTransport.length > 0 ? cpiAirTransport[cpiAirTransport.length - 1] : null;
  const latestCpiGeneral = cpiGeneral.length > 0 ? cpiGeneral[cpiGeneral.length - 1] : null;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-base">Back-Test vs DGCA Benchmark</CardTitle>
        <div className="flex gap-2">
          <Badge variant="secondary">MAPE: {data.mape}%</Badge>
          <Badge variant="secondary">RMSE: ₹{data.rmse}</Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 11 }}
                interval={4}
              />
              <YAxis
                tick={{ fontSize: 11 }}
                tickFormatter={(v: number) => `₹${(v / 1000).toFixed(1)}k`}
              />
              <Tooltip
                content={<ChartTooltip />}
                formatter={(value) => [`₹${Number(value).toLocaleString("en-IN")}`, undefined]}
                labelFormatter={(label) => `Date: ${label}`}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="SkyMetric"
                stroke="var(--chart-1)"
                strokeWidth={2}
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="DGCA Benchmark"
                stroke="var(--chart-3)"
                strokeWidth={2}
                dot={false}
                strokeDasharray="5 5"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* CPI Reference Cards from MoSPI e-Sankhyiki */}
        {(latestCpiAir || latestCpiGeneral) && (
          <div className="mt-4 grid grid-cols-2 gap-3">
            {latestCpiAir && (
              <div className="rounded-lg border bg-card p-3">
                <div className="text-xs font-medium text-muted-foreground">CPI Air Transport (MoSPI)</div>
                <div className="text-lg font-bold">{latestCpiAir.index_value}</div>
                <div className="text-xs text-muted-foreground">
                  {latestCpiAir.month} {latestCpiAir.year} | Base: 2024=100
                </div>
                {latestCpiAir.inflation_pct !== null && (
                  <Badge variant={latestCpiAir.inflation_pct > 0 ? "destructive" : "secondary"} className="mt-1 text-xs">
                    {latestCpiAir.inflation_pct > 0 ? "+" : ""}{latestCpiAir.inflation_pct}% YoY
                  </Badge>
                )}
              </div>
            )}
            {latestCpiGeneral && (
              <div className="rounded-lg border bg-card p-3">
                <div className="text-xs font-medium text-muted-foreground">CPI General (MoSPI)</div>
                <div className="text-lg font-bold">{latestCpiGeneral.index_value}</div>
                <div className="text-xs text-muted-foreground">
                  {latestCpiGeneral.month} {latestCpiGeneral.year} | Base: 2024=100
                </div>
                {latestCpiGeneral.inflation_pct !== null && (
                  <Badge variant={latestCpiGeneral.inflation_pct > 0 ? "destructive" : "secondary"} className="mt-1 text-xs">
                    {latestCpiGeneral.inflation_pct > 0 ? "+" : ""}{latestCpiGeneral.inflation_pct}% YoY
                  </Badge>
                )}
              </div>
            )}
          </div>
        )}

        <p className="mt-2 text-xs text-muted-foreground">{data.note}</p>
      </CardContent>
    </Card>
  );
}
