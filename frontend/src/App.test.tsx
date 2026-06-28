import { afterEach, describe, expect, it, vi } from 'vitest';
import React from 'react';
import { createRoot } from 'react-dom/client';
import { act } from 'react-dom/test-utils';
import { MemoryRouter } from 'react-router-dom';

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

vi.mock('@/lib/api', () => ({
  AUTH_CHANGE_EVENT: 'auth-change',
  getCurrentUser: vi.fn(),
  logout: vi.fn(),
}));

vi.mock('@/pages/LandingPage', () => ({
  default: () => <div data-testid="page-landing" />,
}));
vi.mock('@/pages/ProcessingPage', () => ({
  default: () => <div data-testid="page-processing" />,
}));
vi.mock('@/pages/MethodologyPage', () => ({
  default: () => <div data-testid="page-methodology" />,
}));
vi.mock('@/pages/HistoryPage', () => ({
  default: () => <div data-testid="page-history" />,
}));
vi.mock('@/pages/BenchmarksPage', () => ({
  default: () => <div data-testid="page-benchmarks" />,
}));
vi.mock('@/components/ErrorBoundary', () => ({
  default: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));
vi.mock('@/components/LoginPanel', () => ({
  default: () => <div data-testid="login-panel" />,
}));

import App from '@/App';
import { getCurrentUser } from '@/lib/api';

const mockGetCurrentUser = vi.mocked(getCurrentUser);

type RootHandle = ReturnType<typeof createRoot>;

function renderAt(route: string): { container: HTMLDivElement; root: RootHandle } {
  const container = document.createElement('div');
  document.body.appendChild(container);
  const root = createRoot(container);
  act(() => {
    root.render(
      <MemoryRouter initialEntries={[route]}>
        <App />
      </MemoryRouter>,
    );
  });
  return { container, root };
}

describe('App routing: /benchmarks admin gating', () => {
  const handles: Array<{ container: HTMLDivElement; root: RootHandle }> = [];

  afterEach(() => {
    for (const handle of handles) {
      act(() => {
        handle.root.unmount();
      });
      handle.container.remove();
    }
    handles.length = 0;
    vi.clearAllMocks();
  });

  it('redirects guest users away from /benchmarks', () => {
    mockGetCurrentUser.mockReturnValue(null);
    const ctx = renderAt('/benchmarks');
    handles.push(ctx);

    expect(ctx.container.querySelector('[data-testid="page-benchmarks"]')).toBeNull();
    expect(ctx.container.querySelector('[data-testid="page-landing"]')).not.toBeNull();
  });

  it('redirects authenticated non-admin users away from /benchmarks', () => {
    mockGetCurrentUser.mockReturnValue({
      id: 1,
      username: 'regular-user',
      is_admin: false,
    });
    const ctx = renderAt('/benchmarks');
    handles.push(ctx);

    expect(ctx.container.querySelector('[data-testid="page-benchmarks"]')).toBeNull();
    expect(ctx.container.querySelector('[data-testid="page-landing"]')).not.toBeNull();
  });

  it('renders BenchmarksPage for admin users', () => {
    mockGetCurrentUser.mockReturnValue({
      id: 2,
      username: 'admin-user',
      is_admin: true,
    });
    const ctx = renderAt('/benchmarks');
    handles.push(ctx);

    expect(ctx.container.querySelector('[data-testid="page-benchmarks"]')).not.toBeNull();
  });
});
