"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Play, Database } from "lucide-react";
import { ScraperStatusDashboard } from "@/components/dashboard/scraper-status";
import { useScraperRun, useScraperStatus } from "@/lib/hooks";
import { api } from "@/lib/api";

const ALL_CITIES = ["DEL", "BOM", "BLR", "CCU", "HYD", "MAA", "IXS", "DHM"];

export default function ScraperPage() {
  const [origin, setOrigin] = useState("DEL");
  const [destination, setDestination] = useState("BOM");
  const [date, setDate] = useState("");
  const [runAllMsg, setRunAllMsg] = useState<string | null>(null);
  const [runAllErr, setRunAllErr] = useState<string | null>(null);

  const runMutation = useScraperRun();
  const { data: status } = useScraperStatus();

  const handleRun = () => {
    runMutation.mutate({
      origin,
      destination,
      date: date || undefined,
    });
  };

  const handleRunAll = async () => {
    setRunAllMsg(null);
    setRunAllErr(null);
    try {
      const res = await api.scraperRunAll();
      setRunAllMsg(res.message ?? "Full scrape triggered (50 jobs).");
    } catch {
      setRunAllErr("Run-all failed. Check API key / backend status.");
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Scraper Control</h1>
        <p className="text-sm text-muted-foreground">
          Trigger manual scrapes and monitor pipeline health · Tier 1: SerpApi →
          Tier 2: MockScraper
        </p>
      </div>

      <ScraperStatusDashboard />

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">
              Single Corridor Run
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-3 gap-3">
              <div className="space-y-1.5">
                <span className="text-sm font-medium">Origin</span>
                <select
                  className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm"
                  value={origin}
                  onChange={(e) => setOrigin(e.target.value)}
                >
                  {ALL_CITIES.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>
              <div className="space-y-1.5">
                <span className="text-sm font-medium">Destination</span>
                <select
                  className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm"
                  value={destination}
                  onChange={(e) => setDestination(e.target.value)}
                >
                  {ALL_CITIES.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>
              <div className="space-y-1.5">
                <span className="text-sm font-medium">Date</span>
                <input
                  type="date"
                  className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm"
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                />
              </div>
            </div>
            <Button
              onClick={handleRun}
              disabled={runMutation.isPending || status?.is_running}
              className="w-full"
            >
              <Play className="h-4 w-4 mr-2" />
              {runMutation.isPending ? "Triggering…" : "Run Scrape"}
            </Button>
            {runMutation.isError && (
              <p className="text-sm text-destructive">
                Trigger failed — backend down or invalid API key.
              </p>
            )}
            {runMutation.isSuccess && (
              <p className="text-sm text-emerald-500">
                Scrape triggered for {origin}–{destination}.
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">
              Full Fleet Run (10 × 5 = 50 jobs)
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">
              Scrapes all 10 corridors across T+1, T+7, T+15, T+30, T+45
              advance windows, then recomputes the national index.
            </p>
            <Button
              onClick={handleRunAll}
              disabled={status?.is_running}
              variant="secondary"
              className="w-full"
            >
              <Database className="h-4 w-4 mr-2" />
              Run All Corridors
            </Button>
            {runAllMsg && (
              <p className="text-sm text-emerald-500">{runAllMsg}</p>
            )}
            {runAllErr && (
              <p className="text-sm text-destructive">{runAllErr}</p>
            )}
            <div className="flex gap-2 pt-2">
              <Badge variant="outline">Auth: X-API-Key</Badge>
              <Badge variant="outline">skymetric-demo-key</Badge>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
