const API_BASE = '/api';
const AUTH_TOKEN_KEY = 'auth_token';
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
  user: { id: number; username: string; is_admin: boolean };
}

export function getAuthToken(): string | null {
  const data = localStorage.getItem(AUTH_TOKEN_KEY);
  if (!data) return null;
  try {
    return (JSON.parse(data) as AuthToken).access_token;
  } catch {
    return null;
  }
}

export function getCurrentUser(): AuthToken['user'] | null {
  const data = localStorage.getItem(AUTH_TOKEN_KEY);
  if (!data) return null;
  try {
    return (JSON.parse(data) as AuthToken).user;
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

export function setAuthToken(tokenData: AuthToken): void {
  localStorage.setItem(AUTH_TOKEN_KEY, JSON.stringify(tokenData));
  notifyAuthChanged();
}

export function clearAuthToken(): void {
  localStorage.removeItem(AUTH_TOKEN_KEY);
  notifyAuthChanged();
}

export function isAuthenticated(): boolean {
  return getAuthToken() !== null;
}

export function getAuthHeaders(): Record<string, string> {
  const token = getAuthToken();
  if (!token) return {};
  return { Authorization: `Bearer ${token}` };
}

export function getAccessHeaders(): Record<string, string> {
  return {
    ...getAuthHeaders(),
    ...(getGuestToken() ? { 'X-Guest-Token': getGuestToken() as string } : {}),
  };
}

export async function parseApiError(response: Response, fallbackMessage: string): Promise<Error> {
  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    const payload = await response.json() as { detail?: string; message?: string };
    return new Error(payload.detail || payload.message || fallbackMessage);
  }
  const text = await response.text();
  return new Error(text || fallbackMessage);
}

export { API_BASE };
