import { afterEach, describe, expect, it } from 'vitest';
import {
  clearAuthToken,
  getAuthHeaders,
  getAuthToken,
  setAuthToken,
  setGuestToken,
  getAccessHeaders,
  parseApiError,
} from './client';

describe('api client auth storage', () => {
  afterEach(() => {
    localStorage.clear();
  });

  it('stores and reads auth token', () => {
    setAuthToken({
      access_token: 'token-123',
      token_type: 'bearer',
      user: { id: 1, username: 'u', is_admin: false },
    });

    expect(getAuthToken()).toBe('token-123');
    expect(getAuthHeaders()).toEqual({ Authorization: 'Bearer token-123' });
  });

  it('clears auth token and leaves empty auth headers', () => {
    setAuthToken({
      access_token: 'token-123',
      token_type: 'bearer',
      user: { id: 1, username: 'u', is_admin: false },
    });
    clearAuthToken();

    expect(getAuthToken()).toBeNull();
    expect(getAuthHeaders()).toEqual({});
  });

  it('combines guest and auth access headers', () => {
    setAuthToken({
      access_token: 'token-123',
      token_type: 'bearer',
      user: { id: 1, username: 'u', is_admin: false },
    });
    setGuestToken('guest-abc');

    expect(getAccessHeaders()).toEqual({
      Authorization: 'Bearer token-123',
      'X-Guest-Token': 'guest-abc',
    });
  });

  it('falls back when a json error response cannot be parsed', async () => {
    const response = new Response('{invalid json', {
      status: 500,
      headers: { 'content-type': 'application/json' },
    });

    await expect(parseApiError(response, 'Fallback error')).resolves.toEqual(
      new Error('Fallback error'),
    );
  });
});
