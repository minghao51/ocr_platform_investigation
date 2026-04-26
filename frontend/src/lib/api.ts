const API_BASE = '/api';

// ============================================================================
// Error Types
// ============================================================================

export interface RateLimitError {
  detail: string;
  limit_type?: "daily" | "per_minute";
  retry_after?: number;
}

export function isRateLimitError(error: unknown): error is RateLimitError {
  if (typeof error !== 'object' || error === null) return false;
  return 'detail' in error && typeof error.detail === 'string' && error.detail.toLowerCase().includes("limit");
}

// ============================================================================
// Authentication Token Management
// ============================================================================

const AUTH_TOKEN_KEY = 'auth_token';
const USER_KEY = 'user';
const GUEST_TOKEN_KEY = 'guest_token';
export const AUTH_CHANGE_EVENT = 'ocr-platform-auth-change';

function notifyAuthChanged(): void {
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new Event(AUTH_CHANGE_EVENT));
  }
}

export interface AuthToken {
  access_token: string;
  token_type: string;
  user: {
    id: number;
    username: string;
    is_admin: boolean;
  };
}

/**
 * Get stored auth token
 */
export function getAuthToken(): string | null {
  const data = localStorage.getItem(AUTH_TOKEN_KEY);
  if (!data) return null;

  try {
    const parsed = JSON.parse(data) as AuthToken;
    return parsed.access_token;
  } catch {
    return null;
  }
}

/**
 * Get stored user info
 */
export function getCurrentUser(): AuthToken['user'] | null {
  const data = localStorage.getItem(AUTH_TOKEN_KEY);
  if (!data) return null;

  try {
    const parsed = JSON.parse(data) as AuthToken;
    return parsed.user;
  } catch {
    return null;
  }
}

export function getGuestToken(): string | null {
  return localStorage.getItem(GUEST_TOKEN_KEY);
}

export function setGuestToken(token: string): void {
  localStorage.setItem(GUEST_TOKEN_KEY, token);
}

/**
 * Set auth token (after login)
 */
export function setAuthToken(tokenData: AuthToken): void {
  localStorage.setItem(AUTH_TOKEN_KEY, JSON.stringify(tokenData));
  notifyAuthChanged();
}

/**
 * Clear auth token (logout)
 */
export function clearAuthToken(): void {
  localStorage.removeItem(AUTH_TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  notifyAuthChanged();
}

/**
 * Get auth headers for requests
 */
function getAuthHeaders(): Record<string, string> {
  const token = getAuthToken();
  if (!token) return {};

  return {
    'Authorization': `Bearer ${token}`
  };
}

function getAccessHeaders(): Record<string, string> {
  return {
    ...getAuthHeaders(),
    ...(getGuestToken() ? { 'X-Guest-Token': getGuestToken() as string } : {}),
  };
}

/**
 * Login with username and password
 */
export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse extends AuthToken {}

export async function login(credentials: LoginRequest): Promise<LoginResponse> {
  const response = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(credentials),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Login failed');
  }

  const data = await response.json() as LoginResponse;
  setAuthToken(data);
  return data;
}

/**
 * Logout (clears local token)
 */
export function logout(): void {
  clearAuthToken();
}

/**
 * Check if user is authenticated
 */
export function isAuthenticated(): boolean {
  return getAuthToken() !== null;
}

// ============================================================================
// API Types
// ============================================================================

export interface Provider {
  name: string;
  display_name: string;
  models: Model[];
  has_api_key: boolean;
  is_default?: boolean;
}

export interface Model {
  id: string;
  name: string;
  max_tokens?: number;
}

