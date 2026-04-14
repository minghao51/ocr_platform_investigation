# Handoff: Demo Deploy Follow-Up

Date: 2026-04-11

## What was completed

- Audited Docker, deployment config, docs, auth, rate limiting, and benchmark/test coverage.
- Fixed demo-account behavior so limited demo users are usable instead of being hard-blocked.
- Implemented configurable per-minute OCR rate limiting with admin/master bypass behavior.
- Aligned fresh database schema with the user limit fields already used by the app.
- Switched hosted deployment guidance to a Docker-based Render flow.
- Simplified `docker-compose.yml` for demo/staging use by removing dev bind mounts.
- Added `Cache-Control: no-store` for non-asset responses so demo pages/API responses stay fresh.
- Repaired benchmark runner/test issues so the full backend suite passes.

## Files changed in this thread

- [README.md](/Users/minghao/Desktop/personal/ocr_platform_testdrive/README.md)
- [.env.example](/Users/minghao/Desktop/personal/ocr_platform_testdrive/.env.example)
- [docker-compose.yml](/Users/minghao/Desktop/personal/ocr_platform_testdrive/docker-compose.yml)
- [Dockerfile](/Users/minghao/Desktop/personal/ocr_platform_testdrive/Dockerfile)
- [render.yaml](/Users/minghao/Desktop/personal/ocr_platform_testdrive/render.yaml)
- [backend/config.py](/Users/minghao/Desktop/personal/ocr_platform_testdrive/backend/config.py)
- [backend/limiter.py](/Users/minghao/Desktop/personal/ocr_platform_testdrive/backend/limiter.py)
- [backend/dependencies.py](/Users/minghao/Desktop/personal/ocr_platform_testdrive/backend/dependencies.py)
- [backend/main.py](/Users/minghao/Desktop/personal/ocr_platform_testdrive/backend/main.py)
- [backend/routers/upload.py](/Users/minghao/Desktop/personal/ocr_platform_testdrive/backend/routers/upload.py)
- [backend/routers/processing.py](/Users/minghao/Desktop/personal/ocr_platform_testdrive/backend/routers/processing.py)
- [backend/routers/text_processing.py](/Users/minghao/Desktop/personal/ocr_platform_testdrive/backend/routers/text_processing.py)
- [backend/database/schema.sql](/Users/minghao/Desktop/personal/ocr_platform_testdrive/backend/database/schema.sql)
- [backend/database/crud.py](/Users/minghao/Desktop/personal/ocr_platform_testdrive/backend/database/crud.py)
- [backend/cli.py](/Users/minghao/Desktop/personal/ocr_platform_testdrive/backend/cli.py)
- [backend/benchmarks/runner.py](/Users/minghao/Desktop/personal/ocr_platform_testdrive/backend/benchmarks/runner.py)
- [backend/tests/test_limits.py](/Users/minghao/Desktop/personal/ocr_platform_testdrive/backend/tests/test_limits.py)
- [backend/tests/integration/test_benchmark_crud.py](/Users/minghao/Desktop/personal/ocr_platform_testdrive/backend/tests/integration/test_benchmark_crud.py)
- [backend/tests/integration/test_benchmark_runner.py](/Users/minghao/Desktop/personal/ocr_platform_testdrive/backend/tests/integration/test_benchmark_runner.py)
- [docs/README.md](/Users/minghao/Desktop/personal/ocr_platform_testdrive/docs/README.md)
- [docs/guides/setup.md](/Users/minghao/Desktop/personal/ocr_platform_testdrive/docs/guides/setup.md)
- [docs/guides/deployment.md](/Users/minghao/Desktop/personal/ocr_platform_testdrive/docs/guides/deployment.md)
- [docs/guides/user-guide.md](/Users/minghao/Desktop/personal/ocr_platform_testdrive/docs/guides/user-guide.md)
- [docs/guides/troubleshooting.md](/Users/minghao/Desktop/personal/ocr_platform_testdrive/docs/guides/troubleshooting.md)
- [docs/reference/testing.md](/Users/minghao/Desktop/personal/ocr_platform_testdrive/docs/reference/testing.md)

## Verified status

- `cd backend && uv run pytest -q` -> passes (`108 passed`)
- `cd frontend && npm run build` -> passes
- `docker compose config` -> valid
- Browser verification was partially completed against a live local app.

## Important product behavior after fixes

- Limited demo users:
  - can log in
  - can use OCR until they hit `DEMO_DAILY_REQUEST_LIMIT`
- Admin/master users:
  - bypass the demo daily cap
  - bypass per-minute OCR/upload rate caps
- Non-asset responses:
  - return `Cache-Control: no-store`
- Frontend assets:
  - still cache normally when hashed

## Leftover items for the next thread

## Continuation update

Completed in the follow-up thread after this handoff was written:

- Investigated the frontend auth refresh behavior and fixed it so auth state now re-syncs on explicit auth changes, `storage` events, focus, `pageshow`, and visibility changes.
- Switched the app header auth status to derive from tracked user state instead of re-reading token presence ad hoc during render.
- Added a real Playwright smoke test that:
  - builds the frontend
  - boots the backend against a temporary SQLite DB
  - seeds a demo user
  - verifies login
  - verifies upload unlocks
  - verifies auth survives reload
  - verifies history access after login
