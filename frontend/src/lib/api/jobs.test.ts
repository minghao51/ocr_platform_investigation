import { afterEach, describe, expect, it, vi } from 'vitest';
import {
  createJobCorrection,
  deleteJob,
  getJob,
  getJobStatus,
  listJobCorrections,
  listJobs,
  processDocument,
  uploadFile,
} from './jobs';
import { setAuthToken, setGuestToken } from './client';

describe('jobs api', () => {
  const originalFetch = globalThis.fetch;

  afterEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
    globalThis.fetch = originalFetch;
  });

  it('uploadFile stores returned guest token and sends access headers', async () => {
    setAuthToken({
      access_token: 'auth-token',
      token_type: 'bearer',
      user: { id: 1, username: 'u', is_admin: false },
    });
    setGuestToken('guest-old');

    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          file_id: 'f1',
          file_name: 'doc.pdf',
          file_type: 'application/pdf',
          file_size: 123,
          guest_token: 'guest-new',
        }),
        { status: 200, headers: { 'content-type': 'application/json' } },
      ),
    );
    globalThis.fetch = fetchMock as unknown as typeof fetch;

    const file = new File(['hello'], 'doc.pdf', { type: 'application/pdf' });
    const result = await uploadFile(file);

    expect(result.file_id).toBe('f1');
    expect(localStorage.getItem('guest_token')).toBe('guest-new');
    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(init.headers).toEqual({
      Authorization: 'Bearer auth-token',
      'X-Guest-Token': 'guest-old',
    });
  });

  it('processDocument throws rate-limit fallback on 429', async () => {
    globalThis.fetch = vi
      .fn()
      .mockResolvedValue(new Response('', { status: 429, headers: { 'content-type': 'text/plain' } })) as unknown as typeof fetch;

    await expect(
      processDocument({ file_id: 'f1', schema_id: 1, provider: 'openrouter', model: 'x' }),
    ).rejects.toEqual(new Error('Rate limit exceeded'));
  });

  it('listJobs uses auth headers and query params', async () => {
    setAuthToken({
      access_token: 'auth-token',
      token_type: 'bearer',
      user: { id: 1, username: 'u', is_admin: false },
    });

    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ jobs: [], total: 0, limit: 10, offset: 5 }), {
        status: 200,
        headers: { 'content-type': 'application/json' },
      }),
    );
    globalThis.fetch = fetchMock as unknown as typeof fetch;

    await listJobs('success', 'gemini', 10, 5);

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain('/api/jobs/?');
    expect(url).toContain('status=success');
    expect(url).toContain('provider=gemini');
    expect(url).toContain('limit=10');
    expect(url).toContain('offset=5');
    expect(init.headers).toEqual({ Authorization: 'Bearer auth-token' });
  });

  it('getJobStatus and listJobCorrections use access headers', async () => {
    setAuthToken({
      access_token: 'auth-token',
      token_type: 'bearer',
      user: { id: 1, username: 'u', is_admin: false },
    });
    setGuestToken('guest-abc');

    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ id: 2, status: 'queued' }), {
          status: 200,
          headers: { 'content-type': 'application/json' },
        }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify([]), {
          status: 200,
          headers: { 'content-type': 'application/json' },
        }),
      );
    globalThis.fetch = fetchMock as unknown as typeof fetch;

    await getJobStatus(2);
    await listJobCorrections(2);

    const [, statusInit] = fetchMock.mock.calls[0] as [string, RequestInit];
    const [, correctionsInit] = fetchMock.mock.calls[1] as [string, RequestInit];
    expect(statusInit.headers).toEqual({
      Authorization: 'Bearer auth-token',
      'X-Guest-Token': 'guest-abc',
    });
    expect(correctionsInit.headers).toEqual({
      Authorization: 'Bearer auth-token',
      'X-Guest-Token': 'guest-abc',
    });
  });

  it('deleteJob, getJob, and createJobCorrection use auth-only headers', async () => {
    setAuthToken({
      access_token: 'auth-token',
      token_type: 'bearer',
      user: { id: 1, username: 'u', is_admin: false },
    });
    setGuestToken('guest-abc');

    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ id: 2 }), { status: 200, headers: { 'content-type': 'application/json' } }))
      .mockResolvedValueOnce(new Response(null, { status: 204 }))
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ id: 1, job_id: 2, corrected_result: {}, feedback_tags: [] }), {
          status: 200,
          headers: { 'content-type': 'application/json' },
        }),
      );
    globalThis.fetch = fetchMock as unknown as typeof fetch;

    await getJob(2);
    await deleteJob(2);
    await createJobCorrection(2, {}, []);

    const [, getInit] = fetchMock.mock.calls[0] as [string, RequestInit];
    const [, delInit] = fetchMock.mock.calls[1] as [string, RequestInit];
    const [, correctionInit] = fetchMock.mock.calls[2] as [string, RequestInit];

    expect(getInit.headers).toEqual({ Authorization: 'Bearer auth-token' });
    expect(delInit.headers).toEqual({ Authorization: 'Bearer auth-token' });
    expect(correctionInit.headers).toEqual({
      'Content-Type': 'application/json',
      Authorization: 'Bearer auth-token',
    });
  });
});
