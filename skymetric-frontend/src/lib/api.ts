const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface DailyIndexResponse {
  date: string;
  headline_index: number;
  sector_indices: Record<string, number>;
  window_indices: Record<string, number>;
  base_date: string;
}

export interface SectorIndicesResponse {
  date: string;
  sectors: Record<string, number>;
}

export interface HeatmapResponse {
  corridors: string[];
  dates: string[];
  matrix: number[][];
  unit: string;
  source?: string;
}

export interface Carrier {
  name: string;
  market_share: number;
}

export interface CarriersResponse {
  carriers: Carrier[];
}

export interface ElasticityResponse {
  date: string;
  advance_windows: number[];
  curves: Record<string, Record<string, number>>;
  anchor_window: number;
}

export interface HealthResponse {
  status: string;
  service: string;
}

export interface ScraperStatus {
  is_running: boolean;
  total_jobs: number;
  completed_jobs: number;
  failed_jobs: number;
  last_run: string | null;
  quotes_collected: number;
  sources_checked: number;
  avg_latency_ms: number;
  backoff_triggers: number;
  supported_sources: string[];
  active_sources: string[];
}

export interface ScraperRunResponse {
  message?: string;
  error?: string;
  origin?: string;
  destination?: string;
  date?: string;
  status?: ScraperStatus;
}

export interface BacktestResponse {
  dates: string[];
  skymetric_index: number[];
  dgca_benchmark: number[];
  mape: number;
  rmse: number;
  days_compared: number;
  cpi?: CpiData;
  note: string;
}

export interface CpiDataPoint {
  year: number;
  month: string;
  index_value: number;
  inflation_pct: number | null;
  series: string;
}

export interface CpiData {
  cpi_general: CpiDataPoint[];
  cpi_transport: CpiDataPoint[];
  cpi_air_transport: CpiDataPoint[];
  source: string;
  base_year: number;
  note: string;
}

export interface CpiResponse {
  series: string;
  data: CpiDataPoint[];
  source: string;
  note: string;
}

export interface SuperlativeResponse {
  date: string;
  base_date: string;
  fisher: number;
  paasche: number;
  torqvist: number;
  laspeyres: number;
  jevons: number;
  cpi_bps: {
    fare_change_pct: number;
    bps_transport: number;
    bps_headline: number;
    transport_weight: number;
  };
}

export interface Anomaly {
  origin: string;
  destination: string;
  carrier: string;
  flight_number: string;
  fare: number;
  median_fare: number;
  z_score: number;
  direction: string;
  advance_window_days: number;
  timestamp: string;
}

export interface AnomaliesResponse {
  date: string;
  threshold: number;
  count: number;
  anomalies: Anomaly[];
}

export interface DataTrustResponse {
  date: string;
  score: number;
  grade: string;
  dimensions: Record<string, number>;
  details: {
    total_records: number;
    unique_sources: number;
    unique_corridors: number;
    unique_carriers: number;
    anomaly_count: number;
    anomaly_ratio: number;
  };
}

async function fetchApi<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store", ...init });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export const api = {
  health: () => fetchApi<HealthResponse>("/api/v1/health"),
  dailyIndex: (date?: string) =>
    fetchApi<DailyIndexResponse>(
      `/api/v1/index/daily${date ? `?target_date=${date}` : ""}`
    ),
  sectorIndices: (date?: string) =>
    fetchApi<SectorIndicesResponse>(
      `/api/v1/index/sectors${date ? `?target_date=${date}` : ""}`
    ),
  heatmap: (days = 30, date?: string) =>
    fetchApi<HeatmapResponse>(
      `/api/v1/routes/heatmap?days=${days}${date ? `&target_date=${date}` : ""}`
    ),
  carriers: () => fetchApi<CarriersResponse>("/api/v1/routes/carriers"),
  elasticity: (date?: string) =>
    fetchApi<ElasticityResponse>(
      `/api/v1/elasticity/${date ? `?target_date=${date}` : ""}`
    ),
  scraperStatus: () => fetchApi<ScraperStatus>("/api/v1/scraper/status"),
  scraperRun: async (origin?: string, destination?: string, date?: string) => {
    const params = new URLSearchParams();
    if (origin) params.set("origin", origin);
    if (destination) params.set("destination", destination);
    if (date) params.set("date", date);
    const qs = params.toString();
    return fetchApi<ScraperRunResponse>(
      `/api/v1/scraper/run${qs ? `?${qs}` : ""}`,
      {
        method: "POST",
        headers: { "X-API-Key": "skymetric-demo-key" },
      }
    );
  },
  backtest: () => fetchApi<BacktestResponse>("/api/v1/backtest/compare"),
  cpiAll: () => fetchApi<{ cpi_general: CpiDataPoint[]; cpi_transport: CpiDataPoint[]; cpi_air_transport: CpiDataPoint[]; source: string; base_year: number; note: string }>("/api/v1/cpi"),
  cpiAirTransport: () => fetchApi<CpiResponse>("/api/v1/cpi/air-transport"),
  cpiGeneral: () => fetchApi<CpiResponse>("/api/v1/cpi/general"),
  superlative: (date?: string) =>
    fetchApi<SuperlativeResponse>(
      `/api/v1/analytics/superlative${date ? `?target_date=${date}` : ""}`
    ),
  anomalies: (date?: string, threshold?: number) =>
    fetchApi<AnomaliesResponse>(
      `/api/v1/analytics/anomalies${date ? `?target_date=${date}` : ""}${threshold ? `&threshold=${threshold}` : ""}`
    ),
  dataTrust: (date?: string) =>
    fetchApi<DataTrustResponse>(
      `/api/v1/analytics/data-trust${date ? `?target_date=${date}` : ""}`
    ),
  exportCsv: (date?: string, days?: number) =>
    `${API_BASE}/api/v1/analytics/export/csv${date ? `?target_date=${date}` : ""}${days ? `&days=${days}` : ""}`,
};
