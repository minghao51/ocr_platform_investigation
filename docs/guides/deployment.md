# Deployment Guide

## Recommended Demo Host

For a fast hosted demo, use Render with the provided [render.yaml](/Users/minghao/Desktop/personal/ocr_platform_testdrive/render.yaml).

Why this is the easiest first host:

- the repo already includes a multi-stage [Dockerfile](/Users/minghao/Desktop/personal/ocr_platform_testdrive/Dockerfile)
- the backend can serve the built frontend from the same container
- a persistent disk keeps the SQLite database and uploaded files between deploys

## Render Setup

1. Push the repo to GitHub/GitLab.
2. In Render, create a new Blueprint service from the repo.
3. Provide at least one provider API key when prompted.
4. Keep the persistent disk enabled at `/app/data`.
5. After deploy, open `/health` and `/docs` to confirm the service is live.

## Accounts for a Demo

Create at least two kinds of accounts:

- master account: an admin account for you or the presenter; admin accounts bypass request caps
- demo account: limited accounts for guests; these use the configured daily demo limit

From a shell in the deployed service:

```bash
cd /app
python -m cli create-admin demo-master strong-password
python -m cli create-demo guest1 guest-password
python -m cli list-users
```

## Demo-Safe Defaults

- API and HTML responses are sent with `Cache-Control: no-store` so demos do not get stale pages or API payloads
- hashed frontend assets can still cache safely
- uploads and OCR endpoints use per-minute rate limits
- limited demo accounts also use a daily OCR cap

## Notes

- SQLite is fine for a short-lived demo, but move to PostgreSQL before broader sharing or concurrent team usage.
- Uploaded files live under `/app/data/uploads`, so do not remove the disk between demo runs unless you want a clean reset.
