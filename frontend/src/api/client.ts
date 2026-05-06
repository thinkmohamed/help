export interface AOI {
  id: string;
  name: string;
  description: string | null;
  geometry: GeoJSON.Polygon;
  bbox: [number, number, number, number];
  created_at: number;
}

export interface Source {
  id: string;
  provider: string;
  label: string;
  bands: string[];
  category: string;
  authenticated: boolean;
}

export interface JobProgressEvent {
  ts: number;
  stage: string;
  status: string;
  [key: string]: unknown;
}

export interface Job {
  id: string;
  aoi_id: string;
  sources: string[];
  status: 'queued' | 'running' | 'completed' | 'failed';
  progress: JobProgressEvent[];
  created_at: number;
  started_at: number | null;
  finished_at: number | null;
  error: string | null;
}

export interface TargetSummary {
  mean_prob: number;
  max_prob: number;
  n_clusters: number;
  high_confidence_px: number;
}

export interface TargetCluster {
  id: number;
  centroid_yx: [number, number];
  size_px: number;
  mean_score: number;
}

export interface TargetResult {
  key: string;
  label_en: string;
  label_ar: string;
  color: string;
  summary: TargetSummary;
  clusters: TargetCluster[];
  heatmap_png: string;
}

export interface JobResult {
  aoi: AOI;
  grid: [number, number];
  sources_used: { source_id: string; provider: string; band: string; is_synthetic: boolean }[];
  feature_names: string[];
  n_features: number;
  targets: Record<string, TargetResult>;
  timings: Record<string, number>;
}

const BASE = '';

async function req<T>(method: string, path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${method} ${path} -> ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () => req<{ status: string; version: string }>('GET', '/api/health'),
  listSources: () => req<Source[]>('GET', '/api/sources'),
  listAOI: () => req<AOI[]>('GET', '/api/aoi'),
  createAOI: (name: string, geometry: GeoJSON.Polygon, description?: string) =>
    req<AOI>('POST', '/api/aoi', { name, geometry, description }),
  deleteAOI: (id: string) => req<{ deleted: boolean }>('DELETE', `/api/aoi/${id}`),
  listJobs: () => req<Job[]>('GET', '/api/jobs'),
  getJob: (id: string) => req<Job>('GET', `/api/jobs/${id}`),
  createJob: (aoi_id: string, sources: string[], grid: [number, number] = [128, 128]) =>
    req<Job>('POST', '/api/jobs', { aoi_id, sources, grid, use_torch: true }),
  getResult: (id: string) => req<JobResult>('GET', `/api/results/${id}`),
};