export interface Schema {
  id?: number;
  name: string;
  description?: string;
  definition: Record<string, unknown>;
  is_template?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface Job {
  job_id: number;
  file_name: string;
  file_type: string;
  status: 'pending' | 'processing' | 'success' | 'error';
  provider: string;
  model: string;
  schema_name: string;
  created_at?: string;
  updated_at?: string;
  processing_time?: number;
  processing_method?: 'vision' | 'text' | 'hybrid' | 'docling-parse' | 'docling-extract' | 'transcription';
  document_type?: string;
  correction_status?: 'uncorrected' | 'corrected';
  correction_summary?: {
    latest_correction_id: number;
    feedback_tags: string[];
    change_count: number;
  };
  hybrid_diagnostics?: {
    layout_pages: number;
    complex_pages: number[];
    timings: {
      layout_seconds: number;
      vision_seconds: number;
    };
    page_diagnostics?: Array<{
      page_number: number;
      block_count: number;
      image_count: number;
      table_count: number;
      is_complex: boolean;
    }>;
  };
  result?: unknown;
  error?: string;
  prompt_tokens?: number;
  completion_tokens?: number;
  estimated_cost?: number;
  metadata?: Record<string, unknown>;
  quality_score?: number;
  quality_checks?: QualityReport;
  preprocessing_applied?: string[];
}

export interface QualityCheck {
  name: string;
  severity: 'pass' | 'warn' | 'fail';
  score: number;
  value: number;
  threshold: number;
  message: string;
  auto_fixable: boolean;
  fix_recommendation: string;
}

export interface QualityReport {
  passed: boolean;
  overall_score: number;
  level: 'excellent' | 'good' | 'acceptable' | 'poor' | 'critical';
  checks: Record<string, QualityCheck>;
  recommendations: string[];
  auto_fixable_issues: string[];
  should_reject: boolean;
  rejection_reason: string;
}

export interface ProcessRequest {
  file_id: string;
  provider?: string;
  model?: string;
  schema_id?: number;
  schema_definition?: Record<string, unknown>;
  schema_mode?: 'raw' | 'auto-detect' | 'manual';
  prompt?: string;
  temperature?: number;
  max_tokens?: number;
  extraction_method?: 'auto' | 'text' | 'vision' | 'hybrid' | 'docling-parse' | 'docling-extract' | 'transcription';
  quality_threshold?: number;
  auto_preprocess?: boolean;
  skip_quality?: boolean;
}

export interface ProcessResponse {
  job_id: number;
  status: string;
  guest_token?: string;
}

export interface SchemaSuggestion {
  id: number;
  file_ids: string[];
  provider: string;
  model: string;
  document_type?: string;
  draft_name?: string;
  schema_definition: Record<string, unknown>;
  field_descriptions: Record<string, string>;
  rationale: string;
  confidence: number;
  status: string;
  created_at: string;
}

export interface JobCorrection {
  id: number;
  job_id: number;
  original_result: unknown;
  corrected_result: unknown;
  diff_summary: Array<{
    path: string;
    change_type: string;
    before: unknown;
    after: unknown;
  }>;
  feedback_tags: string[];
  notes?: string;
  reviewer_username?: string;
  created_at: string;
}

export interface AnalyticsOverview {
  total_jobs: number;
  successful_jobs: number;
  total_cost: number;
  avg_latency: number | null;
  corrected_jobs: number;
  success_rate: number;
  production_correction_rate: number;
  cost_per_successful_job: number;
  cost_per_corrected_job: number;
}

export interface UsageAnalytics {
  overview: AnalyticsOverview;
  provider_breakdown: Array<{
    provider: string;
    model: string;
    schema_name: string | null;
    total_jobs: number;
    successful_jobs: number;
    total_cost: number;
    avg_latency: number;
    corrected_jobs: number;
    success_rate: number;
    correction_rate: number;
    cost_per_successful_job: number;
    cost_per_corrected_job: number;
  }>;
  pipeline_distribution: Array<{
    processing_method: string;
    job_count: number;
    total_cost: number;
    avg_latency: number;
  }>;
  daily_trend: Array<{
    day: string;
    total_jobs: number;
    total_cost: number;
    corrected_jobs: number;
  }>;
  benchmark_accuracy: Array<{
    provider: string;
    model: string;
    benchmark_accuracy: number;
    cost_per_document: number;
    benchmark_latency: number;
    run_count: number;
  }>;
  correction_patterns: Array<{
    feedback_tag: string;
    frequency: number;
  }>;
}

// ============================================================================
// API Functions (with auth headers)
// ============================================================================

// Upload
export async function uploadFile(file: File): Promise<{ file_id: string; file_name: string; file_type: string; file_size: number; guest_token?: string }> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE}/upload/`, {
    method: 'POST',
    headers: getAccessHeaders(),
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Upload failed');
  }

  const data = await response.json() as { file_id: string; file_name: string; file_type: string; file_size: number; guest_token?: string };
  if (data.guest_token) {
    setGuestToken(data.guest_token);
  }
  return data;
}

// Process
export async function processDocument(request: ProcessRequest): Promise<ProcessResponse> {
  const response = await fetch(`${API_BASE}/process/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getAccessHeaders()
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    if (response.status === 429) {
      const error = await response.json() as RateLimitError;
      throw new Error(error.detail || 'Rate limit exceeded');
    }
    const error = await response.json();
    throw new Error(error.detail || 'Processing failed');
  }

  const data = await response.json() as ProcessResponse;
  if (data.guest_token) {
    setGuestToken(data.guest_token);
  }
  return data;
}

