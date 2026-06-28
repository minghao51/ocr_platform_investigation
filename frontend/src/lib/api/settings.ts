import {
  API_BASE,
  AUTH_CHANGE_EVENT,
  getAccessHeaders,
  parseApiError,
} from './client';
import type { ExtractSettings, PdfAnalysis, QualityReport } from './types';

let _settingsCache: ExtractSettings | null = null;
let _settingsPromise: Promise<ExtractSettings> | null = null;

export async function getExtractSettings(): Promise<ExtractSettings> {
  if (_settingsCache) return _settingsCache;
  if (_settingsPromise) return _settingsPromise;

  _settingsPromise = (async () => {
    const response = await fetch(`${API_BASE}/extract/settings`, {
      headers: getAccessHeaders(),
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

if (typeof window !== 'undefined') {
  window.addEventListener(AUTH_CHANGE_EVENT, clearExtractSettingsCache);
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
