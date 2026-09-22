"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function ApiExplorerPage() {
  const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">API Explorer</h1>
        <p className="text-sm text-muted-foreground">
          Interactive OpenAPI/Swagger console for SkyMetric airfare index
          queries, analytics, and scraper controls
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">
            FastAPI Swagger UI
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="rounded-lg border overflow-hidden">
            <iframe
              src={`${apiBase}/docs`}
              className="w-full h-[700px] border-0"
              title="API Explorer"
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">
            Available Endpoints
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {[
              {
                method: "GET",
                path: "/api/v1/health",
                desc: "Health check",
              },
              {
                method: "GET",
                path: "/api/v1/index/daily",
                desc: "National SkyMetric for a date",
              },
              {
                method: "GET",
                path: "/api/v1/index/sectors",
                desc: "Per-corridor index breakdown",
              },
              {
                method: "GET",
                path: "/api/v1/routes/heatmap",
                desc: "Sector × time heatmap",
              },
              {
                method: "GET",
                path: "/api/v1/routes/carriers",
                desc: "Carrier market share data",
              },
              {
                method: "GET",
                path: "/api/v1/elasticity",
                desc: "Advance-purchase curves",
              },
            ].map((ep) => (
              <div
                key={ep.path}
                className="rounded-lg border p-3 flex items-start gap-3"
              >
                <span className="inline-flex items-center rounded-md bg-emerald-50 px-2 py-1 text-xs font-medium text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300 shrink-0">
                  {ep.method}
                </span>
                <div className="min-w-0">
                  <code className="text-xs font-mono break-all">{ep.path}</code>
                  <p className="text-[11px] text-muted-foreground mt-0.5">
                    {ep.desc}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
