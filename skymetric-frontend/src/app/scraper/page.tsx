"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Radio, Zap } from "lucide-react";
import { ScraperStatusDashboard } from "@/components/dashboard/scraper-status";
import { useLiveRefresh, useScraperStatus } from "@/lib/hooks";

const ALL_CITIES = ["DEL", "BOM", "BLR", "CCU", "HYD", "MAA", "IXS", "DHM"];

export default function ScraperPage() {
  const [origin, setOrigin] = useState("DEL");
  const [destination, setDestination] = useState("BOM");
  const [refreshMsg, setRefreshMsg] = useState<string | null>(null);
  const [refreshErr, setRefreshErr] = useState<string | null>(null);
  const [runMsg, setRunMsg] = useState<string | null>(null);
  const [runErr, setRunErr] = useState<string | null>(null);

  const liveRefresh = useLiveRefresh();
  const { data: status } = useScraperStatus();

  const breakdown = status?.source_breakdown ?? {};
  const liveFares = status?.live_fares ?? 0;
  const liveEnabled = status?.live_enabled ?? false;

  const handleRun = async () => {
    setRunMsg(null);
    setRunErr(null);
    try {
      const { api } = await import("@/lib/api");
      const res = await api.scraperRun(origin, destination);
      const sample = res.sample_fares?.[0];
      setRunMsg(
        `${res.message}` +
          (sample
            ? ` · e.g. ${sample.carrier} ${sample.flight_number} ₹${sample.total_fare}`
            : "")
      );
    } catch {
      setRunErr("Run failed — is the backend running on port 8000?");
    }
  };

  const handleLiveRefresh = async () => {
    setRefreshMsg(null);
    setRefreshErr(null);
    try {
      const res = await liveRefresh.mutateAsync();
      setRefreshMsg(
        `${res.message} · live fares now ${res.live_fares.toLocaleString("en-IN")}`
      );
    } catch {
      setRefreshErr("Live refresh failed — check SERPAPI_KEY / backend.");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Scraper Control</h1>
          <p className="text-sm text-muted-foreground">
            Tier 1: SerpApi (live Google Flights) → Tier 2: MockScraper
          </p>
        </div>
        <Badge variant={liveEnabled ? "default" : "secondary"} className="gap-1">
          <Radio className={`h-3 w-3 ${liveEnabled ? "animate-pulse" : "opacity-40"}`} />
          {liveEnabled ? "SerpApi live enabled" : "Mock only (no key)"}
        </Badge>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            Data Source Breakdown
            {liveFares > 0 && (
              <Badge className="gap-1 text-[10px]">
                <Radio className="h-3 w-3 animate-pulse" />
                Live
              </Badge>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
            <div className="p-3 rounded-lg border bg-card">
              <div className="text-xs text-muted-foreground">Live (SerpApi)</div>
              <div className="font-mono font-bold text-xl text-primary">
                {(breakdown.serpapi ?? 0).toLocaleString("en-IN")}
              </div>
            </div>
            <div className="p-3 rounded-lg border bg-card">
              <div className="text-xs text-muted-foreground">Mock</div>
              <div className="font-mono font-bold text-xl">
                {(breakdown.mock ?? 0).toLocaleString("en-IN")}
              </div>
            </div>
            <div className="p-3 rounded-lg border bg-card">
              <div className="text-xs text-muted-foreground">Seed history</div>
              <div className="font-mono font-bold text-xl">
                {(breakdown.seed_generator ?? 0).toLocaleString("en-IN")}
              </div>
            </div>
            <div className="p-3 rounded-lg border bg-card">
              <div className="text-xs text-muted-foreground">Total rows</div>
              <div className="font-mono font-bold text-xl">
                {(status?.total_fares ?? 0).toLocaleString("en-IN")}
              </div>
            </div>
          </div>

          <div className="flex flex-wrap gap-3">
            <Button
              onClick={handleLiveRefresh}
              disabled={liveRefresh.isPending || status?.is_running || !liveEnabled}
              className="gap-2"
            >
              <Zap className="h-4 w-4" />
              {liveRefresh.isPending
                ? "Fetching live fares…"
                : "Live Refresh (3 corridors)"}
            </Button>
            <span className="text-xs text-muted-foreground self-center">
              DEL-BOM · DEL-BLR · BOM-BLR at T+15 · skips if live data is under 12h old (quota-safe)
            </span>
          </div>

          {refreshMsg && (
            <p className="text-sm text-emerald-500">{refreshMsg}</p>
          )}
          {refreshErr && <p className="text-sm text-destructive">{refreshErr}</p>}
        </CardContent>
      </Card>

      <ScraperStatusDashboard />

      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Single Corridor Run</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <span className="text-sm font-medium">Origin</span>
              <Select value={origin} onValueChange={(v) => setOrigin(v ?? "DEL")}>
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {ALL_CITIES.map((c) => (
                    <SelectItem key={c} value={c}>
                      {c}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <span className="text-sm font-medium">Destination</span>
              <Select value={destination} onValueChange={(v) => setDestination(v ?? "BOM")}>
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {ALL_CITIES.map((c) => (
                    <SelectItem key={c} value={c}>
                      {c}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <Button
            onClick={handleRun}
            disabled={status?.is_running}
            className="w-full gap-2"
          >
            <Radio className="h-4 w-4" />
            Run Scrape (trunk = live, others = mock)
          </Button>
          {runMsg && <p className="text-sm text-emerald-500">{runMsg}</p>}
          {runErr && <p className="text-sm text-destructive">{runErr}</p>}
          <div className="flex flex-wrap gap-2">
            <Badge variant="outline">Auth: X-API-Key</Badge>
            <Badge variant="outline">skymetric-demo-key</Badge>
            <Badge variant="outline">SerpApi only on trunk corridors</Badge>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
