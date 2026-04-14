import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  E2E_DATABASE_URL,
  E2E_DB_PATH,
  E2E_DEMO_PASSWORD,
  E2E_DEMO_USERNAME,
  E2E_JWT_SECRET,
} from './playwright.env';

function run(command: string, args: string[], cwd: string, extraEnv: NodeJS.ProcessEnv = {}) {
  execFileSync(command, args, {
    cwd,
    stdio: 'inherit',
    env: {
      ...process.env,
      ...extraEnv,
    },
  });
}

export default async function globalSetup() {
  const currentDir = path.dirname(fileURLToPath(import.meta.url));
  const repoRoot = path.resolve(currentDir, '..');
  const backendDir = path.join(repoRoot, 'backend');
  const frontendDir = path.join(repoRoot, 'frontend');
  const sharedEnv = {
    DATABASE_URL: E2E_DATABASE_URL,
    JWT_SECRET_KEY: E2E_JWT_SECRET,
  };

  fs.rmSync(E2E_DB_PATH, { force: true });

  run('npm', ['run', 'build'], frontendDir);
  run('uv', ['run', 'python', '-m', 'database.migrations'], backendDir, sharedEnv);
  run('uv', ['run', 'python', '-m', 'cli', 'create-demo', E2E_DEMO_USERNAME, E2E_DEMO_PASSWORD], backendDir, sharedEnv);
}
