# Testing Reference

## Backend Tests

Run from the `backend` directory:

```bash
uv run pytest
```

Run a specific file:

```bash
uv run pytest tests/test_integration.py
```

Current tracked backend tests are under [backend/tests](/Users/minghao/Desktop/personal/ocr_platform_testdrive/backend/tests).

## Frontend

There is no dedicated frontend test suite documented in the current repo state. Validation should be done through:

- local manual testing
- the app UI
- browser console/network inspection when needed

## Manual Smoke Test

1. Start backend and frontend.
2. Log in with an admin account and verify upload/process actions are allowed without limit errors.
3. Log in with a demo-limited account and verify upload/process actions work until the configured cap is reached.
4. Upload a document.
5. Submit a job.
6. Confirm live status updates and final result.
7. Confirm the job appears in History.

## Useful Endpoints During Verification

- `GET /health`
- `GET /docs`
- `GET /api/providers/`

## Admin Utilities

Use [backend/cli.py](/Users/minghao/Desktop/personal/ocr_platform_testdrive/backend/cli.py) to create or inspect users before manual testing.
