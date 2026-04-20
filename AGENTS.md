## 1. Workflow
- **Analyze First:** Read relevant files before proposing solutions. Never hallucinate.
- **Approve Changes:** Present a plan for approval before modifying code.
- **Minimal Scope:** Change as little code as possible. No new abstractions.

## 2. Output Style
- High-level summaries only.
- No speculation about code you haven't read.

## 3. Technical Stack
- **Python:**
  - Package manager: `uv`.
  - Execution: Always `uv run <command>`. Never `python`.
  - Installing package: `uv add`
  - Sync: `uv sync`.
- **Frontend:**
  - Verify: Run `npm run check` and `npm test` after changes.
- **Files:** Markdown files must follow `YYYYMMDD-filename.md` format.
- **Docker:** `dotenvx run -- docker-compose up` for runs requiring api keys etc.

## 4. Project Structure
```
ocr_platform_testdrive/
├── backend/                    # FastAPI backend
│   ├── routers/               # API endpoints (upload, processing, jobs, schemas, etc.)
│   ├── services/              # Business logic (VLM providers, docling, hybrid processing)
│   ├── database/              # SQLite CRUD, migrations, pool
│   ├── models/                # Pydantic models
│   ├── benchmarks/            # Benchmarking framework
│   ├── tests/                 # pytest tests
│   └── main.py                # FastAPI app entry point
├── frontend/                   # React + TypeScript frontend
│   ├── src/
│   │   ├── pages/            # Page components (Landing, Processing, History, Benchmarks)
│   │   ├── components/       # Reusable components
│   │   └── lib/api.ts        # API client (types, fetch wrappers)
│   └── e2e/                  # Playwright E2E tests
├── data/                       # Local data storage (uploads, database)
├── docs/                       # Project documentation
│   ├── features/             # Feature documentation
│   ├── benchmarks/           # Benchmark results
│   ├── handoffs/             # Phase handoffs
│   └── reference/            # Technical reference
└── docker-compose.yml         # Container orchestration
```

## 5. Key Conventions
- **Database:** SQLite at `data/database.sqlite`. Migrations in `backend/database/migrations.py`
- **Auth:** JWT tokens stored in localStorage. Guest tokens for unauthenticated uploads.
- **Processing Methods:** `text`, `vision`, `hybrid`, `docling-parse`, `docling-extract`, `transcription`
- **API Base:** `/api` (relative path for proxy compatibility)
- **VLM Providers:** OpenRouter, Gemini. Configured via env vars.
- **Rate Limiting:** 10 req/min general, 5 uploads/min, 3 jobs/min per user

## 6. Important Files
- `backend/main.py` - FastAPI app, CORS, middleware, router registration
- `backend/config.py` - Settings, env var parsing (pydantic-settings)
- `backend/database/crud.py` - Database operations
- `backend/services/processing.py` - Core processing logic
- `frontend/src/lib/api.ts` - Frontend API client (DO NOT duplicate types)
- `docker-compose.yml` - Port 8001:8000 (avoids local dev conflict)

## 7. Testing
- Backend: `uv run pytest backend/tests/`
- Frontend: `npm test` (unit), `npm run test:e2e` (Playwright)
- Quality: Check `backend/tests/conftest.py` for fixtures