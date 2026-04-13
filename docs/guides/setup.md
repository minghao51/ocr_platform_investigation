# Setup Guide

This project can run either through Docker Compose or as separate backend/frontend processes.

## Prerequisites

- Python 3.11+
- Node 18+
- `uv` for the backend workflow
- Docker and Docker Compose if you want the containerized path
- At least one VLM provider API key

## 1. Configure Environment

Create a local environment file:

```bash
cp .env.example .env
```

Important variables:

- `NEBIUS_API_KEY`, `OPENROUTER_API_KEY`, or `GEMINI_API_KEY`
- `JWT_SECRET_KEY`
- `CORS_ORIGINS` or `CORS_ORIGINS_STR`
- `DATABASE_URL` if you want to override the default SQLite path
- `RATE_LIMIT_PER_MINUTE` for per-minute OCR action caps
- `DEMO_DAILY_REQUEST_LIMIT` for limited demo accounts

Generate a JWT secret with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## 2. Create an Admin User

The app requires login for uploads and history access.

```bash
uv run python -m backend.cli create-admin admin your-password
```

Optional:

```bash
uv run python -m backend.cli create-demo testuser testpass
uv run python -m backend.cli list-users
```

## 3. Run with Docker

From the repo root:

```bash
docker compose up --build
```

Open:

- App: `http://localhost:8000`
- Health check: `http://localhost:8000/health`
- OpenAPI docs: `http://localhost:8000/docs`

## 4. Run Locally

Backend:

```bash
cd backend
uv run uvicorn main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Open:

- Frontend dev server: `http://localhost:5173`
- Backend API: `http://localhost:8000`

## 5. Verify the App

1. Open the app.
2. Log in with the user you created.
3. Upload a PDF or image.
4. Start an extraction job.
5. Confirm the result appears in History.

## Notes

- The backend serves the built frontend from `/` when `frontend/dist` exists.
- CORS defaults are intended for local development.
- Uploaded files are stored under `data/uploads`.
- Admin users bypass rate and demo daily limits.
- Demo users are limited by `DEMO_DAILY_REQUEST_LIMIT` per day.

## Next Reading

- [docs/guides/user-guide.md](/Users/minghao/Desktop/personal/ocr_platform_testdrive/docs/guides/user-guide.md)
- [docs/guides/deployment.md](/Users/minghao/Desktop/personal/ocr_platform_testdrive/docs/guides/deployment.md)
- [docs/reference/api.md](/Users/minghao/Desktop/personal/ocr_platform_testdrive/docs/reference/api.md)
- [docs/guides/troubleshooting.md](/Users/minghao/Desktop/personal/ocr_platform_testdrive/docs/guides/troubleshooting.md)