// Unified job status endpoint (replaces getJobStatus and pollJobStatus)
export async function getJobStatus(jobId: number): Promise<Job> {
  const response = await fetch(`${API_BASE}/process/status/${jobId}`, {
    headers: getAccessHeaders()
  });

  if (!response.ok) {
    throw await parseApiError(response, 'Failed to get job status');
  }

  return response.json();
}

// Schemas (read-only - may not require auth)
export async function listSchemas(isTemplate?: boolean): Promise<Schema[]> {
  const params = isTemplate !== undefined ? `?is_template=${isTemplate}` : '';
  const response = await fetch(`${API_BASE}/schemas/${params}`, {
    headers: getAuthHeaders()
  });
  if (!response.ok) {
    throw await parseApiError(response, 'Failed to load schemas');
  }
  return response.json();
}

export async function getTemplates(): Promise<Schema[]> {
  const response = await fetch(`${API_BASE}/schemas/templates`, {
    headers: getAuthHeaders()
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `Failed to fetch templates: ${response.statusText}`);
  }
  const data = await response.json();
  if (!Array.isArray(data)) {
    throw new Error(`Invalid response format: expected array, got ${typeof data}`);
  }
  // Templates don't have IDs - add synthetic ID for compatibility
  return data;
}

export async function getSchema(schemaId: number): Promise<Schema> {
  const response = await fetch(`${API_BASE}/schemas/${schemaId}`, {
    headers: getAuthHeaders()
  });

  if (!response.ok) {
    throw await parseApiError(response, 'Schema not found');
  }

  return response.json();
}

export async function createSchema(schema: Omit<Schema, 'id' | 'created_at' | 'updated_at'>): Promise<Schema> {
  const response = await fetch(`${API_BASE}/schemas/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders()
    },
    body: JSON.stringify(schema),
  });

  if (!response.ok) {
    throw await parseApiError(response, 'Failed to create schema');
  }

  return response.json();
}

export async function suggestSchema(
  fileIds: string[],
  provider?: string,
  model?: string,
): Promise<SchemaSuggestion> {
  const response = await fetch(`${API_BASE}/schemas/suggestions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getAccessHeaders(),
    },
    body: JSON.stringify({
      file_ids: fileIds,
      ...(provider ? { provider } : {}),
      ...(model ? { model } : {}),
    }),
  });

  if (!response.ok) {
    throw await parseApiError(response, 'Failed to suggest schema');
  }

  return response.json();
}

export async function listSchemaSuggestions(): Promise<SchemaSuggestion[]> {
  const response = await fetch(`${API_BASE}/schemas/suggestions/list`, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    throw await parseApiError(response, 'Failed to load schema suggestions');
  }

  return response.json();
}

