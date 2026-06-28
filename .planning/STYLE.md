# OCR Platform — Code Style & Conventions

## File Organization

```
ocr_platform_testdrive/
├── backend/                          # FastAPI backend (Python)
│   ├── main.py                       # App entry, lifespan, CORS, router registration
│   ├── config.py                     # pydantic-settings, env var parsing
│   ├── auth.py                       # JWT create/verify, argon2 password hashing
│   ├── dependencies.py               # FastAPI Depends: get_current_user, get_optional_user, limits
│   ├── limiter.py                    # slowapi rate-limit key function, admin exemption
│   ├── paths.py                      # Repo root, data dir, upload dir discovery
│   ├── cli.py                        # CLI entry point
│   ├── routers/                      # HTTP endpoint handlers (one file per domain)
│   │   ├── upload.py                 #   File upload + PDF text-layer analysis
│   │   ├── processing.py             #   Document processing routing + queueing
│   │   ├── jobs.py                   #   Job CRUD, corrections
│   │   ├── schemas.py                #   Schema CRUD + suggestions
│   │   ├── text_processing.py        #   Text-specific processing endpoint
│   │   ├── websocket.py              #   WebSocket ticket + status stream
│   │   ├── providers.py              #   VLM provider listing
│   │   ├── extract_settings.py       #   Extraction config metadata
│   │   ├── benchmarks.py             #   Benchmark run/results
│   │   ├── analytics.py              #   Usage analytics
│   │   ├── quality.py                #   Quality check endpoints
│   │   └── shared.py                 #   Shared helpers (ensure_file_access, ensure_job_access)
│   ├── services/                     # Business logic layer
│   │   ├── processing.py             #   ProcessingService + top-level run_processing_job()
│   │   ├── job_queue.py              #   Async job worker (poll DB queue, dispatch)
│   │   ├── openrouter.py             #   OpenRouter VLM provider
│   │   ├── gemini.py                 #   Gemini VLM provider
│   │   ├── litellm_provider.py       #   LiteLLM VLM provider
│   │   ├── vlm_provider.py           #   Abstract VLM provider interface
│   │   ├── provider_catalog.py       #   Provider + model metadata registry
│   │   ├── provider_utils.py         #   API key resolution helpers
│   │   ├── pricing.py                #   Cost calculation per model
│   │   ├── prompt_optimizer.py       #   Prompt enrichment (CoT, hints, doc-type)
│   │   ├── prompt_learning.py        #   Correction → prompt learning loop
│   │   ├── prompt_templates.py       #   System prompt templates
│   │   ├── docling_service.py        #   Docling document parsing
│   │   ├── hybrid_processing.py      #   Layout + vision hybrid pipeline
│   │   ├── text_extraction.py        #   pdfplumber text extraction
│   │   ├── schema_service.py         #   Schema template management
│   │   ├── schema_suggester.py       #   AI schema suggestion from documents
│   │   ├── quality_gate.py           #   Image quality assessment (brightness, blur, etc.)
│   │   ├── image_service.py          #   Image loading/conversion
│   │   ├── image_preprocessor.py     #   Auto-fix image quality issues
│   │   ├── document_classifier.py    #   PDF type detection (digital vs scanned)
│   │   ├── chunking_service.py       #   Document chunking for large files
│   │   ├── transcription_service.py  #   Audio → text transcription
│   │   ├── processing_utils.py       #   Status broadcast helper
│   │   └── processors/               #   Strategy pattern per extraction method
│   │       ├── base.py               #     Processor ABC
│   │       ├── factory.py            #     ProcessorFactory (strategy selection)
│   │       ├── vision.py             #     VisionProcessor (VLM-based)
│   │       ├── text.py               #     TextProcessor (pdfplumber → LLM)
│   │       ├── docling_parse.py      #     DoclingParseProcessor (local parse → LLM)
│   │       └── docling_extract.py    #     DoclingExtractProcessor (local VLM)
│   ├── models/                       # Pydantic models
│   │   └── schemas.py                #   ProcessRequest, ProcessResponse, SchemaSuggestRequest, etc.
│   ├── database/                     # Data access layer
│   │   ├── migrations.py             #   Schema migrations (SQL)
│   │   ├── pool.py                   #   aiosqlite connection pool
│   │   ├── validators.py             #   Column name allow-list
│   │   └── crud/                     #   CRUD per domain entity
│   │       ├── jobs.py               #     processing_jobs + uploaded_files
│   │       ├── users.py              #     users table
│   │       ├── schemas.py            #     extraction_schemas + corrections + prompt_learning
│   │       ├── benchmarks.py         #     benchmark_runs + benchmark_results
│   │       └── queue.py              #     job_queue table (worker scheduling)
│   ├── benchmarks/                   # Benchmarking system
│   │   ├── runner.py                 #   Benchmark orchestrator
│   │   ├── scoring.py                #   Accuracy scoring (LLM-as-judge, exact match)
│   │   ├── datasets.py               #   Built-in benchmark datasets
│   │   ├── datasets_extended.py      #   Extended datasets
│   │   ├── ablation_benchmark.py     #   Ablation experiments
│   │   ├── prompt_optimizer_benchmark.py
│   │   └── exporter.py               #   CSV/JSON export
│   └── tests/                        # pytest test suite
│       ├── conftest.py               #   Root fixtures (client, auth_header)
│       ├── unit/                     #   Fast, isolated unit tests
│       └── integration/              #   Full-pipeline integration tests (DB required)
├── frontend/                         # React + TypeScript frontend
│   ├── src/
│   │   ├── main.tsx                  # ReactDOM.createRoot entry
│   │   ├── App.tsx                   # Root component: nav, routing, auth state
│   │   ├── pages/                    # Page-level routed components
│   │   │   ├── LandingPage.tsx       #   Home page
│   │   │   ├── ProcessingPage.tsx    #   Smart extraction page
│   │   │   ├── BaseExtractionPage.tsx#   Shared extraction workflow component
│   │   │   ├── HistoryPage.tsx       #   Job history list + detail
│   │   │   ├── MethodologyPage.tsx   #   Extraction method documentation
│   │   │   └── BenchmarksPage.tsx    #   Benchmark results viewer
│   │   ├── components/               # Reusable UI components
│   │   │   ├── FileUpload.tsx        #   Drag-and-drop file upload
│   │   │   ├── ModelSelector.tsx     #   Provider + model dropdowns
│   │   │   ├── MethodModelSelector.tsx
│   │   │   ├── ResultsDisplay.tsx    #   Job result display
│   │   │   ├── ProcessingStatus.tsx  #   Status indicator
│   │   │   ├── ExtractedDataDisplay.tsx
│   │   │   ├── MarkdownViewer.tsx    #   Rendered markdown output
│   │   │   ├── SchemaEditor.tsx      #   JSON schema editor
│   │   │   ├── CorrectionReviewPanel.tsx
│   │   │   ├── AdvancedOptions.tsx   #   Temperature, max_tokens, quality
│   │   │   ├── LoginPanel.tsx        #   Login form
│   │   │   ├── RateLimitAlert.tsx    #   429 warning
│   │   │   ├── QualityBadge.tsx      #   Quality score display
│   │   │   ├── ErrorBoundary.tsx     #   React error boundary
│   │   │   ├── LoadingSpinner.tsx
│   │   │   └── schemaEditorValidation.ts  # Non-UI validation logic
│   │   ├── lib/                      # Non-UI logic
│   │   │   ├── api/                  #   API client module
│   │   │   │   ├── index.ts          #     Barrel re-export
│   │   │   │   ├── client.ts         #     Auth tokens, headers, base fetch
│   │   │   │   ├── types.ts          #     All shared API types
│   │   │   │   ├── auth.ts           #     login/logout
│   │   │   │   ├── jobs.ts           #     upload, process, status, corrections
│   │   │   │   ├── schemas.ts        #     Schema CRUD + suggestions
│   │   │   │   ├── settings.ts       #     Providers, extract settings
│   │   │   │   └── benchmarks.ts     #     Benchmark API
│   │   │   ├── websocket.ts          #   JobStatusWebSocket class
│   │   │   ├── status.ts             #   Status color mapping
│   │   │   └── methods.ts            #   ExtractionMethod metadata + constants
│   │   └── hooks/                    # Custom React hooks
│   │       └── useProviders.ts       #   Provider list fetching
│   ├── e2e/                          # Playwright end-to-end tests
│   │   ├── smoke.spec.ts
│   │   └── markdown-safety.spec.ts
│   ├── vitest.config.ts
│   └── playwright.config.ts
├── data/                             # Runtime data (uploads, sqlite DB)
├── Dockerfile
└── docker-compose.yml                # Port 8001:8000, env injection
```

