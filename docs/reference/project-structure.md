# Project Structure

## Top Level

```text
ocr_platform_testdrive/
├── backend/
├── frontend/
├── docs/
├── data/
├── Dockerfile
├── docker-compose.yml
├── README.md
└── .env.example
```

## Backend

- `main.py`: FastAPI app assembly, router registration, SPA fallback
- `routers/`: HTTP and WebSocket endpoints
- `services/`: processing, provider integrations, schema utilities
- `database/`: schema, migrations, CRUD, connection management
- `models/`: request/response models
- `tests/`: backend tests
- `cli.py`: admin and user-management commands

## Frontend

- `src/App.tsx`: routing and top-level navigation
- `src/pages/`: landing, extraction, history, methodology
- `src/components/`: upload, schema editor, model selector, results UI
- `src/lib/api.ts`: frontend API client
- `src/lib/websocket.ts`: live job update client

## Docs

- `guides/`: practical setup and usage docs
- `reference/`: API, schema, testing, and structure docs
- `archive/`: old plans, reports, and implementation notes retained for context only

## Notable Runtime Paths

- uploads: `data/uploads`
- local SQLite default: `data/ocr_platform.db`
