"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Activity } from "lucide-react";
import {
  LayoutDashboard,
  Map,
  TrendingUp,
  Plane,
  FileCode,
  BarChart3,
  FlaskConical,
  Bot,
} from "lucide-react";

const navItems = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/heatmap", label: "Route Heatmap", icon: Map },
  { href: "/elasticity", label: "Lead-Time Curves", icon: TrendingUp },
  { href: "/carriers", label: "Carriers", icon: Plane },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/backtest", label: "Back-Test", icon: FlaskConical },
  { href: "/scraper", label: "Scraper Control", icon: Bot },
  { href: "/api-explorer", label: "API Explorer", icon: FileCode },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden md:flex w-64 flex-col border-r bg-card">
      <div className="flex h-14 items-center gap-2 border-b px-4">
        <Activity className="h-5 w-5 text-primary" />
        <span className="font-semibold text-lg tracking-tight">SkyMetric</span>
        <span className="ml-auto text-[10px] text-muted-foreground font-mono">
          v1.0
        </span>
      </div>
      <nav className="flex-1 p-3 space-y-1">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              )}
            >
              <item.icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="border-t p-4">
        <p className="text-[10px] text-muted-foreground text-center">
          MoSPI / NSO / RBI
          <br />
          DGCA Passenger-Weighted
        </p>
      </div>
    </aside>
  );
}
