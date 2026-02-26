const API_BASE = '/api';

// ============================================================================
// Authentication Token Management
// ============================================================================

const AUTH_TOKEN_KEY = 'auth_token';
const USER_KEY = 'user';

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

/**
 * Set auth token (after login)
 */
export function setAuthToken(tokenData: AuthToken): void {
  localStorage.setItem(AUTH_TOKEN_KEY, JSON.stringify(tokenData));
}

/**
 * Clear auth token (logout)
 */
export function clearAuthToken(): void {
  localStorage.removeItem(AUTH_TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
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
  processing_method?: 'vision' | 'text' | 'hybrid';
  result?: unknown;
  error?: string;
}

export interface ProcessRequest {
  file_id: string;
  provider: string;
  model: string;
  schema_id?: number;
  schema_definition?: Record<string, unknown>;
  prompt?: string;
  temperature?: number;
  max_tokens?: number;
  extraction_method?: 'auto' | 'text' | 'vision' | 'hybrid';
}

export interface ProcessResponse {
  job_id: number;
  status: string;
}

// ============================================================================
// API Functions (with auth headers)
// ============================================================================

// Upload
export async function uploadFile(file: File): Promise<{ file_id: string; file_name: string; file_type: string; file_size: number }> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE}/upload/`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Upload failed');
  }

  return response.json();
}

// Process
export async function processDocument(request: ProcessRequest): Promise<ProcessResponse> {
  const response = await fetch(`${API_BASE}/process/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders()
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Processing failed');
  }

  return response.json();
}

// Text Extraction
export async function processTextDocument(
  fileId: string,
  provider: string,
  model: string,
  schemaId?: number
): Promise<{ job_id: number }> {
  const response = await fetch(`${API_BASE}/text/process`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders()
    },
    body: JSON.stringify({
      file_id: fileId,
      provider,
      model,
      schema_id: schemaId
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to process text document');
  }

  return response.json();
}

// Unified job status endpoint (replaces getJobStatus and pollJobStatus)
export async function getJobStatus(jobId: number): Promise<Job> {
  const response = await fetch(`${API_BASE}/jobs/${jobId}`, {
    headers: getAuthHeaders()
  });

  if (!response.ok) {
    throw new Error('Failed to get job status');
  }

  return response.json();
}

// Schemas (read-only - may not require auth)
export async function listSchemas(isTemplate?: boolean): Promise<Schema[]> {
  const params = isTemplate !== undefined ? `?is_template=${isTemplate}` : '';
  const response = await fetch(`${API_BASE}/schemas${params}`, {
    headers: getAuthHeaders()
  });
  return response.json();
}

export async function getTemplates(): Promise<Schema[]> {
  const response = await fetch(`${API_BASE}/schemas/templates`, {
    headers: getAuthHeaders()
  });
  return response.json();
}

export async function getSchema(schemaId: number): Promise<Schema> {
  const response = await fetch(`${API_BASE}/schemas/${schemaId}`, {
    headers: getAuthHeaders()
  });

  if (!response.ok) {
    throw new Error('Schema not found');
  }

  return response.json();
}

export async function createSchema(schema: Omit<Schema, 'id' | 'created_at' | 'updated_at'>): Promise<Schema> {
  const response = await fetch(`${API_BASE}/schemas`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders()
    },
    body: JSON.stringify(schema),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create schema');
  }

  return response.json();
}

// Jobs
export async function listJobs(status?: string, provider?: string, limit = 50): Promise<Job[]> {
  const params = new URLSearchParams();
  if (status) params.append('status', status);
  if (provider) params.append('provider', provider);
  params.append('limit', limit.toString());

  const response = await fetch(`${API_BASE}/jobs?${params}`, {
    headers: getAuthHeaders()
  });
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
  return response.json();
}
