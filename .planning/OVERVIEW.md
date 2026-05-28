# OCR Platform — Overview

Document processing platform that uploads files (PDFs, images, audio), routes them through intelligent pipelines (local docling, VLM providers, text extraction), and returns structured JSON. Supports human-in-the-loop corrections and automated benchmarking to compare provider accuracy/cost.

## Architecture

**Monorepo, client-server.** Backend runs as a FastAPI process; frontend is a Vite-bundled React SPA served by the same process in production. No separate API gateway.

```
User → React SPA (Vite) → FastAPI (uvicorn) → SQLite
                              ├─ Docling (local parsing)
                              ├─ OpenRouter (VLM API)
                              ├─ Google Gemini (VLM API)
                              └─ LiteLLM (unified LLM API)
```

**Layered structure:**
- **Routers** (`backend/routers/`): Thin HTTP layer — auth, upload, process, jobs, benchmarks, analytics, quality, websocket, schemas, extract_settings. Each router parses requests, calls services/CRUD, returns responses.
- **Services** (`backend/services/`): Business logic — processing pipeline (`processing.py:21`), VLM provider abstractions (`vlm_provider.py:9`), docling parsing (`docling_service.py:42`), prompt optimization (`prompt_optimizer.py`), schema suggestion, quality gate, chunking, transcription.
- **Processor Strategy** (`backend/services/processors/`): Pluggable extraction strategies via `ProcessorFactory` (`factory.py:13`) and `Processor` ABC (`base.py:5`). Implementations: `VisionProcessor`, `TextProcessor`, `DoclingParseProcessor`, `DoclingExtractProcessor`, `_HybridProcessor`.
- **Database** (`backend/database/`): SQLite with WAL mode (`pool.py:28`), migration framework (`migrations.py:14`), CRUD per domain.
- **Models** (`backend/models/`): Pydantic v2 request/response schemas (`schemas.py`).
- **Frontend** (`frontend/src/`): React 18 SPA with react-router-dom v6, Tailwind v3, Vitest + Playwright.

**Key abstractions:**
- `ProcessingService` (`processing.py:21`) — orchestrator that wires providers/pipeline/docling together. Entry point for all extraction jobs.
- `VLMProvider` ABC (`vlm_provider.py:9`) — base class for `OpenRouterProvider` (`openrouter.py`), `GeminiProvider` (`gemini.py`), `LiteLLMProvider` (`litellm_provider.py`). Each implements `process_image()` and `process_text()`.
- `Processor` ABC (`processors/base.py:5`) — extraction strategy interface. Factory selects one based on method + file type.
- `PromptOptimizer` (`prompt_optimizer.py`) — enriches user prompts with schema hints, CoT instructions, doc-type-specific templates.
- `JobQueue` (`job_queue.py`) — durable SQLite-backed background worker with recovery on startup (`main.py:40`).

**API base path:** All endpoints live under `/api`. Defined in routers with `prefix="/api/..."`. Frontend uses `API_BASE = '/api'` (`client.ts:1`). In production, nginx/reverse-proxy at `/api` → backend.

## Key Data Flows

### Document Processing Flow
1. **Upload** → `POST /api/upload/` → file streamed to `data/uploads/` → metadata stored in `uploaded_files` table → returns `file_id` + optional `guest_token`.
2. **Process** → `POST /api/process/` → `DocumentClassifier` analyzes PDF → selects pipeline (`text`/`vision`/`hybrid`/`docling-parse`/`docling-extract`/`transcription`) → creates `processing_jobs` row → enqueues task in `job_queue` table → returns `job_id`.
3. **Job Worker** → background coroutine reads `job_queue` → `run_processing_job()` (`processing.py:143`) → resolves schema, optimizes prompt via `PromptOptimizer`, instantiates `ProcessingService` → `ProcessorFactory` selects strategy → strategy calls provider API (or docling locally) → result written to `processing_jobs.result`.
4. **Status Polling** → `GET /api/process/status/{job_id}` or WebSocket via `POST /api/ws/ticket` then `ws /api/ws/job/{job_id}`.
5. **Correction** → Human reviews result → `POST /api/jobs/{id}/corrections` with corrected JSON + feedback tags → diff stored, `PromptLearningService` updates prompt hints.

### Auth Flow (see Auth Flow Summary section)
### Benchmarking Flow
- CLI: `uv run python -m backend.cli run-benchmark --provider openrouter --model google/gemini-3-flash-preview` (`cli.py:36`).
- Steps: load dataset (CORD, extended datasets) → run samples through VLM → score accuracy per field → store in `benchmark_runs` + `benchmark_results` tables.
- Results exportable to markdown (`cli.py:229`).

