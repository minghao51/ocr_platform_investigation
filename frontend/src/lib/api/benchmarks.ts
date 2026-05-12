import { API_BASE, getAuthHeaders, parseApiError } from './client';
import type { BenchmarkRun, BenchmarkResult, ModelComparison, BenchmarkedModel, UsageAnalytics } from './types';

export async function listBenchmarkRuns(limit = 50, dataset?: string, provider?: string): Promise<BenchmarkRun[]> {
  const params = new URLSearchParams();
  params.append('limit', limit.toString());
  if (dataset) params.append('dataset', dataset);
  if (provider) params.append('provider', provider);

  const response = await fetch(`${API_BASE}/benchmarks/runs?${params}`, {
    headers: getAuthHeaders()
  });
  if (!response.ok) {
    throw await parseApiError(response, 'Failed to load benchmark runs');
  }
  return response.json();
}

export async function getBenchmarkRun(runId: number): Promise<BenchmarkRun> {
  const response = await fetch(`${API_BASE}/benchmarks/runs/${runId}`, {
    headers: getAuthHeaders()
  });
  if (!response.ok) {
    throw await parseApiError(response, 'Benchmark run not found');
  }
  return response.json();
}

export async function getBenchmarkResults(runId: number): Promise<BenchmarkResult[]> {
  const response = await fetch(`${API_BASE}/benchmarks/runs/${runId}/results`, {
    headers: getAuthHeaders()
  });
  if (!response.ok) {
    throw await parseApiError(response, 'Failed to load benchmark results');
  }
  return response.json();
}

export async function compareModels(dataset = 'cord', limit = 20): Promise<{ runs: ModelComparison[] }> {
  const params = new URLSearchParams();
  params.append('dataset', dataset);
  params.append('limit', limit.toString());

  const response = await fetch(`${API_BASE}/benchmarks/compare?${params}`, {
    headers: getAuthHeaders()
  });
  if (!response.ok) {
    throw await parseApiError(response, 'Failed to load benchmark comparison');
  }
  return response.json();
}

export async function getBenchmarkedModels(): Promise<BenchmarkedModel[]> {
  const response = await fetch(`${API_BASE}/benchmarks/models`, {
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    return [];
  }
  return response.json();
}

export async function getUsageAnalytics(filters?: {
  date_from?: string;
  date_to?: string;
  provider?: string;
  model?: string;
  schema_name?: string;
  processing_method?: string;
  document_type?: string;
}): Promise<UsageAnalytics> {
  const params = new URLSearchParams();
  Object.entries(filters || {}).forEach(([key, value]) => {
    if (value) params.append(key, value);
  });

  const response = await fetch(`${API_BASE}/analytics/usage?${params.toString()}`, {
    headers: getAuthHeaders()
  });
  if (!response.ok) {
    throw await parseApiError(response, 'Failed to load usage analytics');
  }
  return response.json();
}
