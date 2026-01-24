# OCR Platform - Claude Context

This file provides context for Claude Code to work effectively with this project.

## Project Overview

A modern OCR platform using Vision Language Models (VLMs) to extract structured data from documents. Supports multiple VLM providers (Nebius, OpenRouter, Google Gemini) with intelligent auto-routing between text extraction and vision processing pipelines.

**Key Features:**
- Multi-provider VLM support
- Intelligent document routing (auto-detects optimal pipeline)
- Schema-based structured extraction
- Real-time job processing
- React + TypeScript frontend

## Tech Stack

**Backend:** FastAPI + Python 3.11 + SQLite + Pydantic v2
**Frontend:** React 18 + TypeScript + Vite + TailwindCSS
**Infrastructure:** Docker + Docker Compose

## Documentation Structure

```
docs/
├── guides/              # User-facing documentation
│   ├── setup.md        # Environment setup & installation
│   ├── user-guide.md   # Platform usage guide
│   ├── schema-guide.md # JSON schema creation
│   └── troubleshooting.md
│
├── development/         # Development workflows
│   ├── testing-guide.md    # Testing procedures
│   ├── backend-testing.md  # Backend-specific testing
│   └── auto-routing-test-report.md # Test results
│
├── implementation/      # Technical implementation details
│   ├── implementation-summary.md # Project summary
│   ├── mvp-implementation.md    # MVP implementation
│   └── auto-routing.md          # Auto-routing feature
│
├── plans/              # Design documents
├── progress/           # Project tracking
└── reports/            # Historical records
    ├── changelog.md
    └── investigations/   # Issue investigations & fixes
```

## Quick Start

### Development Workflow

1. **Setup:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   uv sync  # Backend dependencies
   cd frontend && npm install  # Frontend dependencies
   ```

2. **Run Backend:**
   ```bash
   cd backend
   uv run uvicorn main:app --reload --port 8000
   ```

3. **Run Frontend:**
   ```bash
   cd frontend
   npm run dev  # Runs on http://localhost:5173
   ```

### Docker (Alternative)

```bash
docker compose up --build
```

## Key Files & Locations

**Backend:**
- `backend/main.py` - FastAPI application entry point
- `backend/routers/` - API endpoints (processing, jobs, schemas)
- `backend/services/processing.py` - Main processing pipeline
- `backend/services/document_classifier.py` - Document routing logic
- `backend/database/crud.py` - Database operations

**Frontend:**
- `frontend/src/App.tsx` - Main app with navigation
- `frontend/src/pages/` - Page components (ProcessingPage, HistoryPage)
- `frontend/src/components/` - Reusable UI components
- `frontend/src/lib/api.ts` - API client

**Configuration:**
- `.env` - Environment variables (API keys, settings)
- `backend/pyproject.toml` - Python dependencies
- `frontend/package.json` - Node dependencies

## Development Guidelines

### Adding New Features

1. **Backend Changes:**
   - Update `backend/routers/` for new endpoints
   - Add business logic to `backend/services/`
   - Update database schema in `backend/database/`
   - Add Pydantic models to `backend/models/`

2. **Frontend Changes:**
   - Create components in `frontend/src/components/`
   - Add pages in `frontend/src/pages/`
   - Update API client in `frontend/src/lib/api.ts`
   - Update navigation in `frontend/src/App.tsx`

3. **Documentation:**
   - Update `docs/reports/changelog.md` with changes
   - Add new guides to appropriate `docs/` subdirectory
   - Update this file (claude.md) if architecture changes

### Testing

```bash
# Backend tests
cd backend
pytest tests/

# Frontend tests (if available)
cd frontend
npm test
```

### Common Tasks

**Reset Database:**
```bash
rm backend/data/ocr.db
cd backend && python -m database.migrations
```

**Check API Status:**
- Health check: http://localhost:8000/health
- API docs: http://localhost:8000/docs

**View Logs:**
```bash
# Docker logs
docker compose logs -f

# Backend logs (when running locally)
# Check terminal where uvicorn is running
```

## Environment Variables

Required in `.env`:
- `NEBIUS_API_KEY` - Nebius API key
- `OPENROUTER_API_KEY` - OpenRouter API key
- `GEMINI_API_KEY` - Google Gemini API key

(At least one provider key is required)

## Important Notes

- The platform uses **auto-routing** to automatically choose between text extraction and vision processing
- Document classification happens in `backend/services/document_classifier.py`
- Text extraction uses pdfplumber, vision uses VLMs
- All processing is asynchronous with job tracking
- Frontend polls for job status updates

## Troubleshooting

**Port already in use:**
```bash
lsof -i :8000  # Find process
kill -9 <PID>  # Kill it
```

**Database errors:**
- Reinitialize: `rm -rf backend/data/ && cd backend && python -m database.migrations`

**API key issues:**
- Verify `.env` file exists
- Check keys are correct (no extra quotes/spaces)
- Ensure at least one provider is configured

## Getting Help

1. Check relevant documentation in `docs/`
2. Review `docs/guides/troubleshooting.md`
3. Check API docs at http://localhost:8000/docs
4. Review recent changes in `docs/reports/changelog.md`
