"use client";

import { ThemeToggle } from "./theme-toggle";
import { Activity, Menu, Radio } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { Sidebar } from "./sidebar";
import { useHealth, useScraperStatus } from "@/lib/hooks";

const PAGE_TITLES: Record<string, string> = {
  "/": "National Index",
  "/heatmap": "Route Heatmap",
  "/elasticity": "Lead-Time Curves",
  "/carriers": "Carriers",
  "/analytics": "Analytics",
  "/backtest": "Back-Test",
  "/scraper": "Scraper Control",
  "/api-explorer": "API Explorer",
};

export function Header() {
  const pathname = usePathname();
  const { data: health } = useHealth();
  const { data: scraper } = useScraperStatus();

  const pageTitle = PAGE_TITLES[pathname] ?? "SkyMetric";
  const isLive = health?.live_data === true || (scraper?.live_fares ?? 0) > 0;
  const liveFares = scraper?.live_fares ?? 0;
  const isHealthy = health?.status === "healthy";
  const isRunning = scraper?.is_running === true;

  return (
    <header className="sticky top-0 z-40 flex h-14 items-center gap-3 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 px-4 md:px-6">
      <Sheet>
        <SheetTrigger
          render={
            <Button variant="ghost" size="icon" className="md:hidden h-9 w-9">
              <Menu className="h-5 w-5" />
              <span className="sr-only">Toggle menu</span>
            </Button>
          }
        />
        <SheetContent side="left" className="w-64 p-0">
          <Sidebar />
        </SheetContent>
      </Sheet>

      <div className="flex items-center gap-2 md:hidden">
        <Activity className="h-5 w-5 text-primary" />
        <span className="font-semibold">SkyMetric</span>
      </div>

      <span className="hidden md:inline text-sm font-medium text-muted-foreground">
        {pageTitle}
      </span>

      <div className="flex-1" />

      <div className="flex items-center gap-2">
        {isRunning && (
          <Badge variant="destructive" className="animate-pulse text-[10px]">
            Scraping…
          </Badge>
        )}
        <Badge
          variant={isLive ? "default" : "secondary"}
          className="gap-1 text-[10px] font-mono"
          title={
            isLive
              ? `${liveFares} live SerpApi fares in database`
              : "No live SerpApi fares yet — using seed/mock"
          }
        >
          <Radio
            className={`h-3 w-3 ${isLive ? "animate-pulse" : "opacity-40"}`}
          />
          {isLive ? `Live · ${liveFares.toLocaleString("en-IN")}` : "Simulated"}
        </Badge>
        <span
          className={`h-2 w-2 rounded-full ${isHealthy ? "bg-emerald-500" : "bg-destructive"}`}
          title={isHealthy ? "Backend healthy" : "Backend down"}
        />
        <span className="hidden sm:inline text-xs text-muted-foreground font-mono">
          India Airfare Price Observatory
        </span>
        <ThemeToggle />
      </div>
    </header>
  );
}