## Tech Stack

| Layer | Technology | Version | Notes |
|---|---|---|---|
| Backend runtime | Python | >=3.11 | uv package manager |
| Backend framework | FastAPI | 0.115.0 | async, auto OpenAPI docs |
| ASGI server | uvicorn | 0.32.0 | `uvicorn[standard]` |
| Frontend | React | ^18.3.1 | SPA |
| Frontend framework | Vite | ^5.3.1 | Bundler |
| Frontend routing | react-router-dom | ^6.30.3 | Client-side routing |
| CSS | Tailwind CSS | ^3.4.4 | Utility-first |
| TypeScript | TypeScript | ^5.5.3 | Frontend only |
| Database | SQLite | — | WAL mode, no ORM. `aiosqlite` for async |
| Validation | Pydantic | >=2.13.0 | Backend models + settings |
| Auth | PyJWT + passlib (argon2) | >=2.9.0 / >=1.7.4 | HS256 tokens |
| Rate limiting | slowapi | >=0.1.9 | 10 req/min default |
| CLI | tabulate | >=0.9.0 | Admin CLI |
| PDF parsing | PyMuPDF, pdfplumber, docling | >=1.26.7 / >=0.11.0 / >=2.89.0 | Local extraction |
| VLM clients | httpx | 0.28.0 | Custom provider wrappers |
| LiteLLM | litellm | >=1.81.0 | Unified provider interface |
| Image processing | Pillow, opencv-python-headless | >=11.0.0 / >=4.9.0 | Quality gate, preprocessing |
| Audio transcription | — | — | Via VLM providers |
| Testing (backend) | pytest | >=7.4.0 | pytest-asyncio, pytest-mock |
| Testing (frontend) | Vitest + Playwright | ^2.1.9, ^1.55.0 | Unit + E2E |
| Linting | ruff, ESLint, prettier | — | pre-commit hooks |
| CI | GitHub Actions | — | lint, test, deploy to Render |

## Infrastructure

- **Docker** (`docker-compose.yml`): Single `app` service. Port 8001:8000. Binds `./data` for persistence, mounts `.env` (encrypted) + `.env.keys`. CPU limit 2.0, memory 2G. `no-new-privileges:true`, `cap_drop: ALL`.
- **Dockerfile**: Not shown in docker-compose, multistage (builds frontend dist, runs backend). Check `Dockerfile` for details.
- **Render deployment** (`render.yaml`): Free tier, Docker runtime, Oregon region. Disk mount at `/app/data` (1GB). `JWT_SECRET_KEY` auto-generated; `CORS_ORIGINS_STR` set to Render URL.
- **CI/CD** (`.github/workflows/deploy.yml`): On push to `main` → `uv sync --frozen --dev` → `uv run pytest` → deploy to Render via `render-deploy-action@v1`.
- **Lint CI** (`.github/workflows/lint.yml`): Separate workflow for ruff + pre-commit.
- **Pre-commit** (`.pre-commit-config.yaml`): Husky + lint-staged for frontend (`eslint --fix`, `prettier --write`).
- **SPA fallback**: FastAPI middleware (`main.py:145`) serves `index.html` for non-API, non-asset 404s. Static assets from `frontend/dist/assets/`.

## Integrations

