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

const FARE_DATA = [
  { name: "Base Fare", value: 4200, color: "var(--chart-1)" },
  { name: "Taxes & Fees", value: 980, color: "var(--chart-2)" },
  { name: "Convenience", value: 250, color: "var(--chart-3)" },
  { name: "UDF", value: 150, color: "var(--chart-4)" },
];

export function FareBreakdown() {
  const total = FARE_DATA.reduce((sum, d) => sum + d.value, 0);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">
          Average Fare Breakdown
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[250px]">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={FARE_DATA}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={90}
                paddingAngle={3}
                dataKey="value"
              >
                {FARE_DATA.map((entry, i) => (
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
          <div className="text-xs text-muted-foreground">Total Average Fare</div>
        </div>
      </CardContent>
    </Card>
  );
}