## Naming Conventions

### Python

| Element | Convention | Examples |
|---------|-----------|---------|
| Files | `snake_case.py` | `processing.py`, `job_queue.py`, `vlm_provider.py`, `litellm_provider.py` |
| Classes | `PascalCase` | `ProcessingService`, `OpenRouterProvider`, `ProcessorFactory`, `Settings` |
| Functions | `snake_case` | `run_processing_job()`, `create_access_token()`, `get_settings()`, `verify_token()` |
| Private helpers | `_prefix_underscore` | `_resolve_schema()`, `_register_result()`, `_HybridProcessor`, `_loads_if_json()` |
| Methods | `snake_case` (no prefix except private) | `process_file()`, `get_provider()`, `update_job_status()`, `get_processor()` |
| Async functions | `async def` prefix | `async def process_document()` (routers, services, CRUD all async) |
| Module constants | `UPPER_SNAKE` | `MAX_PROMPT_LENGTH` (10_000), `MAX_SCHEMA_DEPTH` (5), `ALLOWED_EXTENSIONS` |
| Pydantic models | `PascalCase` | `ProcessRequest`, `ProcessResponse`, `SchemaSuggestRequest`, `JobCorrectionRequest` |
| Router variable | `router` (uniform) | `router = APIRouter(prefix="/api/upload", tags=["upload"])` |
| Logger | `logger` (module-level) | `logger = logging.getLogger(__name__)` |
| Test functions | `test_<descriptive_name>` | `test_limited_demo_user_is_allowed_below_daily_cap()` |
| CRUD functions | `create_<entity>`, `get_<entity>`, `list_<entities>`, `update_<entity>` | `create_job()`, `get_user_by_id()`, `list_jobs()`, `update_job_status()` |

