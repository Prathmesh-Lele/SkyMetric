"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface WindowData {
  window: number;
  label: string;
  index: number;
}

const windowLabels: Record<number, string> = {
  1: "Emergency",
  7: "Short-Horizon",
  15: "Headline Anchor",
  30: "Consumer Baseline",
  45: "Early Bird",
};

interface WindowCardsProps {
  windows: Record<string, number>;
  isLoading?: boolean;
}

export function WindowCards({ windows, isLoading }: WindowCardsProps) {
  const windowData: WindowData[] = [1, 7, 15, 30, 45].map((w) => ({
    window: w,
    label: windowLabels[w] || "",
    index: windows[String(w)] || 100,
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">
          Advance Booking Sub-Indices
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
          {windowData.map((w) => {
            const change = w.index - 100;
            const isAnchor = w.window === 15;
            return (
              <div
                key={w.window}
                className={cn(
                  "rounded-lg border p-3 text-center",
                  isAnchor && "border-primary bg-primary/5"
                )}
              >
                <div className="text-xs text-muted-foreground font-mono">
                  T+{w.window}
                </div>
                <div className="text-lg font-bold mt-1">{w.index.toFixed(1)}</div>
                <Badge
                  variant={isAnchor ? "default" : change >= 0 ? "destructive" : "secondary"}
                  className="text-[10px] mt-1"
                >
                  {change >= 0 ? "+" : ""}
                  {change.toFixed(1)}%
                </Badge>
                <div className="text-[10px] text-muted-foreground mt-1">
                  {w.label}
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
