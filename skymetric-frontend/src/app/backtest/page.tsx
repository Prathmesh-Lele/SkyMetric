"use client";

import { BacktestChart } from "@/components/dashboard/backtest-chart";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useBacktest } from "@/lib/hooks";
import { Skeleton } from "@/components/ui/skeleton";

export default function BacktestPage() {
  const { data, isLoading } = useBacktest();

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            Back-Test vs DGCA Benchmark
          </h1>
          <p className="text-sm text-muted-foreground">
            30-day comparison of SkyMetric average fares against published DGCA
            monthly averages, with MoSPI CPI reference series
          </p>
        </div>
        {data && (
          <div className="flex gap-2 shrink-0">
            <Badge variant="secondary">MAPE: {data.mape}%</Badge>
            <Badge variant="secondary">RMSE: ₹{data.rmse}</Badge>
            <Badge variant="secondary">{data.days_compared} days</Badge>
          </div>
        )}
      </div>

      <BacktestChart />

      {isLoading ? (
        <Skeleton className="h-32 w-full" />
      ) : data ? (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">
              Methodology Note
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">{data.note}</p>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