### TypeScript

| Element | Convention | Examples |
|---------|-----------|---------|
| Files (components) | `PascalCase.tsx` | `FileUpload.tsx`, `ResultsDisplay.tsx`, `LoginPanel.tsx` |
| Files (lib) | `camelCase.ts` | `client.ts`, `websocket.ts`, `status.ts`, `methods.ts` |
| Components | `PascalCase`, default export | `export default function FileUpload({...})` |
| Props interfaces | `PascalCase + Props` suffix | `FileUploadProps`, `ResultsDisplayProps`, `LoginPanelProps` |
| Functions | `camelCase` | `uploadFile()`, `processDocument()`, `getAuthToken()` |
| Private methods | `_prefix_underscore` | `_fetchTicket()`, `_build_request()` |
| Types/Interfaces | `PascalCase` | `ProcessRequest`, `Job`, `QualityReport`, `WebSocketMessage` |
| Constants | `UPPER_SNAKE` | `API_BASE`, `AUTH_TOKEN_KEY`, `GUEST_TOKEN_KEY`, `AUTH_CHANGE_EVENT` |
| Type aliases | `PascalCase` | `ExtractionMethod`, `StatusCallback`, `ErrorCallback` |
| Enum-like | `type` union strings | `type ExtractionMethod = 'auto' | 'text' | 'vision' | ...` |
| Interface properties | `snake_case` (mirrors API JSON) | `file_id: string`, `guest_token?: string`, `processing_method?: string` |

## Python Patterns

### Pydantic Models (`models/schemas.py`)
- All inherit from `BaseModel` (pydantic v2)
- `Field()` for metadata: `Field(default=..., max_length=..., ge=0.0, le=2.0)`
- `@field_validator("field_name")` for per-field validation, always `@classmethod`
- `@model_validator(mode="before")` for cross-field transformations
- `Optional[]` used instead of `| None` in model classes
- `ConfigDict` only used in `settings.py`; simple models use `BaseModel` directly

### FastAPI Routers (`routers/`)
- One file per domain, single `router = APIRouter(prefix="/api/<domain>", tags=["<domain>"])`
- **No sub-routers** — every router registers flat at the app level in `main.py:110-121`
- Dependencies: `get_current_user` (requires auth), `get_optional_user` (auth or guest)
- Auth endpoints additionally use `check_and_increment_daily_limit`
- Rate limiting via decorator: `@limiter.limit(get_rate_limit_value)`
- Route handlers use `async def` (DB/IO-bound); simple sync handlers use `def`
- Error responses: `raise HTTPException(status_code=4xx, detail="message")`
- Response typing: `response_model=<PydanticClass>` on the decorator or implicit return dict

