"use client";

import { Button } from "@/components/ui/button";
import { CalendarIcon } from "lucide-react";
import { useMounted } from "@/lib/hooks";

interface DatePickerProps {
  date?: string;
  onDateChange: (date: string | undefined) => void;
  label?: string;
}

export function DatePicker({ date, onDateChange, label = "Pick a date" }: DatePickerProps) {
  const mounted = useMounted();
  // Compute after mount only — Date.now() differs between SSR and client
  const today = mounted ? new Date().toISOString().split("T")[0] : "";
  const thirtyDaysAgo = mounted
    ? new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)
        .toISOString()
        .split("T")[0]
    : "";

  return (
    <div className="flex items-center gap-2">
      <CalendarIcon className="h-4 w-4 text-muted-foreground" />
      <input
        type="date"
        value={date || ""}
        min={thirtyDaysAgo || undefined}
        max={today || undefined}
        onChange={(e) => onDateChange(e.target.value || undefined)}
        className="rounded-md border bg-background px-3 py-1.5 text-sm"
      />
      {date && (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onDateChange(undefined)}
        >
          Clear
        </Button>
      )}
    </div>
  );
}
