"use client";

import { useState, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useHeatmap } from "@/lib/hooks";
import { Skeleton } from "@/components/ui/skeleton";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";

const ALL_CITIES = ["DEL", "BOM", "BLR", "CCU", "HYD", "MAA", "IXS", "DHM"];

const CITY_NAMES: Record<string, string> = {
  DEL: "Delhi",
  BOM: "Mumbai",
  BLR: "Bengaluru",
  CCU: "Kolkata",
  HYD: "Hyderabad",
  MAA: "Chennai",
  IXS: "Silchar",
  DHM: "Dharamshala",
};

export default function HeatmapPage() {
  const { data, isLoading, isError } = useHeatmap(30);
  const [selectedOrigin, setSelectedOrigin] = useState("all");
  const [selectedDest, setSelectedDest] = useState("all");

  const filteredData = useMemo(() => {
    if (!data) return null;
    if (selectedOrigin === "all" && selectedDest === "all") return data;

    const filteredCorridors: string[] = [];
    const filteredMatrix: number[][] = [];

    data.corridors.forEach((corridor, i) => {
      const [orig, dest] = corridor.split("-");
      const matchOrigin = selectedOrigin === "all" || orig === selectedOrigin;
      const matchDest = selectedDest === "all" || dest === selectedDest;
      if (matchOrigin && matchDest) {
        filteredCorridors.push(corridor);
        filteredMatrix.push(data.matrix[i]);
      }
    });

    return { ...data, corridors: filteredCorridors, matrix: filteredMatrix };
  }, [data, selectedOrigin, selectedDest]);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-[500px] w-full" />
      </div>
    );
  }

  if (isError || !filteredData) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Route Heatmap</h1>
        </div>
        <Card>
          <CardContent className="p-8 text-center text-muted-foreground">
            Heatmap data unavailable. Start the backend:{" "}
            <code className="font-mono text-xs bg-muted px-1.5 py-0.5 rounded">
              uvicorn skymetric.api.main:app --port 8000
            </code>
          </CardContent>
        </Card>
      </div>
    );
  }

  const allValues = filteredData.matrix.flat();
  const minVal = Math.min(...allValues);
  const maxVal = Math.max(...allValues);
  const range = maxVal - minVal || 1;
  const isLive = (filteredData.live_fares ?? 0) > 0;

  function getHeatColor(value: number): string {
    const normalized = (value - minVal) / range;
    if (normalized < 0.25) return "bg-emerald-100 text-emerald-900 dark:bg-emerald-950/50 dark:text-emerald-300";
    if (normalized < 0.5) return "bg-yellow-100 text-yellow-900 dark:bg-yellow-950/50 dark:text-yellow-300";
    if (normalized < 0.75) return "bg-orange-100 text-orange-900 dark:bg-orange-950/50 dark:text-orange-300";
    return "bg-red-100 text-red-900 dark:bg-red-950/50 dark:text-red-300";
  }

  function getHeatBorder(value: number): string {
    const normalized = (value - minVal) / range;
    if (normalized < 0.25) return "border-emerald-200 dark:border-emerald-800";
    if (normalized < 0.5) return "border-yellow-200 dark:border-yellow-800";
    if (normalized < 0.75) return "border-orange-200 dark:border-orange-800";
    return "border-red-200 dark:border-red-800";
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-bold tracking-tight">Route Heatmap</h1>
        {isLive && (
          <Badge className="gap-1 text-[10px]">
            <span className="h-1.5 w-1.5 rounded-full bg-primary-foreground animate-pulse" />
            Live
          </Badge>
        )}
        <p className="text-sm text-muted-foreground">
          Sector × Date fare matrix · {filteredData.corridors.length} corridors ·{" "}
          {filteredData.dates.length} days
        </p>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium">Origin:</span>
              <Select value={selectedOrigin} onValueChange={(v) => setSelectedOrigin(v ?? "all")}>
                <SelectTrigger className="w-[140px]">
                  <SelectValue placeholder="All Cities" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Cities</SelectItem>
                  {ALL_CITIES.map((city) => (
                    <SelectItem key={city} value={city}>
                      {city} - {CITY_NAMES[city]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-sm font-medium">Destination:</span>
              <Select value={selectedDest} onValueChange={(v) => setSelectedDest(v ?? "all")}>
                <SelectTrigger className="w-[140px]">
                  <SelectValue placeholder="All Cities" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Cities</SelectItem>
                  {ALL_CITIES.map((city) => (
                    <SelectItem key={city} value={city}>
                      {city} - {CITY_NAMES[city]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {(selectedOrigin !== "all" || selectedDest !== "all") && (
              <Badge variant="secondary" className="cursor-pointer" onClick={() => { setSelectedOrigin("all"); setSelectedDest("all"); }}>
                Clear Filters
              </Badge>
            )}

            <div className="ml-auto flex items-center gap-3 text-xs text-muted-foreground">
              <span className="flex items-center gap-1">
                <span className="inline-block w-3 h-3 rounded border bg-emerald-100 dark:bg-emerald-950/50" />
                Low
              </span>
              <span className="flex items-center gap-1">
                <span className="inline-block w-3 h-3 rounded border bg-yellow-100 dark:bg-yellow-950/50" />
                Medium
              </span>
              <span className="flex items-center gap-1">
                <span className="inline-block w-3 h-3 rounded border bg-orange-100 dark:bg-orange-950/50" />
                High
              </span>
              <span className="flex items-center gap-1">
                <span className="inline-block w-3 h-3 rounded border bg-red-100 dark:bg-red-950/50" />
                Peak
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Heatmap Grid */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">
            Fare Heatmap ({filteredData.unit})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {filteredData.corridors.length === 0 ? (
            <p className="text-center text-muted-foreground py-8">
              No corridors match the selected filters.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-xs border-collapse">
                <thead>
                  <tr>
                    <th className="text-left p-2 font-medium text-muted-foreground sticky left-0 bg-card z-10 border-b">
                      Route
                    </th>
                    {filteredData.dates.map((d) => (
                      <th
                        key={d}
                        className="p-2 font-medium text-muted-foreground text-center border-b min-w-[60px]"
                      >
                        {new Date(d).toLocaleDateString("en-IN", {
                          month: "short",
                          day: "numeric",
                        })}
                      </th>
                    ))}
                    <th className="p-2 font-medium text-muted-foreground text-center border-b">
                      Avg
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {filteredData.corridors.map((corridor, i) => {
                    const rowValues = filteredData.matrix[i];
                    const rowAvg = rowValues.reduce((a, b) => a + b, 0) / rowValues.length;
                    return (
                      <tr key={corridor} className="group">
                        <td className="p-2 font-mono font-medium sticky left-0 bg-card z-10 border-b group-hover:bg-accent/50">
                          <div className="flex items-center gap-2">
                            <span>{corridor}</span>
                            <span className="text-[10px] text-muted-foreground">
                              {corridor.split("-").map(c => CITY_NAMES[c] || c).join(" → ")}
                            </span>
                          </div>
                        </td>
                        {rowValues.map((value, j) => (
                          <td
                            key={j}
                            className={`p-1 text-center font-mono rounded border ${getHeatColor(value)} ${getHeatBorder(value)} cursor-default transition-transform hover:scale-110 hover:z-10 hover:shadow-lg`}
                            title={`${corridor} · ${filteredData.dates[j]}: ₹${Math.round(value).toLocaleString("en-IN")}`}
                          >
                            {Math.round(value)}
                          </td>
                        ))}
                        <td className="p-2 text-center font-mono font-medium border-b bg-muted/30">
                          ₹{Math.round(rowAvg).toLocaleString("en-IN")}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Summary Stats */}
      {filteredData.corridors.length > 0 && (
        <div className="grid gap-4 grid-cols-2 md:grid-cols-4">
          <Card>
            <CardContent className="p-4 text-center">
              <div className="text-2xl font-bold font-mono">
                ₹{Math.round(minVal).toLocaleString("en-IN")}
              </div>
              <div className="text-xs text-muted-foreground">Lowest Fare</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <div className="text-2xl font-bold font-mono">
                ₹{Math.round(maxVal).toLocaleString("en-IN")}
              </div>
              <div className="text-xs text-muted-foreground">Highest Fare</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <div className="text-2xl font-bold font-mono">
                ₹{Math.round(allValues.reduce((a, b) => a + b, 0) / allValues.length).toLocaleString("en-IN")}
              </div>
              <div className="text-xs text-muted-foreground">Average Fare</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <div className="text-2xl font-bold font-mono">
                {((maxVal - minVal) / minVal * 100).toFixed(1)}%
              </div>
              <div className="text-xs text-muted-foreground">Fare Spread</div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