### Service Layer
- **Service classes** in `services/` with `__init__` accepting configuration
  - E.g., `ProcessingService(quality_threshold, auto_preprocess, skip_quality)`
- **Top-level async functions** for entry points: `run_processing_job()`, `run_text_processing_job()`
- **Provider strategy**: base `Processor` ABC (`processors/base.py`) → concrete implementations in `processors/` → resolved by `ProcessorFactory.get_processor()`
- **VLM providers**: duck-typed classes (`OpenRouterProvider`, `GeminiProvider`, `LiteLLMProvider`) with `async def process()` and `async with` context manager support
- **Helper modules**: stateless functions in `processing_utils.py`, `provider_utils.py`, `pricing.py`

### Database Layer (`database/crud/`)
- All CRUD functions are `async def` using `async with connect() as db:`
- Raw SQL via `aiosqlite` — no ORM
- Row mapping: `db.row_factory = aiosqlite.Row` + `return dict(row)`
- SQL-injection safe: parameterized queries with `?` placeholders
- Column validation: `validate_update_columns()` prevent arbitrary column updates
- Re-exported through `database/crud/__init__.py` with explicit `__all__` list

### Background Job Queue
- **Enqueue**: `enqueue_processing_task(job_id, file_path, payload, task_type)` → inserts into `job_queue` table
- **Polling worker**: `_worker_loop` → `crud.claim_next_queued_job()` → `_run_job()` → dispatches to `run_processing_job()` or `run_text_processing_job()`
- Worker lifecycle: `start_job_worker()`/`stop_job_worker()` called in FastAPI `lifespan`
- **Test safety**: `_should_start_worker()` returns `False` when `PYTEST_CURRENT_TEST` env var is set

### Error Handling
- Services return `{"success": False, "error": "..."}` dicts from `process_file()`
- Top-level `_register_result()` translates success/fail into DB status update
- `_handle_processing_error()` wraps exceptions into structured DB updates
- `pytest.raises(HTTPException)` for testing HTTP error paths

## TypeScript Patterns

### React Components
- `export default function ComponentName({ prop1, prop2 }: ComponentProps)` — default export, PascalCase
- Props interface in same file, named `ComponentNameProps`
- State: `useState` only (no external state management — no Redux, no Zustand)
- Effects: `useEffect` for side effects, `useRef` for DOM references
- Styling: Tailwind CSS utility classes exclusively (no `.css` files in `src/`)
- Path alias: `@/` maps to `src/`, used for imports from `pages/`, `components/`, `lib/api`
- No separate CSS modules or styled-components

### API Client (`src/lib/api/`)
- **Domain files**: `jobs.ts`, `schemas.ts`, `settings.ts`, `benchmarks.ts`, `auth.ts`
- All functions are `async` returning typed promises
- Pattern: `fetch(API_BASE + path, { method, headers, body })` → check `ok` → `response.json()` → typed result
- Auth headers: `getAuthHeaders()` (JWT only), `getAccessHeaders()` (JWT + guest token)
- Error handling: `parseApiError()` fallback, specific `429` rate-limit handling
- Guest tokens saved via `setGuestToken(data.guest_token)` after upload/process
- Re-exported barrel pattern in `index.ts`

### Type Definitions
- All shared types in `src/lib/api/types.ts`, mirroring backend Pydantic models
- `interface` for object shapes, `type` for union/enum-like (`ExtractionMethod`)
- Fields use `snake_case` to match JSON API responses directly
- `Record<string, unknown>` for dynamic objects (schema_definition, result)
- Optional fields: `field?: type` for nullable/optional properties
- Literal unions for constrained strings: `status: 'pending' | 'processing' | 'success' | 'error'`

### WebSocket Client (`src/lib/websocket.ts`)
- Class-based: `JobStatusWebSocket` wraps `WebSocket` lifecycle
- Public API: `connect(jobId)`, `disconnect()`, `onStatusChange(cb)`, `onError(cb)`, `isConnected()`
- Reconnect with exponential backoff (2s → 30s max, 5 attempts max)
- Auth via short-lived ticket (`POST /api/ws/ticket`) to avoid JWT in URL
- Auto-disconnects on terminal status (`success`/`error`)

