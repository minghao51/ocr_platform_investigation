# OCR Platform

OCR Platform is a FastAPI + React application for extracting structured data from PDFs and images with vision-language models. It supports authenticated uploads, schema-based extraction, job history, and real-time status updates over WebSocket.

## What It Does

- Upload PDF and image documents
- Run OCR/data extraction with Nebius, OpenRouter, or Gemini
- Use built-in templates or provide your own JSON Schema
- Auto-route PDFs between text and vision pipelines
- Track jobs and inspect prior results

## Stack

- Backend: FastAPI, SQLite, Pydantic, jsonschema
- Frontend: React, TypeScript, Vite
- Runtime: Docker Compose or local backend/frontend processes

## Quick Start

### Docker

```bash
cp .env.example .env
docker compose up --build
```

Open `http://localhost:8000`.

This Compose file is now tuned for demo/staging use: it runs the built app in one container and persists only `./data`.

### Local Development

Terminal 1:

```bash
cp .env.example .env
cd backend
uv run uvicorn main:app --reload --port 8000
```

Terminal 2:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

## Required Configuration

At least one provider key is required:

- `NEBIUS_API_KEY`
- `OPENROUTER_API_KEY`
- `GEMINI_API_KEY`

You also need:

- `JWT_SECRET_KEY`
- `CORS_ORIGINS` or `CORS_ORIGINS_STR`

See [docs/guides/setup.md](/Users/minghao/Desktop/personal/ocr_platform_testdrive/docs/guides/setup.md) for the full setup flow.

## Core Workflow

1. Create a user with the CLI or log in with an existing account.
2. Upload a document.
3. Pick a provider/model.
4. Choose a saved schema, a built-in template, or paste a custom schema.
5. Start processing and wait for live status updates.
6. Review the result in the Extract or History screens.

## CLI

Administrative commands live in [backend/cli.py](/Users/minghao/Desktop/personal/ocr_platform_testdrive/backend/cli.py).

Examples:

```bash
uv run python -m backend.cli create-admin admin strong-password
uv run python -m backend.cli create-demo guest1 guest-password
uv run python -m backend.cli list-users
```

## Documentation

- Setup: [docs/guides/setup.md](/Users/minghao/Desktop/personal/ocr_platform_testdrive/docs/guides/setup.md)
- Deployment: [docs/guides/deployment.md](/Users/minghao/Desktop/personal/ocr_platform_testdrive/docs/guides/deployment.md)
- Using the app: [docs/guides/user-guide.md](/Users/minghao/Desktop/personal/ocr_platform_testdrive/docs/guides/user-guide.md)
- Troubleshooting: [docs/guides/troubleshooting.md](/Users/minghao/Desktop/personal/ocr_platform_testdrive/docs/guides/troubleshooting.md)
- API reference: [docs/reference/api.md](/Users/minghao/Desktop/personal/ocr_platform_testdrive/docs/reference/api.md)
- Schema reference: [docs/reference/schema-guide.md](/Users/minghao/Desktop/personal/ocr_platform_testdrive/docs/reference/schema-guide.md)
- Testing: [docs/reference/testing.md](/Users/minghao/Desktop/personal/ocr_platform_testdrive/docs/reference/testing.md)
- Project structure: [docs/reference/project-structure.md](/Users/minghao/Desktop/personal/ocr_platform_testdrive/docs/reference/project-structure.md)

Historical plans and implementation notes were moved under [docs/archive](/Users/minghao/Desktop/personal/ocr_platform_testdrive/docs/archive).
