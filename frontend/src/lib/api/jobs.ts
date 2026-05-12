import { API_BASE, getAccessHeaders, getAuthHeaders, setGuestToken, parseApiError } from './client';
import type { ProcessRequest, ProcessResponse, Job, JobCorrection, RateLimitError } from './types';

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

export async function getJobStatus(jobId: number): Promise<Job> {
  const response = await fetch(`${API_BASE}/process/status/${jobId}`, {
    headers: getAccessHeaders()
  });
  if (!response.ok) {
    throw await parseApiError(response, 'Failed to get job status');
  }
  return response.json();
}

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

export async function deleteJob(jobId: number): Promise<void> {
  const response = await fetch(`${API_BASE}/jobs/${jobId}`, {
    method: 'DELETE',
    headers: getAuthHeaders()
  });
  if (!response.ok) {
    throw new Error('Failed to delete job');
  }
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
