import { afterEach, describe, expect, it } from 'vitest';
import {
  AUTH_CHANGE_EVENT,
  clearAuthToken,
  getAuthHeaders,
  getCurrentUser,
  getAuthToken,
  isAuthenticated,
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
    expect(getCurrentUser()).toEqual({ id: 1, username: 'u', is_admin: false });
    expect(isAuthenticated()).toBe(true);
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
    expect(getCurrentUser()).toBeNull();
    expect(isAuthenticated()).toBe(false);
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

  it('returns null when stored auth token json is invalid', () => {
    localStorage.setItem('auth_token', '{not json');

    expect(getAuthToken()).toBeNull();
    expect(getCurrentUser()).toBeNull();
    expect(isAuthenticated()).toBe(false);
  });

  it('uses response text for non-json errors', async () => {
    const response = new Response('Text failure', {
      status: 500,
      headers: { 'content-type': 'text/plain' },
    });

    await expect(parseApiError(response, 'Fallback error')).resolves.toEqual(
      new Error('Text failure'),
    );
  });

  it('dispatches auth change event on set and clear', () => {
    let events = 0;
    window.addEventListener(AUTH_CHANGE_EVENT, () => {
      events += 1;
    });

    setAuthToken({
      access_token: 'token-123',
      token_type: 'bearer',
      user: { id: 1, username: 'u', is_admin: false },
    });
    clearAuthToken();

    expect(events).toBe(2);
  });
});
