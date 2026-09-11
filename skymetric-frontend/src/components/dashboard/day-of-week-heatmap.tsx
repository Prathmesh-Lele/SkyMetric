"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

const CORRIDORS = ["DEL-BOM", "DEL-BLR", "BOM-BLR", "DEL-CCU", "DEL-HYD"];

const FARE_DATA: Record<string, Record<string, number>> = {
  "DEL-BOM": { Mon: 4200, Tue: 3980, Wed: 3850, Thu: 4050, Fri: 4500, Sat: 4800, Sun: 4600 },
  "DEL-BLR": { Mon: 4800, Tue: 4550, Wed: 4400, Thu: 4650, Fri: 5100, Sat: 5400, Sun: 5200 },
  "BOM-BLR": { Mon: 3600, Tue: 3400, Wed: 3300, Thu: 3500, Fri: 3900, Sat: 4200, Sun: 4000 },
  "DEL-CCU": { Mon: 4400, Tue: 4150, Wed: 4000, Thu: 4250, Fri: 4700, Sat: 5000, Sun: 4800 },
  "DEL-HYD": { Mon: 4600, Tue: 4350, Wed: 4200, Thu: 4450, Fri: 4900, Sat: 5200, Sun: 5000 },
};

export function DayOfWeekHeatmap() {
  const allValues = Object.values(FARE_DATA).flatMap((d) => Object.values(d));
  const minVal = Math.min(...allValues);
  const maxVal = Math.max(...allValues);
  const range = maxVal - minVal || 1;

  function getColor(value: number): string {
    const normalized = (value - minVal) / range;
    if (normalized < 0.25) return "bg-emerald-100 text-emerald-900 dark:bg-emerald-950/50 dark:text-emerald-300";
    if (normalized < 0.5) return "bg-yellow-100 text-yellow-900 dark:bg-yellow-950/50 dark:text-yellow-300";
    if (normalized < 0.75) return "bg-orange-100 text-orange-900 dark:bg-orange-950/50 dark:text-orange-300";
    return "bg-red-100 text-red-900 dark:bg-red-950/50 dark:text-red-300";
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">
          Day-of-Week Fare Pattern
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
              {CORRIDORS.map((corridor) => (
                <tr key={corridor} className="group">
                  <td className="p-2 font-mono font-medium border-b group-hover:bg-accent/50">
                    {corridor}
                  </td>
                  {DAYS.map((day) => {
                    const value = FARE_DATA[corridor][day];
                    return (
                      <td
                        key={day}
                        className={`p-2 text-center font-mono rounded border ${getColor(value)} transition-transform hover:scale-105`}
                        title={`${corridor} ${day}: ₹${value.toLocaleString("en-IN")}`}
                      >
                        ₹{(value / 1000).toFixed(1)}k
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
