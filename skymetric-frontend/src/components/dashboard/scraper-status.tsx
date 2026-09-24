"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useMounted, useScraperStatus } from "@/lib/hooks";
import { api } from "@/lib/api";

const CITIES = ["DEL", "BOM", "BLR", "CCU", "HYD", "MAA", "IXS", "DHM"];
const API_KEY = "skymetric-demo-key";

export function ScraperStatusDashboard() {
  const mounted = useMounted();
  const { data: rawStatus, refetch, isError } = useScraperStatus();
  // Null API data until mount so SSR HTML matches first client paint
  const status = mounted ? rawStatus : undefined;
  const [origin, setOrigin] = useState("DEL");
  const [destination, setDestination] = useState("BOM");
  const [isRunning, setIsRunning] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const showLive = (status?.live_fares ?? 0) > 0;
  const lastRun = status?.last_run
    ? new Date(status.last_run).toLocaleString("en-IN")
    : null;

  const handleRunScraper = async () => {
    setIsRunning(true);
    setMessage(null);
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/scraper/run?origin=${origin}&destination=${destination}`,
        { method: "POST", headers: { "X-API-Key": API_KEY } }
      );
      const data = await res.json();
      if (!res.ok) {
        setMessage(data.detail || `Error: ${res.status}`);
      } else {
        setMessage(data.message || "Scraper triggered");
        setTimeout(() => refetch(), 2000);
      }
    } catch (e) {
      setMessage(`Failed: ${e instanceof Error ? e.message : "Unknown error"}`);
    } finally {
      setIsRunning(false);
    }
  };

  if (mounted && isError) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Scraper Status</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-destructive">
            Unable to connect to scraper API. Is the backend running?
          </p>
        </CardContent>
      </Card>
    );
  }

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
          {showLive && (
            <Badge className="gap-1 text-[10px]">
              <span className="h-1.5 w-1.5 rounded-full bg-primary-foreground animate-pulse" />
              {(status?.live_fares ?? 0).toLocaleString("en-IN")} live
            </Badge>
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
            <span className="text-muted-foreground">Live Source</span>
            <div className="font-mono font-bold text-lg">
              {status?.live_enabled ? "SerpApi" : "Mock"}
            </div>
          </div>
        </div>

        <div className="text-xs text-muted-foreground">
          Last run: {lastRun ?? "Never"}
          {status?.last_fetch_source && ` · last fetch: ${status.last_fetch_source}`}
        </div>

        {status?.next_scheduled_scrape && (
          <div className="text-xs text-muted-foreground">
            Next auto scrape: {new Date(status.next_scheduled_scrape).toLocaleString("en-IN")}
          </div>
        )}

        {status?.source_breakdown && (
          <div className="text-xs text-muted-foreground font-mono">
            {Object.entries(status.source_breakdown)
              .map(([k, v]) => `${k}: ${v}`)
              .join(" · ")}
          </div>
        )}

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
          {message && (
            <p className="text-xs text-muted-foreground" role="status">
              {message}
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