## Testing

### Python (pytest)

| Aspect | Convention |
|--------|-----------|
| Runner | `cd backend && uv run pytest tests/` |
| Config | `pyproject.toml`: `testpaths = ["tests"]`, `python_files = ["test_*.py"]`, `asyncio_mode = "auto"` |
| Async | `@pytest.mark.asyncio` on test functions |
| Fixtures | `conftest.py` at `tests/`: `client` (TestClient), `auth_header` (admin token), `test_user_auth_header` |
| Integration fixtures | `tests/integration/conftest.py`: `_disable_rate_limiting` (autouse), `temp_db_env` (isolated SQLite) |
| Markers | `unit`, `integration`, `e2e`, `slow`, `network`, `db` (registered in pyproject.toml:86-94) |
| Auto-marker | `pytest_collection_modifyitems` adds `integration`/`slow` based on file path |
| DB isolation | Integration tests use `tmp_path` + `monkeypatch` to override `paths.get_db_path` |
| Mocking | `pytest-mock` available, `monkeypatch` (stdlib) used in conftest |
| Naming | `test_<what>_<condition>_<expected>()` — descriptive, one assertion path per test |
| Slow exclusion | `uv run pytest -m "not slow"` for fast unit-only runs |
| Test discovery | `tests/unit/test_*.py`, `tests/integration/test_*.py`, `tests/e2e/test_*.py` |

### TypeScript (Vitest + Playwright)

| Aspect | Convention |
|--------|-----------|
| Unit runner | `npm run test:unit` → `vitest run` from `frontend/` |
| Vitest config | `vitest.config.ts`: `environment: 'jsdom'`, `include: ['src/**/*.test.ts']` |
| E2E runner | `npm run test:e2e:smoke` → `playwright test e2e/smoke.spec.ts` |
| E2E config | `playwright.config.ts`: auto-starts uvicorn via `webServer`, custom env vars |
| E2E env vars | `E2E_BACKEND_PORT`, `E2E_BASE_URL`, `E2E_DATABASE_URL`, `E2E_JWT_SECRET` |
| E2E global setup | `playwright.global-setup.ts` runs before all tests |
| Naming plan | `src/**/*.test.ts` for vitest, `e2e/**/*.spec.ts` for Playwright |
| Combined run | `npm test` runs unit + e2e smoke sequentially |

## Linting & Formatting

| Stack | Tool | Configuration |
|-------|------|---------------|
| Python | **ruff** | `ruff>=0.15.2` in dev-dependencies (backend/pyproject.toml:73). No separate ruff.toml. |
| TypeScript | **ESLint v8** | `eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0`. Plugins: `@typescript-eslint`, `react-hooks`, `react-refresh` |
| TypeScript | **Prettier v3** | `prettier --write` via lint-staged on `*.{ts,tsx,js,jsx}` |
| TypeScript | **Husky** pre-commit | Runs `lint-staged` before commit |
| TypeScript | **lint-staged** | ESLint fix + Prettier write on `.ts/.tsx/.js/.jsx`, Prettier write on `.css/.scss/.md/.json/.yaml` |
| TypeScript | **TypeScript strict** | `tsconfig.json`: `strict: true`, `noUnusedLocals: true`, `noUnusedParameters: true` |
| Build check | `npm run check` | Runs `npm run lint && npm run build` (lint + tsc + vite build) |

## Build/Dev Commands

```
# Backend
uv sync                                         → Install Python deps
cd backend && uv run uvicorn main:app --reload --port 8001  → Start FastAPI dev server
cd backend && uv run -m backend.cli                          → Run CLI tools
cd backend && uv run pytest tests/                           → Run all backend tests
cd backend && uv run pytest tests/ -m "not slow"             → Run unit tests only (skip integration/e2e)

# Frontend
npm install                                     → Install JS deps
npm run dev                                     → Start Vite dev server (port 5173)
npm run check                                   → ESLint + tsc + vite build
npm run build                                   → tsc + vite build (to frontend/dist/)
npm test                                        → vitest unit + Playwright e2e smoke
npm run test:unit                               → vitest run (src/**/*.test.ts)
npm run test:e2e:smoke                          → playwright test e2e/smoke.spec.ts

# Docker
dotenvx run -- docker-compose up                → Full stack via Docker (port 8001 → 8000)
docker-compose up --build                       → Rebuild + start Docker