// Jobs
export async function listJobs(status?: string, provider?: string, limit = 50, offset?: number): Promise<Job[]> {
  const params = new URLSearchParams();
  if (status) params.append('status', status);
  if (provider) params.append('provider', provider);
  params.append('limit', limit.toString());
  if (offset !== undefined) params.append('offset', offset.toString());

  const response = await fetch(`${API_BASE}/jobs/?${params}`, {
    headers: getAuthHeaders()
  });
  if (!response.ok) {
    throw await parseApiError(response, 'Failed to load jobs');
  }
  return response.json();
}

export async function getJob(jobId: number): Promise<Job> {
  const response = await fetch(`${API_BASE}/jobs/${jobId}`, {
    headers: getAuthHeaders()
  });

  if (!response.ok) {
    throw new Error('Job not found');
  }

  return response.json();
}

export async function listJobCorrections(jobId: number): Promise<JobCorrection[]> {
  const response = await fetch(`${API_BASE}/jobs/${jobId}/corrections`, {
    headers: getAccessHeaders()
  });

  if (!response.ok) {
    throw await parseApiError(response, 'Failed to load job corrections');
  }

  return response.json();
}

export async function createJobCorrection(
  jobId: number,
  correctedResult: Record<string, unknown>,
  feedbackTags: string[],
  notes?: string,
): Promise<JobCorrection> {
  const response = await fetch(`${API_BASE}/jobs/${jobId}/corrections`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders(),
    },
    body: JSON.stringify({
      corrected_result: correctedResult,
      feedback_tags: feedbackTags,
      notes,
    }),
  });

  if (!response.ok) {
    throw await parseApiError(response, 'Failed to save job correction');
  }

  return response.json();
}

export async function deleteJob(jobId: number): Promise<void> {
  const response = await fetch(`${API_BASE}/jobs/${jobId}`, {
    method: 'DELETE',
    headers: getAuthHeaders()
  });

  if (!response.ok) {
    throw new Error('Failed to delete job');
  }
}

// Providers
export async function listProviders(): Promise<Provider[]> {
  const response = await fetch(`${API_BASE}/providers/`, {
    headers: getAuthHeaders()
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `Failed to fetch providers: ${response.statusText}`);
  }
  const data = await response.json();
  if (!Array.isArray(data)) {
    if (data.error) {
      throw new Error(data.error);
    }
    throw new Error(`Invalid response format: expected array, got ${typeof data}`);
  }
  return data;
}

// ============================================================================
// Extract Settings
// ============================================================================

export interface ExtractSettings {
  providers: Provider[];
  extraction_methods: {
    id: string;
    name: string;
    description: string;
  }[];
  schema_modes: {
    id: string;
    label: string;
    available_for: string[] | null;
  }[];
  schema_templates: Record<string, Record<string, unknown>>;
  defaults: {
    temperature: { default: number; min: number; max: number; step: number };
    max_tokens: { default: number; min: number; max: number; step: number };
    quality_threshold: { default: number; min: number; max: number; step: number };
    auto_preprocess: { default: boolean };
    skip_quality: { default: boolean };
    prompt_max_length: number;
  };
  file_type_methods: Record<string, string>;
}

let _settingsCache: ExtractSettings | null = null;
let _settingsPromise: Promise<ExtractSettings> | null = null;

export async function getExtractSettings(): Promise<ExtractSettings> {
  if (_settingsCache) return _settingsCache;
  if (_settingsPromise) return _settingsPromise;

  _settingsPromise = (async () => {
    const response = await fetch(`${API_BASE}/extract/settings`, {
      headers: getAuthHeaders(),
    });
    if (!response.ok) {
      throw new Error(`Failed to fetch extract settings: ${response.statusText}`);
    }
    const data = await response.json();
    _settingsCache = data as ExtractSettings;
    _settingsPromise = null;
    return _settingsCache!;
  })();

  return _settingsPromise;
}

