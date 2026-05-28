import { API_BASE, setAuthToken, clearAuthToken, getAuthHeaders, parseApiError } from './client';
import type { LoginRequest, LoginResponse } from './types';

export async function login(credentials: LoginRequest): Promise<LoginResponse> {
  const response = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Login-Username': credentials.username,
    },
    body: JSON.stringify(credentials),
  });

  if (!response.ok) {
    throw await parseApiError(response, 'Login failed');
  }

  const data = await response.json() as LoginResponse;
  setAuthToken(data);
  return data;
}

export async function logout(): Promise<void> {
  try {
    await fetch(`${API_BASE}/auth/logout`, {
      method: 'POST',
      headers: {
        ...getAuthHeaders(),
      },
    });
  } finally {
    clearAuthToken();
  }
}