- Added Playwright config/setup files and an npm script:
  - [frontend/playwright.config.ts](/Users/minghao/Desktop/personal/ocr_platform_testdrive/frontend/playwright.config.ts)
  - [frontend/playwright.global-setup.ts](/Users/minghao/Desktop/personal/ocr_platform_testdrive/frontend/playwright.global-setup.ts)
  - [frontend/playwright.env.ts](/Users/minghao/Desktop/personal/ocr_platform_testdrive/frontend/playwright.env.ts)
  - [frontend/e2e/smoke.spec.ts](/Users/minghao/Desktop/personal/ocr_platform_testdrive/frontend/e2e/smoke.spec.ts)

Verified in this continuation thread:

- `cd frontend && npm run test:e2e:smoke` -> passes

Still pending after this continuation:

- actual hosted deployment to Render
- hosted account creation
- Playwright MCP-specific browser verification against the hosted app

Current MCP status:

- The earlier `/.playwright-mcp` permissions issue is no longer the only problem seen.
- In this environment, Playwright MCP also hit:
  - stale browser profile lock (`Browser is already in use ...`)
  - then transport shutdowns after cleanup (`Transport closed`)
- Because of that, MCP-specific browser verification is still unresolved even though the repository now has a working Playwright smoke test.

### 1. Do a real hosted deployment

Target first:

- Render via [render.yaml](/Users/minghao/Desktop/personal/ocr_platform_testdrive/render.yaml)

Suggested flow:

1. Push current branch/repo state.
2. Create a Render Blueprint deploy.
3. Set real secrets:
   - `JWT_SECRET_KEY`
   - one or more provider API keys
4. Confirm persistent disk is mounted at `/app/data`.
5. Verify hosted endpoints:
   - `/health`
   - `/docs`
   - `/`

### 2. Create real demo accounts on the hosted instance

Need:

- one master/admin account for presenter use
- several limited guest/demo accounts

Commands to use in the app container:

```bash
cd /app/backend
python -m cli create-admin master <strong-password>
python -m cli create-demo guest1 <password>
python -m cli create-demo guest2 <password>
python -m cli list-users
```

Notes:

- `python -m cli ...` works from inside `backend/`
- `python -m backend.cli ...` works from repo root
- do not mix those contexts in docs/scripts without being explicit

### 3. Finish browser verification with Playwright MCP specifically

This is still incomplete.

What happened:

- Playwright MCP failed in this environment because it tried to create `/.playwright-mcp`
- root filesystem permissions blocked that
- I used the Playwright CLI wrapper as a fallback and verified page loads plus API calls there

Next-thread goal:

1. Fix the MCP runtime path/environment.
2. Re-run browser verification using MCP, not CLI fallback.
3. Verify:
   - login flow updates UI state correctly
   - upload unlocks after login
   - history access works
   - rate limiting behavior is visible and sane

### 4. Investigate UI auth refresh behavior

There was a suspicious browser observation:

- manually injecting `auth_token` into localStorage and reloading did not flip the UI out of guest mode during the CLI fallback run

This may be one of:

- a real frontend auth-state refresh issue
- CLI browser/session behavior
- bad storage timing in the fallback path

Likely files to inspect:

- [frontend/src/App.tsx](/Users/minghao/Desktop/personal/ocr_platform_testdrive/frontend/src/App.tsx)
- [frontend/src/pages/ProcessingPage.tsx](/Users/minghao/Desktop/personal/ocr_platform_testdrive/frontend/src/pages/ProcessingPage.tsx)
- [frontend/src/components/LoginPanel.tsx](/Users/minghao/Desktop/personal/ocr_platform_testdrive/frontend/src/components/LoginPanel.tsx)
- [frontend/src/lib/api.ts](/Users/minghao/Desktop/personal/ocr_platform_testdrive/frontend/src/lib/api.ts)

### 5. Add one real frontend smoke test

Recommended:

- login
- upload enablement
- history access

Best place:

- introduce a minimal Playwright e2e smoke script rather than relying only on manual verification

### 6. Move beyond SQLite before wider sharing

For demo:

- SQLite on a persistent disk is acceptable

Before broader use:

- move to Postgres
- review concurrency assumptions
- review file storage strategy for uploads

## Known caveats

- Existing uncommitted repo changes were already present before this thread, especially around benchmarks and local tool folders.
- `.playwright-cli/`, `.planning/`, and `.claude/` exist locally and should be treated carefully before committing.
- The temporary local demo DB used during verification was `/tmp/ocr-platform-demo.db`.
- During local verification a short JWT secret was used only for smoke testing; production must use a strong secret.

## Recommended order for next thread

1. Deploy to Render.
2. Create hosted admin + demo accounts.
3. Fix/enable Playwright MCP runtime.
4. Re-run browser verification against the hosted app.
5. Investigate frontend auth-state refresh if it still reproduces.
6. Add one automated frontend smoke test.
7. Decide whether to prepare the Postgres migration now or after demo feedback.

## Handy commands

```bash
cd /Users/minghao/Desktop/personal/ocr_platform_testdrive/backend
uv run pytest -q
```

```bash
cd /Users/minghao/Desktop/personal/ocr_platform_testdrive/frontend
npm run build
```

```bash
cd /Users/minghao/Desktop/personal/ocr_platform_testdrive
docker compose config
```
