## 1. Workflow
- **Analyze First:** Read relevant files before proposing solutions. Never hallucinate.
- **Approve Changes:** Present a plan for approval before modifying code.
- **Minimal Scope:** Change as little code as possible. No new abstractions.
- **Check Skills:** Before any task, check if a relevant skill exists and follow it.
- **Verify:** After changes, run lint and type-check if applicable. Ask user for the command if unsure.
- **No Commits:** Never commit unless explicitly asked.

## 2. Output Style
- Concise. Bulletpoints over paragraphs.
- Reference file paths with line numbers when relevant.
- No preamble or postamble. Answer directly.

## 3. File Operations
- **Read before edit** — Always read a file before editing it.
- **Prefer Edit tool** over Write for surgical changes.
- **Prefer editing existing files** over creating new ones.

## 4. Technical Stack
- **Python:**
  - Package manager: `uv`.
  - Execution: Always `uv run <command>`. Never `python`.
  - Installing package: `uv add`
  - Sync: `uv sync`.
- **Frontend:**
  - Verify: Run `npm run check` and `npm test` after changes.
- **Files:** Markdown files must follow `YYYYMMDD-filename.md` format.
- **Docker:** `dotenvx run -- docker-compose up` for runs requiring api keys etc.

## 5. Project Structure
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

## 6. Key Conventions
- **Database:** SQLite at `data/database.sqlite`. Migrations in `backend/database/migrations.py`
- **Auth:** JWT tokens stored in localStorage. Guest tokens for unauthenticated uploads.
- **Processing Methods:** `text`, `vision`, `hybrid`, `docling-parse`, `docling-extract`, `transcription`
- **API Base:** `/api` (relative path for proxy compatibility)
- **VLM Providers:** OpenRouter, Gemini. Configured via env vars.
- **Rate Limiting:** 10 req/min general, 5 uploads/min, 3 jobs/min per user

## 7. Important Files
- `backend/main.py` - FastAPI app, CORS, middleware, router registration
- `backend/config.py` - Settings, env var parsing (pydantic-settings)
- `backend/database/crud.py` - Database operations
- `backend/services/processing.py` - Core processing logic
- `frontend/src/lib/api.ts` - Frontend API client (DO NOT duplicate types)
- `docker-compose.yml` - Port 8001:8000 (avoids local dev conflict)

## 8. Testing
- Backend: `uv run pytest backend/tests/`
- Frontend: `npm test` (unit), `npm run test:e2e` (Playwright)
- Quality: Check `backend/tests/conftest.py` for fixtures

## 9. Project Context References

After running codemap analysis, add these references:
- Project overview (architecture, stack, integrations): `.planning/OVERVIEW.md`
- Code style & conventions: `.planning/STYLE.md`
- Current state (bugs, risks, maintenance): `.planning/STATE.md`