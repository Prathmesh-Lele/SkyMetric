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
  scraperRun: (origin?: string, destination?: string, date?: string) =>
    fetchApi<ScraperRunResponse>(
      `/api/v1/scraper/run${origin ? `?origin=${origin}` : ""}${destination ? `&destination=${destination}` : ""}${date ? `&date=${date}` : ""}`,
      { method: "POST" }
    ),
};
