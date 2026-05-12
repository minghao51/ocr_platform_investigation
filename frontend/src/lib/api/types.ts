export interface RateLimitError {
  detail: string;
  limit_type?: "daily" | "per_minute";
  retry_after?: number;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: { id: number; username: string; is_admin: boolean };
}

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
    timings: { layout_seconds: number; vision_seconds: number };
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
  diff_summary: Array<{ path: string; change_type: string; before: unknown; after: unknown }>;
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

export interface ExtractSettings {
  providers: Provider[];
  extraction_methods: { id: string; name: string; description: string }[];
  schema_modes: { id: string; label: string; available_for: string[] | null }[];
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

export interface PdfAnalysis {
  file_id: string;
  has_text_layer: boolean;
  text_chars: number;
  suggested_methods: string[];
}