| Integration | Type | Status | Configuration | Notes |
|---|---|---|---|---|
| OpenRouter | External VLM API | Active | `OPENROUTER_API_KEY` env var | Routes to 40+ models (Qwen, Gemini via OpenRouter, GPT-4.1 Mini, Grok 4.1). Models defined in `config/providers.yaml:27` |
| Google Gemini | External VLM API | Active | `GEMINI_API_KEY` env var | Direct Gemini API. Models: 2.0 Flash through 3 Pro Preview |
| LiteLLM | External LLM API | Active | Via `OPENROUTER_API_KEY` or direct | Unified provider wrapper (`litellm_provider.py`). Uses openai-compatible endpoints |
| SQLite | Local database | Active | `DATABASE_URL` (default: `sqlite:///data/ocr_platform.db`) | WAL mode, no connection pool (direct aiosqlite). Migrated on startup (`main.py:39`) |
| Docling | Local document parser | Active | None (local) | CPU-optimized: PyMuPDF backend, EasyOCR, TableFormer FAST mode |
| Argon2 | Password hashing | Active | None (library) | Via `passlib[argon2]` |
| JWT (PyJWT) | Auth tokens | Active | `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `JWT_EXPIRATION_HOURS` | HS256. 24h expiry by default. Token versioning for revocation |
| LiteLLM | Unified LLM provider | Active | Via OpenRouter API key or custom endpoint | Wraps Gemini/OpenAI/etc models under one interface |

**Provider catalog** (`config/providers.yaml`): 3 providers (docling local, openrouter, gemini, litellm) with ~18 models total. Default provider is docling.

## Auth Flow Summary

**Two auth modes:** registered user (JWT) and guest (token).

### Guest Flow
- No login required. On first upload, a `guest_token` is generated (`secrets.token_urlsafe(32)`) server-side and returned with the upload response.
- Guest token stored in `localStorage` as `guest_token` (`client.ts:39`). Sent as `X-Guest-Token` header on subsequent API calls.
- Guest tokens are opaque strings. No user record created. Guest-scoped data access enforced via `ensure_file_access()` / `ensure_job_access()` in `routers/shared.py`.
- Guest mode indicated in UI by amber "Guest mode" badge (`App.tsx:163`).

### Registered User Flow
- **Login**: `POST /api/auth/login` → validates username/password (argon2 hash) → returns JWT (`auth.py:27`). Rate-limited to 5/min per IP+username (`limiter.py:61`). `X-Login-Username` header used for granular rate-limit keying.
- **JWT payload**: `{ user_id, username, is_admin, exp, iat, token_version }` (`auth.py:38`). Signed with HS256. Configurable expiry (default 24h).
- **Token storage**: `localStorage` key `auth_token` (`client.ts:18`). Sent as `Authorization: Bearer <token>`.
- **Verification**: `get_current_user()` dependency (`dependencies.py:22`) decodes JWT, checks `token_version` against DB to detect revocation. `get_optional_user()` allows guest access.
- **Logout**: `POST /api/auth/logout` → increments `users.token_version` → invalidates all existing JWTs for that user (`auth.py:81`).
- **Admin bypass**: Admins skip per-minute rate limits (`limiter.py:42`) and daily request caps (`dependencies.py:129`).

### Demo Users
- Created via CLI: `uv run python -m backend.cli create-demo <user> <pass>` (`cli.py:301`).
- Flagged `is_limited=1`. Capped at `DEMO_DAILY_REQUEST_LIMIT` (default 5) requests/day via atomic SQL `UPDATE ... RETURNING` check (`dependencies.py:138`).

### WebSocket Auth
- JWT cannot be passed in WebSocket query params (logs). Instead: `POST /api/ws/ticket` exchanges JWT for a single-use, 60-second TTL ticket. Ticket used as `?ticket=` query param on `ws://api/ws/job/{job_id}` (`websocket.py:27`).

## Environment Variables

All env vars in `.env` (dotenvx-encrypted). Read via pydantic-settings `Settings` class (`config.py:13`).

| Variable | Default | Required | Description |
|---|---|---|---|
| `OPENROUTER_API_KEY` | `""` | Yes (for OpenRouter provider) | API key for OpenRouter VLM proxy |
| `GEMINI_API_KEY` | `""` | Yes (for Gemini provider) | Google Gemini API key |
| `DATABASE_URL` | `sqlite:///data/ocr_platform.db` | No | SQLite connection string |
| `JWT_SECRET_KEY` | `change-me-in-production...` | **Yes** (production) | HMAC key for JWT signing. Runtime error if default in non-local env (`config.py:81`) |
| `JWT_ALGORITHM` | `HS256` | No | JWT signing algorithm |
| `JWT_EXPIRATION_HOURS` | `24` | No | Token lifetime in hours |
| `MAX_FILE_SIZE` | `10485760` (10MB) | No | Max upload bytes |
| `CORS_ORIGINS_STR` | `http://localhost:5173,http://localhost:3000` | No | Comma-separated CORS origins. Also accepts `CORS_ORIGINS` alias |
| `RATE_LIMIT_PER_MINUTE` | `10` | No | API rate limit per user/IP |
| `DEMO_DAILY_REQUEST_LIMIT` | `5` | No | Daily cap for `is_limited` users |
| `ENVIRONMENT` / `APP_ENV` / `ENV` | `development` | No | Determines local vs production behavior (JWT secret validation) |
| `DOCLING_PARSE_TIMEOUT_SECONDS` | `60` | No | Timeout for docling parsing |
| `ENABLE_JOB_WORKER` | `True` | No | Toggle background job worker |