export function clearExtractSettingsCache(): void {
  _settingsCache = null;
  _settingsPromise = null;
}

// ============================================================================
// Benchmarks
// ============================================================================

export interface BenchmarkRun {
  id: number;
  dataset: string;
  provider: string;
  model: string;
  processing_method?: string;
  sample_count: number;
  overall_accuracy: number | null;
  avg_latency: number | null;
  total_cost: number | null;
  total_prompt_tokens: number;
  total_completion_tokens: number;
  success_rate: number | null;
  started_at: string | null;
  completed_at: string | null;
}

export interface BenchmarkResult {
  id: number;
  run_id: number;
  sample_index: number;
  file_path: string | null;
  accuracy_score: number;
  latency: number;
  cost: number;
  prompt_tokens: number;
  completion_tokens: number;
  peak_memory_mb?: number;
  expected_json: string | null;
  actual_json: string | null;
  field_scores: string | null;
  error_message: string | null;
}

export interface ModelComparison {
  run_id: number;
  provider: string;
  model: string;
  processing_method?: string;
  sample_count: number;
  overall_accuracy: number;
  avg_latency: number;
  total_cost: number;
  total_prompt_tokens: number;
  total_completion_tokens: number;
  success_rate: number | null;
  started_at: string | null;
}

async function parseApiError(response: Response, fallbackMessage: string): Promise<Error> {
  const contentType = response.headers.get('content-type') || '';

  if (contentType.includes('application/json')) {
    const payload = await response.json() as { detail?: string; message?: string };
    return new Error(payload.detail || payload.message || fallbackMessage);
  }

  const text = await response.text();
  return new Error(text || fallbackMessage);
}

export async function listBenchmarkRuns(
  limit = 50,
  dataset?: string,
  provider?: string
): Promise<BenchmarkRun[]> {
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

export async function compareModels(
  dataset = 'cord',
  limit = 20
): Promise<{ runs: ModelComparison[] }> {
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
    if (value) {
      params.append(key, value);
    }
  });

  const response = await fetch(`${API_BASE}/analytics/usage?${params.toString()}`, {
    headers: getAuthHeaders()
  });
  if (!response.ok) {
    throw await parseApiError(response, 'Failed to load usage analytics');
  }
  return response.json();
}

// ============================================================================
// Quality Gate
// ============================================================================

export async function checkFileQuality(fileId: string, estimatedDpi = 200): Promise<QualityReport> {
  const response = await fetch(`${API_BASE}/quality/check`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getAccessHeaders()
    },
    body: JSON.stringify({ file_id: fileId, estimated_dpi: estimatedDpi }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Quality check failed');
  }

  return response.json();
}

// ============================================================================
// PDF Analysis
// ============================================================================

export interface PdfAnalysis {
  file_id: string;
  has_text_layer: boolean;
  text_chars: number;
  suggested_methods: string[];
}

export async function analyzePdf(fileId: string): Promise<PdfAnalysis> {
  const response = await fetch(`${API_BASE}/upload/analyze-pdf/${fileId}`, {
    method: 'POST',
    headers: getAccessHeaders(),
  });
  if (!response.ok) {
    throw await parseApiError(response, 'PDF analysis failed');
  }
  return response.json();
}

// ============================================================================
// Benchmarked Models
// ============================================================================

export interface BenchmarkedModel {
  provider: string;
  model: string;
  run_id: number;
  accuracy: number | null;
  avg_latency: number | null;
  total_cost: number | null;
  sample_count: number | null;
  success_rate: number | null;
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

export async function checkUploadedImageQuality(file: File, estimatedDpi = 200): Promise<QualityReport> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('estimated_dpi', estimatedDpi.toString());

  const response = await fetch(`${API_BASE}/quality/check-upload`, {
    method: 'POST',
    headers: getAccessHeaders(),
    body: formData,
  });

  if (!response.ok) {
    throw await parseApiError(response, 'Quality check failed');
  }

  return response.json();
}
