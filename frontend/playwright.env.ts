import path from 'node:path';

export const E2E_BACKEND_PORT = 8010;
export const E2E_BASE_URL = `http://127.0.0.1:${E2E_BACKEND_PORT}`;
export const E2E_DB_PATH = path.join('/tmp', 'ocr-platform-playwright-smoke.db');
export const E2E_DATABASE_URL = `sqlite:///${E2E_DB_PATH}`;
export const E2E_JWT_SECRET = 'playwright-local-smoke-secret-0123456789';
export const E2E_DEMO_USERNAME = 'guest1';
export const E2E_DEMO_PASSWORD = 'demo123';
