"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useSuperlative, useAnomalies, useDataTrust } from "@/lib/hooks";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

export default function AnalyticsPage() {
  const { data: superlative, isLoading: loadingSuper } = useSuperlative();
  const { data: anomalies, isLoading: loadingAnom } = useAnomalies();
  const { data: trust, isLoading: loadingTrust } = useDataTrust();

  if (loadingSuper || loadingAnom || loadingTrust) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-64" />
        <div className="grid gap-4 md:grid-cols-3">
          <Skeleton className="h-[200px]" />
          <Skeleton className="h-[200px]" />
          <Skeleton className="h-[200px]" />
        </div>
        <Skeleton className="h-[300px] w-full" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Advanced Analytics</h1>
        <p className="text-sm text-muted-foreground">
          Superlative indices, anomaly detection & data trust scoring
        </p>
      </div>

      {/* Superlative Indices */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">
            Superlative Index Comparison
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-5">
            {superlative && [
              { name: "Fisher Ideal", value: superlative.fisher, desc: "Geometric mean of L & P" },
              { name: "Paasche", value: superlative.paasche, desc: "Current-period weights" },
              { name: "Tornqvist", value: superlative.torqvist, desc: "Symmetric share weights" },
              { name: "Laspeyres", value: superlative.laspeyres, desc: "Fixed base weights" },
              { name: "Jevons", value: superlative.jevons, desc: "Geometric mean" },
            ].map((idx) => (
              <div key={idx.name} className="text-center p-4 rounded-lg border bg-card">
                <div className="text-2xl font-bold font-mono">
                  {idx.value.toFixed(2)}
                </div>
                <div className="text-xs font-medium mt-1">{idx.name}</div>
                <div className="text-[10px] text-muted-foreground">{idx.desc}</div>
              </div>
            ))}
          </div>
          {superlative?.cpi_bps && (
            <div className="mt-4 p-3 rounded-lg bg-muted/30 text-sm">
              <span className="font-medium">CPI Transmission:</span>{" "}
              <span className="font-mono">
                +{superlative.cpi_bps.bps_transport} bps (Transport) / +{superlative.cpi_bps.bps_headline} bps (Headline)
              </span>
              <span className="text-muted-foreground ml-2">
                (Transport weight: {(superlative.cpi_bps.transport_weight * 100).toFixed(2)}%)
              </span>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Data Trust Scorecard */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">
            Data Trust Scorecard
          </CardTitle>
        </CardHeader>
        <CardContent>
          {trust && (
            <div className="grid gap-6 md:grid-cols-2">
              <div className="flex flex-col items-center justify-center p-6">
                <div className="text-6xl font-bold font-mono">
                  {trust.score}
                </div>
                <div className="text-sm text-muted-foreground mt-1">out of 100</div>
                <Badge
                  variant={trust.score >= 80 ? "default" : trust.score >= 60 ? "secondary" : "destructive"}
                  className="mt-2 text-lg"
                >
                  Grade: {trust.grade}
                </Badge>
              </div>
              <div className="space-y-2">
                {Object.entries(trust.dimensions).map(([key, value]) => (
                  <div key={key} className="flex items-center gap-3">
                    <div className="text-xs w-32 text-muted-foreground capitalize">
                      {key.replace(/_/g, " ")}
                    </div>
                    <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all"
                        style={{
                          width: `${(value / (key === "volume_adequacy" ? 10 : 15)) * 100}%`,
                          backgroundColor:
                            value / (key === "volume_adequacy" ? 10 : 15) >= 0.7
                              ? "var(--chart-3)"
                              : value / (key === "volume_adequacy" ? 10 : 15) >= 0.4
                              ? "var(--chart-4)"
                              : "var(--destructive)",
                        }}
                      />
                    </div>
                    <div className="text-xs font-mono w-8 text-right">{value}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
          {trust?.details && (
            <div className="mt-4 grid grid-cols-3 gap-4 text-center text-sm">
              <div>
                <div className="font-mono font-bold">{trust.details.total_records}</div>
                <div className="text-xs text-muted-foreground">Records</div>
              </div>
              <div>
                <div className="font-mono font-bold">{trust.details.unique_sources}</div>
                <div className="text-xs text-muted-foreground">Sources</div>
              </div>
              <div>
                <div className="font-mono font-bold">{trust.details.anomaly_count}</div>
                <div className="text-xs text-muted-foreground">Anomalies</div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Anomaly Detection */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">
            Fare Anomaly Detection ({anomalies?.count || 0} found)
          </CardTitle>
        </CardHeader>
        <CardContent>
          {anomalies && anomalies.anomalies.length > 0 ? (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Route</TableHead>
                    <TableHead>Carrier</TableHead>
                    <TableHead className="text-right">Fare</TableHead>
                    <TableHead className="text-right">Median</TableHead>
                    <TableHead className="text-right">Z-Score</TableHead>
                    <TableHead>Direction</TableHead>
                    <TableHead className="text-right">Window</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {anomalies.anomalies.slice(0, 20).map((a, i) => (
                    <TableRow key={i}>
                      <TableCell className="font-mono font-medium">
                        {a.origin}-{a.destination}
                      </TableCell>
                      <TableCell>{a.carrier}</TableCell>
                      <TableCell className="text-right font-mono">
                        ₹{a.fare.toLocaleString("en-IN")}
                      </TableCell>
                      <TableCell className="text-right font-mono text-muted-foreground">
                        ₹{a.median_fare.toLocaleString("en-IN")}
                      </TableCell>
                      <TableCell className="text-right font-mono">
                        <span className={a.z_score > 0 ? "text-red-500" : "text-emerald-500"}>
                          {a.z_score > 0 ? "+" : ""}{a.z_score}
                        </span>
                      </TableCell>
                      <TableCell>
                        <Badge variant={a.direction === "spike" ? "destructive" : "default"}>
                          {a.direction === "spike" ? "↑ Spike" : "↓ Drop"}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">T+{a.advance_window_days}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : (
            <p className="text-center text-muted-foreground py-8">
              No anomalies detected in current data.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
