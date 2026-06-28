# Audit Remediation Handoff (2026-06-28)

## What changed

- Removed audio from the public upload surface so the app no longer advertises a flow that hard-fails at processing time.
- Added real client-side route gating for `/benchmarks`; non-admin users are redirected instead of landing on a page that immediately triggers 403s.
- Updated repo guidance so backend verification uses the actual package root: `cd backend && uv run pytest tests/`.
- Replaced the stale skipped transcription e2e check with deterministic coverage for the current provider-backed transcription contract.

## Files changed

- `backend/routers/upload.py`
- `backend/tests/integration/test_guest_access.py`
- `backend/tests/e2e/test_e2e_phase1.py`
- `backend/extraction_methods.py`
- `frontend/src/App.tsx`
- `frontend/src/components/FileUpload.tsx`
- `frontend/src/pages/BaseExtractionPage.tsx`
- `frontend/src/pages/LandingPage.tsx`
- `frontend/src/lib/methods.ts`
- `.planning/OVERVIEW.md`
- `.planning/STATE.md`
- `.planning/STYLE.md`
- `docs/reference/api.md`
- `docs/features/phase1.md`
- `docs/guides/user-guide.md`

## Verification

- Backend: `cd backend && uv run pytest tests/`
- Frontend: `cd frontend && npm run check`
- Frontend: `cd frontend && npm test`

## Current product contract

- Supported uploads: PDF, image, DOCX, PPTX, TXT, MD, HTML
- `transcription` remains supported for document-style files
- Audio upload/transcription is intentionally not exposed until a real provider pipeline is implemented end-to-end

## Remaining follow-up worth considering

1. Update older historical docs and archived notes that still mention audio support if they are still referenced by teammates.
2. Add a lightweight frontend route test around non-admin `/benchmarks` navigation if the repo adopts React component test utilities.
3. Decide whether audio support should come back as a dedicated provider-backed feature or stay out of scope.
