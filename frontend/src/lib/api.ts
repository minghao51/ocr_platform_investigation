const API_BASE = '/api';

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
  definition: Record<string, any>;
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
  created_at: string;
  updated_at: string;
  processing_time?: number;
  processing_method?: 'vision' | 'text';
  result?: any;
  error?: string;
}

export interface ProcessRequest {
  file_id: string;
  provider: string;
  model: string;
  schema_id?: number;
  schema_definition?: Record<string, any>;
  prompt?: string;
  temperature?: number;
  max_tokens?: number;
}

export interface ProcessResponse {
  job_id: number;
  status: string;
}

// Upload
export async function uploadFile(file: File): Promise<{ file_id: string; file_name: string; file_type: string; file_path: string; file_size: number }> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE}/upload/`, {
    method: 'POST',
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
    headers: { 'Content-Type': 'application/json' },
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

export async function getJobStatus(jobId: number): Promise<Job> {
  const response = await fetch(`${API_BASE}/process/status/${jobId}`);

  if (!response.ok) {
    throw new Error('Failed to get job status');
  }

  return response.json();
}

export async function pollJobStatus(jobId: number): Promise<Job> {
  const response = await fetch(`${API_BASE}/text/status/${jobId}`);

  if (!response.ok) {
    throw new Error('Failed to get job status');
  }

  return response.json();
}

// Schemas
export async function listSchemas(isTemplate?: boolean): Promise<Schema[]> {
  const params = isTemplate !== undefined ? `?is_template=${isTemplate}` : '';
  const response = await fetch(`${API_BASE}/schemas${params}`);
  return response.json();
}

export async function getTemplates(): Promise<Schema[]> {
  const response = await fetch(`${API_BASE}/schemas/templates`);
  return response.json();
}

export async function getSchema(schemaId: number): Promise<Schema> {
  const response = await fetch(`${API_BASE}/schemas/${schemaId}`);
  
  if (!response.ok) {
    throw new Error('Schema not found');
  }
  
  return response.json();
}

export async function createSchema(schema: Omit<Schema, 'id' | 'created_at' | 'updated_at'>): Promise<Schema> {
  const response = await fetch(`${API_BASE}/schemas`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
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
  
  const response = await fetch(`${API_BASE}/jobs?${params}`);
  return response.json();
}

export async function getJob(jobId: number): Promise<Job> {
  const response = await fetch(`${API_BASE}/jobs/${jobId}`);
  
  if (!response.ok) {
    throw new Error('Job not found');
  }
  
  return response.json();
}

export async function deleteJob(jobId: number): Promise<void> {
  const response = await fetch(`${API_BASE}/jobs/${jobId}`, {
    method: 'DELETE',
  });
  
  if (!response.ok) {
    throw new Error('Failed to delete job');
  }
}

// Providers
export async function listProviders(): Promise<Provider[]> {
  const response = await fetch(`${API_BASE}/providers/`);
  return response.json();
}
