"use client";

import { ThemeToggle } from "./theme-toggle";
import { Activity, Menu } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { Sidebar } from "./sidebar";

export function Header() {
  return (
    <header className="sticky top-0 z-40 flex h-14 items-center gap-4 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 px-4 md:px-6">
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

      <div className="flex-1" />

      <div className="flex items-center gap-2">
        <span className="hidden sm:inline text-xs text-muted-foreground font-mono">
          India Airfare Price Observatory
        </span>
        <ThemeToggle />
      </div>
    </header>
  );
}
