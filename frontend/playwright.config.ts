import { defineConfig } from '@playwright/test';
import { E2E_BACKEND_PORT, E2E_BASE_URL, E2E_DATABASE_URL, E2E_JWT_SECRET } from './playwright.env';

export default defineConfig({
  testDir: '.',
  testMatch: 'e2e/**/*.spec.ts',
  fullyParallel: false,
  retries: 0,
  reporter: 'list',
  globalSetup: './playwright.global-setup.ts',
  use: {
    baseURL: E2E_BASE_URL,
    trace: 'on-first-retry',
  },
  webServer: {
    command: `uv run uvicorn main:app --host 127.0.0.1 --port ${E2E_BACKEND_PORT}`,
    cwd: '../backend',
    url: `${E2E_BASE_URL}/health`,
    reuseExistingServer: false,
    timeout: 120 * 1000,
    env: {
      DATABASE_URL: E2E_DATABASE_URL,
      JWT_SECRET_KEY: E2E_JWT_SECRET,
    },
  },
});
