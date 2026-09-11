"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface SectorTableProps {
  sectors: Record<string, number>;
  isLoading?: boolean;
}

const corridorMeta: Record<string, { passengers: string; classification: string }> = {
  "DEL-BOM": { passengers: "18.4M", classification: "Metro Trunk" },
  "DEL-BLR": { passengers: "14.2M", classification: "Metro Trunk" },
  "BOM-BLR": { passengers: "12.1M", classification: "Metro Trunk" },
  "DEL-CCU": { passengers: "10.5M", classification: "Metro Trunk" },
  "DEL-HYD": { passengers: "8.3M", classification: "Metro Trunk" },
  "BOM-MAA": { passengers: "6.7M", classification: "Metro Trunk" },
  "BLR-HYD": { passengers: "5.8M", classification: "Metro Trunk" },
  "DEL-MAA": { passengers: "5.2M", classification: "Metro Trunk" },
  "DEL-IXS": { passengers: "5.8M", classification: "Regional Thin" },
  "DEL-DHM": { passengers: "3.0M", classification: "Regional Thin" },
};

export function SectorTable({ sectors, isLoading }: SectorTableProps) {
  const rows = Object.entries(sectors)
    .sort(([, a], [, b]) => b - a)
    .map(([route, index]) => ({
      route,
      index,
      meta: corridorMeta[route] || { passengers: "—", classification: "—" },
    }));

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">
          Corridor Index Breakdown
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Route</TableHead>
              <TableHead>Classification</TableHead>
              <TableHead className="text-right">Passengers</TableHead>
              <TableHead className="text-right">Index</TableHead>
              <TableHead className="text-right">Change</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((row) => {
              const change = row.index - 100;
              return (
                <TableRow key={row.route}>
                  <TableCell className="font-mono font-medium">
                    {row.route}
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline" className="text-[10px]">
                      {row.meta.classification}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right text-muted-foreground">
                    {row.meta.passengers}
                  </TableCell>
                  <TableCell className="text-right font-mono font-medium">
                    {row.index.toFixed(2)}
                  </TableCell>
                  <TableCell className="text-right">
                    <Badge
                      variant={change >= 0 ? "destructive" : "secondary"}
                      className="text-[10px]"
                    >
                      {change >= 0 ? "+" : ""}
                      {change.toFixed(1)}%
                    </Badge>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
