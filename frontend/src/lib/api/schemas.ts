import { API_BASE, getAuthHeaders, getAccessHeaders, parseApiError } from './client';
import type { Schema, SchemaSuggestion } from './types';

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
