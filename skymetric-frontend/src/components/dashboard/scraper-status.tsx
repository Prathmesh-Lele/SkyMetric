"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useScraperStatus } from "@/lib/hooks";
import { api } from "@/lib/api";

const CITIES = ["DEL", "BOM", "BLR", "CCU", "HYD", "MAA", "IXS", "DHM"];

export function ScraperStatusDashboard() {
  const { data: status, refetch } = useScraperStatus();
  const [origin, setOrigin] = useState("DEL");
  const [destination, setDestination] = useState("BOM");
  const [isRunning, setIsRunning] = useState(false);

  const handleRunScraper = async () => {
    setIsRunning(true);
    try {
      await api.scraperRun(origin, destination);
      setTimeout(() => refetch(), 2000);
    } catch {
      // API error handled by status polling
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          Scraper Status
          {status?.is_running ? (
            <Badge variant="destructive" className="animate-pulse">Running</Badge>
          ) : (
            <Badge variant="secondary">Idle</Badge>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <span className="text-muted-foreground">Quotes Collected</span>
            <div className="font-mono font-bold text-lg">{status?.quotes_collected ?? 0}</div>
          </div>
          <div>
            <span className="text-muted-foreground">Sources Checked</span>
            <div className="font-mono font-bold text-lg">{status?.sources_checked ?? 0}</div>
          </div>
          <div>
            <span className="text-muted-foreground">Jobs Completed</span>
            <div className="font-mono font-bold text-lg">
              {status?.completed_jobs ?? 0}/{status?.total_jobs ?? 0}
            </div>
          </div>
          <div>
            <span className="text-muted-foreground">Backoff Triggers</span>
            <div className="font-mono font-bold text-lg">{status?.backoff_triggers ?? 0}</div>
          </div>
        </div>

        <div className="text-xs text-muted-foreground">
          Last run: {status?.last_run ? new Date(status.last_run).toLocaleString("en-IN") : "Never"}
        </div>

        <div className="text-xs text-muted-foreground">
          Active sources: {status?.active_sources?.join(", ") || "None"}
        </div>

        <div className="flex flex-col gap-2">
          <div className="flex gap-2">
            <Select value={origin} onValueChange={(v) => setOrigin(v ?? "DEL")}>
              <SelectTrigger className="w-[100px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {CITIES.map((c) => (
                  <SelectItem key={c} value={c}>{c}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={destination} onValueChange={(v) => setDestination(v ?? "BOM")}>
              <SelectTrigger className="w-[100px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {CITIES.map((c) => (
                  <SelectItem key={c} value={c}>{c}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button
              size="sm"
              onClick={handleRunScraper}
              disabled={status?.is_running || isRunning}
            >
              {status?.is_running || isRunning ? "Running..." : "Run Scraper"}
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
